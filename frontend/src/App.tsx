import { useEffect, useState } from "react";
import { ChatWindow } from "./components/ChatWindow";
import { TicketList } from "./components/TicketList";
import { listTickets, type Ticket } from "./api";

export function App() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [email, setEmail] = useState("alice@contoso.com");

  const refresh = () =>
    listTickets()
      .then(setTickets)
      .catch(() => setTickets([]));

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 5000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="layout">
      <header>
        <h1>MMAUG · Foundry Support</h1>
        <label>
          Customer&nbsp;
          <input value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
      </header>
      <main>
        <ChatWindow customerEmail={email} onAfterReply={refresh} />
        <TicketList tickets={tickets} />
      </main>
      <footer>Built for the Malta Microsoft AI User Group · 9 May 2026</footer>
    </div>
  );
}
