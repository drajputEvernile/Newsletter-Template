import { useEffect, useState } from "react";

type Props = {
  counts: number[];
  onClose: () => void;
};

type Status = { configured: boolean; reason: string; sender: string; max_recipients: number };
type SendResult = { sent: string[]; failures: { recipient: string; error: string }[] };

async function api<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`/api/${path}`, {
    method: body ? "POST" : "GET",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(typeof data.detail === "string" ? data.detail : `Request failed (${res.status})`);
  return data as T;
}

/** Preview-only popup: sends the current format as a real email. Not part of the newsletter. */
export default function EmailPanel({ counts, onClose }: Props) {
  const [status, setStatus] = useState<Status | null>(null);
  const [recipients, setRecipients] = useState("");
  const [sending, setSending] = useState(false);
  const [result, setResult] = useState<SendResult | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<Status>("status").then(setStatus, (e: Error) =>
      setStatus({ configured: false, reason: `Email server not reachable: ${e.message}`, sender: "", max_recipients: 0 }),
    );
  }, []);

  const send = async () => {
    setSending(true);
    setResult(null);
    setError("");
    try {
      setResult(await api<SendResult>("send", { counts, recipients: [recipients] }));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSending(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center bg-black/40 p-4"
      onClick={onClose}
      role="presentation"
    >
      <div
        className="w-full max-w-md space-y-3 rounded-xl border border-border bg-card p-5 shadow-xl"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-label="Send email"
      >
        <h2 className="text-base font-semibold text-foreground">Send this newsletter by email</h2>
        <p className="text-xs text-muted-foreground">
          Format: {counts.join(" / ")} (Healthcare / Consumer / BFSI / Technology)
          {status?.configured && (
            <>
              <br />
              Sending from <strong>{status.sender}</strong>
            </>
          )}
        </p>
        {status && !status.configured && (
          <p className="rounded-md border border-destructive/40 bg-destructive/10 p-2 text-xs text-destructive">
            Sending unavailable: {status.reason}
          </p>
        )}
        <label className="block text-sm font-medium text-foreground">
          Email address(es)
          <textarea
            value={recipients}
            onChange={(e) => setRecipients(e.target.value)}
            rows={3}
            autoFocus
            placeholder="name@example.com, other@example.com"
            className="mt-1 w-full rounded-md border border-input bg-background p-2 text-sm"
          />
          <span className="text-xs font-normal text-muted-foreground">
            Separate several with commas, spaces or new lines.
          </span>
        </label>
        {error && <p className="text-sm text-destructive">{error}</p>}
        {result && (
          <div className="space-y-1 text-sm">
            {result.sent.length > 0 && <p className="text-emerald-700">Sent to: {result.sent.join(", ")}</p>}
            {result.failures.map((f) => (
              <p key={f.recipient} className="text-destructive">
                Failed {f.recipient}: {f.error}
              </p>
            ))}
          </div>
        )}
        <div className="flex justify-end gap-2 pt-1">
          <button
            type="button"
            onClick={onClose}
            className="rounded-md border border-border bg-card px-3 py-1.5 text-sm font-medium hover:bg-muted"
          >
            Close
          </button>
          <button
            type="button"
            onClick={send}
            disabled={sending || !recipients.trim() || !status?.configured}
            className="rounded-md border border-accent bg-accent px-3 py-1.5 text-sm font-medium text-accent-foreground disabled:opacity-50"
          >
            {sending ? "Sending…" : "Send"}
          </button>
        </div>
      </div>
    </div>
  );
}
