"""Gmail API helper for sending newsletter emails."""
from __future__ import annotations

import base64
import logging
import os
import shutil
from dataclasses import dataclass
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from time import sleep
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pipeline.shared.config import AppConfig

log = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


@dataclass(frozen=True)
class _ResolvedOAuthPaths:
    token: Path
    client_secret: Path
    configured_token: Path
    configured_client_secret: Path


@dataclass(frozen=True)
class BulkSendResult:
    results: list[dict]
    failures: list[dict[str, str]]

    @property
    def message_ids(self) -> list[str]:
        return [str(r.get("id") or "") for r in self.results if r.get("id")]

    @property
    def successful_recipients(self) -> list[str]:
        return [str(r.get("recipient") or "") for r in self.results if r.get("recipient")]

    @property
    def failed_recipients(self) -> list[str]:
        return [f["recipient"] for f in self.failures if f.get("recipient")]

    @property
    def success_count(self) -> int:
        return len(self.results)

    @property
    def failed_count(self) -> int:
        return len(self.failures)

    @property
    def is_partial_success(self) -> bool:
        return bool(self.results and self.failures)

    def failure_summary(self, *, limit: int | None = None) -> str:
        failures = self.failures[:limit] if limit is not None else self.failures
        return "\n".join(f"{f.get('recipient', '')}: {f.get('error', '')}" for f in failures)


def _gmail_cache_dir() -> Path:
    return Path(os.getenv("GMAIL_TOKEN_CACHE_DIR", str(Path.home() / ".cache" / "gmail")))


def _uses_explicit_cache() -> bool:
    return bool(os.getenv("GMAIL_TOKEN_CACHE_DIR", "").strip())


def _path_is_readable(path: Path) -> bool:
    try:
        return path.is_file() and os.access(path, os.R_OK)
    except OSError:
        return False


def _path_is_writable(path: Path) -> bool:
    try:
        return path.is_file() and os.access(path, os.W_OK)
    except OSError:
        return False


def _maybe_sync_to_cache(source: Path, dest: Path) -> None:
    """Copy *source* into cache when cache is missing or source is newer."""
    if not _path_is_readable(source):
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.is_file():
        shutil.copy2(source, dest)
        return
    try:
        if source.stat().st_mtime > dest.stat().st_mtime:
            shutil.copy2(source, dest)
    except OSError as exc:
        log.warning("Could not sync OAuth file %s -> %s: %s", source, dest, exc)


def _copy_oauth_file(source: Path, dest: Path) -> Path:
    """Copy OAuth file into cache when the mount is not readable by the app user."""
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        return dest
    except OSError as exc:
        if dest.is_file():
            log.warning("Using cached OAuth file %s (could not read %s: %s)", dest, source, exc)
            return dest
        raise PermissionError(
            f"Cannot access OAuth file at {source}. "
            f"Ensure the credentials volume is readable inside the container (UID 1000) "
            f"or place token.json in {dest.parent}."
        ) from exc


def _resolve_oauth_paths(token_path: Path, client_secret_path: Path) -> _ResolvedOAuthPaths:
    """
    Pick OAuth files the app user can read and write.

    When ``GMAIL_TOKEN_CACHE_DIR`` is set (Docker), all reads/writes use the cache volume.
    Locally, configured paths are used when writable; otherwise a copy under ``~/.cache/gmail``.
    """
    cache_dir = _gmail_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_token = cache_dir / "token.json"
    cache_secret = cache_dir / "credentials.json"

    if _uses_explicit_cache():
        _maybe_sync_to_cache(client_secret_path, cache_secret)
        _maybe_sync_to_cache(token_path, cache_token)
        if not cache_secret.is_file():
            raise FileNotFoundError(
                f"Gmail client secret not found at {client_secret_path} "
                f"(cache {cache_secret} is also missing). "
                "Set GMAIL_OAUTH_CLIENT_SECRET_FILE in .env."
            )
        if not cache_token.is_file():
            raise FileNotFoundError(
                f"Gmail token file not found at {token_path} "
                f"(cache {cache_token} is also missing). "
                "Run scripts/generate_gmail_token.py once, then restart Docker."
            )
        return _ResolvedOAuthPaths(
            token=cache_token,
            client_secret=cache_secret,
            configured_token=token_path,
            configured_client_secret=client_secret_path,
        )

    if not client_secret_path.is_file():
        if not cache_secret.is_file():
            raise FileNotFoundError(
                f"Gmail client secret not found at {client_secret_path}. "
                "Set GMAIL_OAUTH_CLIENT_SECRET_FILE in .env."
            )
        resolved_secret = cache_secret
    elif _path_is_writable(client_secret_path):
        resolved_secret = client_secret_path
    else:
        resolved_secret = _copy_oauth_file(client_secret_path, cache_secret)

    if not token_path.is_file():
        if not cache_token.is_file():
            raise FileNotFoundError(
                f"Gmail token file not found at {token_path}. "
                "Run scripts/generate_gmail_token.py to generate the token."
            )
        resolved_token = cache_token
    elif _path_is_writable(token_path):
        resolved_token = token_path
    else:
        resolved_token = _copy_oauth_file(token_path, cache_token)

    return _ResolvedOAuthPaths(
        token=resolved_token,
        client_secret=resolved_secret,
        configured_token=token_path,
        configured_client_secret=client_secret_path,
    )


def oauth_files_available(token_path: Path, client_secret_path: Path) -> bool:
    """Return True when configured or cached OAuth files exist and are readable."""
    if not token_path or not client_secret_path:
        return False
    cache_dir = _gmail_cache_dir()
    cache_token = cache_dir / "token.json"
    cache_secret = cache_dir / "credentials.json"
    token_ok = _path_is_readable(token_path) or cache_token.is_file()
    secret_ok = _path_is_readable(client_secret_path) or cache_secret.is_file()
    if _uses_explicit_cache():
        return cache_token.is_file() and cache_secret.is_file()
    return token_ok and secret_ok


def gmail_is_configured(cfg: AppConfig) -> bool:
    """True when sender email and OAuth files are present (including Docker cache)."""
    if not (cfg.gmail_sender_email or "").strip():
        return False
    return oauth_files_available(cfg.gmail_oauth_token_json, cfg.gmail_oauth_client_secret_file)


def _persist_refreshed_token(creds_json: str, paths: _ResolvedOAuthPaths) -> None:
    paths.token.write_text(creds_json, encoding="utf-8")
    log.info("Refreshed token saved to %s", paths.token)
    configured = paths.configured_token
    if configured != paths.token and _path_is_writable(configured):
        configured.write_text(creds_json, encoding="utf-8")
        log.info("Refreshed token mirrored to %s", configured)


def _get_credentials(token_path: Path, client_secret_path: Path):
    """Load OAuth2 credentials, refreshing the access token if expired."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    paths = _resolve_oauth_paths(token_path, client_secret_path)

    creds = Credentials.from_authorized_user_file(str(paths.token), SCOPES)

    if creds.expired and creds.refresh_token:
        log.info("Gmail access token expired — refreshing.")
        creds.refresh(Request())
        _persist_refreshed_token(creds.to_json(), paths)

    if not creds or not creds.valid:
        raise RuntimeError(
            "Gmail credentials are invalid. "
            f"Token: {paths.token} | Client secret: {paths.client_secret}"
        )

    return creds


def send_html_email(
    *,
    html: str,
    recipients: list[str],
    subject: str,
    sender: str,
    token_path: Path,
    client_secret_path: Path,
    attachments: list[tuple[str, bytes, str]] | None = None,
) -> dict:
    """Send an HTML email via the Gmail API (single message).

    If multiple recipients are provided, they are included together in a single email.
    Prefer :func:`send_html_emails_individually` only when you explicitly want one
    email per recipient.

    *attachments* is an optional list of ``(filename, raw_bytes, mime_type)`` tuples
    (for example ``(\"report.csv\", data, \"text/csv\")``).
    """
    from googleapiclient.discovery import build

    if not recipients:
        raise ValueError("At least one recipient is required.")

    creds = _get_credentials(token_path, client_secret_path)
    service = build("gmail", "v1", credentials=creds)

    to_header = ", ".join([r for r in recipients if (r or "").strip()])
    att_list = [a for a in (attachments or []) if a and a[0] and a[1] is not None]

    if att_list:
        msg = MIMEMultipart("mixed")
        msg["From"] = sender
        msg["To"] = to_header
        msg["Subject"] = subject
        alt = MIMEMultipart("alternative")
        alt.attach(MIMEText(html, "html", "utf-8"))
        msg.attach(alt)
        for filename, data, mime in att_list:
            maintype, _, subtype = (mime or "application/octet-stream").partition("/")
            if not subtype:
                maintype, subtype = "application", "octet-stream"
            part = MIMEBase(maintype, subtype)
            part.set_payload(data)
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", "attachment", filename=filename)
            msg.attach(part)
    else:
        msg = MIMEMultipart("alternative")
        msg["From"] = sender
        msg["To"] = to_header
        msg["Subject"] = subject
        msg.attach(MIMEText(html, "html", "utf-8"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    result: dict = (
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
    )

    log.info("Email sent | recipients=%s | message_id=%s", ",".join(recipients), result.get("id"))
    return result


def send_html_emails_individually(
    *,
    html: str,
    recipients: list[str],
    subject: str,
    sender: str,
    token_path: Path,
    client_secret_path: Path,
    max_retries: int = 1,
    throttle_seconds: float = 0.5,
) -> BulkSendResult:
    """Send one email per recipient, each with a single "To" address.

    Returns successes and final failures. Each failed recipient is retried
    ``max_retries`` times before being reported as a permanent failure.
    """
    from googleapiclient.discovery import build

    if not recipients:
        raise ValueError("At least one recipient is required.")

    creds = _get_credentials(token_path, client_secret_path)
    service = build("gmail", "v1", credentials=creds)

    results: list[dict] = []
    failures: list[dict[str, str]] = []
    attempts = max(1, int(max_retries or 0) + 1)

    for recipient in recipients:
        last_error = ""
        for attempt in range(1, attempts + 1):
            try:
                msg = MIMEMultipart("alternative")
                msg["From"] = sender
                msg["To"] = recipient
                msg["Subject"] = subject
                msg.attach(MIMEText(html, "html", "utf-8"))

                raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
                result: dict = (
                    service.users().messages().send(userId="me", body={"raw": raw}).execute()
                )
                result["recipient"] = recipient
                log.info(
                    "Email sent | recipient=%s | message_id=%s | attempt=%s",
                    recipient,
                    result.get("id"),
                    attempt,
                )
                results.append(result)
                last_error = ""
                break
            except Exception as exc:
                last_error = str(exc)
                log.warning(
                    "Failed to send to %s on attempt %s/%s: %s",
                    recipient,
                    attempt,
                    attempts,
                    exc,
                )
                if attempt < attempts:
                    sleep(max(throttle_seconds, 0) * attempt)

        if last_error:
            failures.append({"recipient": recipient, "error": last_error[:1000]})

        if throttle_seconds > 0:
            sleep(throttle_seconds)

    if failures and not results:
        raise RuntimeError("All sends failed:\n" + "\n".join(f"{f['recipient']}: {f['error']}" for f in failures))
    if failures:
        log.warning(
            "Partial send failures (%d/%d):\n%s",
            len(failures),
            len(recipients),
            "\n".join(f"{f['recipient']}: {f['error']}" for f in failures),
        )

    return BulkSendResult(results=results, failures=failures)
