import { useState } from "react";
import { sendChat } from "../api";

interface Msg {
  role: "user" | "agent";
  text: string;
}

interface Props {
  customerEmail: string;
  onAfterReply: () => void;
}

export function ChatWindow({ customerEmail, onAfterReply }: Props) {
  const [messages, setMessages] = useState<Msg[]>([
    { role: "agent", text: "Hi! How can I help you today?" },
  ]);
  const [input, setInput] = useState("");
  const [threadId, setThreadId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || busy) return;
    const text = input.trim();
    setMessages((m) => [...m, { role: "user", text }]);
    setInput("");
    setBusy(true);
    try {
      const res = await sendChat(text, threadId, customerEmail);
      setThreadId(res.thread_id);
      setMessages((m) => [...m, { role: "agent", text: res.reply }]);
      onAfterReply();
    } catch (err) {
      setMessages((m) => [
        ...m,
        { role: "agent", text: `Sorry, the agent is unavailable: ${(err as Error).message}` },
      ]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="chat">
      <div className="chat__log">
        {messages.map((m, i) => (
          <div key={i} className={`bubble bubble--${m.role}`}>
            {m.text}
          </div>
        ))}
        {busy && <div className="bubble bubble--agent">…thinking</div>}
      </div>
      <form className="chat__form" onSubmit={submit}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Describe your issue…"
        />
        <button type="submit" disabled={busy}>Send</button>
      </form>
    </section>
  );
}
