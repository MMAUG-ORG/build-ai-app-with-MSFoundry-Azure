import { useRef, useState } from "react";
import { uploadFile, type Ticket } from "../api";

interface Props {
  tickets: Ticket[];
}

function TicketRow({ ticket }: { ticket: Ticket }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [status, setStatus] = useState<"idle" | "uploading" | "ok" | "error">("idle");
  const [message, setMessage] = useState<string>("");

  const onPick = () => inputRef.current?.click();

  const onChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setStatus("uploading");
    setMessage(file.name);
    try {
      await uploadFile(ticket.id, file);
      setStatus("ok");
      setMessage(`Uploaded ${file.name}`);
    } catch (err) {
      setStatus("error");
      setMessage(err instanceof Error ? err.message : "Upload failed");
    } finally {
      if (inputRef.current) inputRef.current.value = "";
    }
  };

  return (
    <li className={`ticket ticket--${ticket.priority}`}>
      <span className="ticket__id">#{ticket.id}</span>
      <span className="ticket__subject">{ticket.subject}</span>
      <span className={`ticket__status ticket__status--${ticket.status}`}>{ticket.status}</span>
      <button
        type="button"
        className="ticket__attach"
        onClick={onPick}
        disabled={status === "uploading"}
        title="Attach a file (e.g. screenshot, log) to this ticket"
      >
        {status === "uploading" ? "Uploading…" : "📎 Attach"}
      </button>
      <input ref={inputRef} type="file" hidden onChange={onChange} />
      {status !== "idle" && (
        <span className={`ticket__attach-msg ticket__attach-msg--${status}`}>{message}</span>
      )}
    </li>
  );
}

export function TicketList({ tickets }: Props) {
  return (
    <section className="tickets">
      <h2>Tickets</h2>
      {tickets.length === 0 && <p className="muted">No tickets yet.</p>}
      <ul>
        {tickets.map((t) => (
          <TicketRow key={t.id} ticket={t} />
        ))}
      </ul>
    </section>
  );
}
