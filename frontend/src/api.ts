const API_BASE = import.meta.env.VITE_API_BASE ?? "";

export interface ChatReply {
  thread_id: string;
  reply: string;
}

export interface Ticket {
  id: number;
  subject: string;
  status: string;
  priority: string;
  customer_id: number;
  created_at: string;
}

export async function sendChat(
  message: string,
  threadId: string | null,
  customerEmail: string
): Promise<ChatReply> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      thread_id: threadId,
      customer_email: customerEmail,
    }),
  });
  if (!res.ok) throw new Error(`Chat failed: ${res.status}`);
  return res.json();
}

export async function listTickets(): Promise<Ticket[]> {
  const res = await fetch(`${API_BASE}/tickets`);
  if (!res.ok) throw new Error(`List failed: ${res.status}`);
  return res.json();
}

export async function uploadFile(ticketId: number, file: File): Promise<unknown> {
  const fd = new FormData();
  fd.append("ticket_id", String(ticketId));
  fd.append("file", file);
  const res = await fetch(`${API_BASE}/uploads`, { method: "POST", body: fd });
  if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
  return res.json();
}
