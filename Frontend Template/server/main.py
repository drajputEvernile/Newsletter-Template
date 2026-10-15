"""Email send API for the Frontend Template (http://127.0.0.1:1002).

POST /api/send    {counts, recipients}   -> {sent, failures}
GET  /api/status                         -> {configured, sender, reason}

Rendering and sending use the production code unchanged: `pipeline/shared/email_renderer.py`
and `gmail.py` are byte-for-byte copies of the backend files. Per-count email bodies live in
`email_layouts/` (one file per news-per-sector count) and are plugged into that renderer.

The sender is the NAME of the folder under `server/credentials/` that holds that mailbox's
`credentials.json` and `token.json`, e.g. `server/credentials/someone@example.com/`.
`counts` is the news per sector in order Healthcare, Consumer, BFSI, Technology.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SERVER_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SERVER_DIR))  # so `pipeline.shared.*` resolves like in the backend

from fastapi import FastAPI, HTTPException  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from pipeline.shared.config import getenv_optional  # noqa: E402
from email_layouts import render_email  # noqa: E402
from pipeline.shared.gmail import send_html_emails_individually  # noqa: E402

DATA_FILE = SERVER_DIR.parent / "src" / "data" / "newsletter.json"
CREDENTIALS_DIR = SERVER_DIR / "credentials"
SECTOR_ORDER = ["Healthcare", "Consumer", "BFSI", "Technology"]
MAX_PER_SECTOR = 5
MAX_RECIPIENTS = int(getenv_optional("MAX_RECIPIENTS", "10"))
# Main app's default subject (routes/email.py), prefixed so test sends are recognisable.
SUBJECT = "[Testing] Capital Flow By Evernile"
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

app = FastAPI(title="Newsletter template email server")


class SendRequest(BaseModel):
    counts: list[int] = Field(min_length=len(SECTOR_ORDER), max_length=len(SECTOR_ORDER))
    recipients: list[str]


def _sender_account() -> tuple[str, Path, Path, str]:
    """(sender, token.json, credentials.json, problem) from `server/credentials/<sender>/`."""
    folders = sorted(
        d
        for d in (CREDENTIALS_DIR.iterdir() if CREDENTIALS_DIR.is_dir() else [])
        if d.is_dir() and _EMAIL_RE.match(d.name)
    )
    if not folders:
        return "", Path(), Path(), "No sender folder in server/credentials/ (name it after the sender email)."
    wanted = getenv_optional("GMAIL_SENDER_EMAIL").lower()
    folder = next((d for d in folders if d.name.lower() == wanted), folders[0])
    token, secret = folder / "token.json", folder / "credentials.json"
    missing = [p.name for p in (token, secret) if not p.is_file()]
    if missing:
        return folder.name, token, secret, f"{folder.name}: missing {', '.join(missing)}"
    return folder.name, token, secret, ""


def _payload(counts: list[int]) -> dict:
    """Sample newsletter trimmed to `counts[i]` stories for sector `SECTOR_ORDER[i]`."""
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    sectors = data.get("sectors", {})
    trimmed = {}
    for label, n in zip(SECTOR_ORDER, counts):
        n = max(1, min(MAX_PER_SECTOR, n))
        articles = sorted(sectors.get(label, []), key=lambda a: a.get("priority_rank", 99))
        trimmed[label] = articles[:n]
    return {"summary_date": data.get("summary_date", ""), "sectors": trimmed}


def _parse_recipients(raw: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for entry in raw:
        for addr in re.split(r"[,;\s]+", entry):
            addr = addr.strip()
            if not addr or addr.lower() in seen:
                continue
            if not _EMAIL_RE.match(addr):
                raise HTTPException(422, f"Invalid email address: {addr!r}")
            seen.add(addr.lower())
            out.append(addr)
    return out


@app.get("/api/status")
def status():
    sender, _, _, problem = _sender_account()
    return {"configured": not problem, "reason": problem, "sender": sender, "max_recipients": MAX_RECIPIENTS}


@app.post("/api/send")
def send(req: SendRequest):
    sender, token, secret, problem = _sender_account()
    if problem:
        raise HTTPException(503, problem)
    recipients = _parse_recipients(req.recipients)
    if not recipients:
        raise HTTPException(422, "Enter at least one email address.")
    if len(recipients) > MAX_RECIPIENTS:
        raise HTTPException(422, f"At most {MAX_RECIPIENTS} recipients per send.")

    html = render_email(_payload(req.counts))
    try:
        report = send_html_emails_individually(
            html=html,
            recipients=recipients,
            subject=SUBJECT,
            sender=sender,
            token_path=token,
            client_secret_path=secret,
        )
    except Exception as exc:
        raise HTTPException(502, f"Gmail error: {exc}") from exc
    return {"sent": report.successful_recipients, "failures": report.failures}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=1002)
