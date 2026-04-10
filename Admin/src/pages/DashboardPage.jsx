import { useNavigate } from "react-router-dom";

const recentRequests = [
  { id: "REQ-301", type: "Adoption", status: "Pending" },
  { id: "REQ-299", type: "Report", status: "In Review" },
  { id: "REQ-294", type: "Verification", status: "Approved" }
];

export default function DashboardPage() {
  const navigate = useNavigate();

  return (
    <main className="page-shell">
      <section className="content-card fade-in-up">
        <div className="title-row">
          <div>
            <p className="tag">Admin Dashboard</p>
            <h1>Operations Overview</h1>
            <p className="muted">Live status of requests, users, and moderation queue.</p>
          </div>
          <div className="row-actions">
            <button className="btn-secondary" onClick={() => navigate("/home")}>Home</button>
            <button
              className="btn-secondary"
              onClick={() => {
                localStorage.removeItem("pethub_admin_logged_in");
                navigate("/login");
              }}
            >
              Logout
            </button>
          </div>
        </div>

        <div className="grid-3">
          <article className="panel">
            <h2>New Users (24h)</h2>
            <p className="big">89</p>
          </article>
          <article className="panel">
            <h2>Open Tickets</h2>
            <p className="big">17</p>
          </article>
          <article className="panel">
            <h2>Resolved Today</h2>
            <p className="big">42</p>
          </article>
        </div>

        <article className="panel table-wrap">
          <h2>Recent Requests</h2>
          <table>
            <thead>
              <tr>
                <th>Request ID</th>
                <th>Type</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {recentRequests.map((item) => (
                <tr key={item.id}>
                  <td>{item.id}</td>
                  <td>{item.type}</td>
                  <td>{item.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </article>
      </section>
    </main>
  );
}