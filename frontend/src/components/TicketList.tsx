import type { Ticket } from "../api";

interface Props {
  tickets: Ticket[];
}

export function TicketList({ tickets }: Props) {
  return (
    <section className="tickets">
      <h2>Tickets</h2>
      {tickets.length === 0 && <p className="muted">No tickets yet.</p>}
      <ul>
        {tickets.map((t) => (
          <li key={t.id} className={`ticket ticket--${t.priority}`}>
            <span className="ticket__id">#{t.id}</span>
            <span className="ticket__subject">{t.subject}</span>
            <span className={`ticket__status ticket__status--${t.status}`}>{t.status}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
