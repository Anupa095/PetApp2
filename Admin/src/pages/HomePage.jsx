import { useNavigate } from "react-router-dom";

export default function HomePage() {
  const navigate = useNavigate();

  return (
    <main className="page-shell">
      <section className="content-card fade-in-up">
        <div className="title-row">
          <div>
            <p className="tag">Admin Home</p>
            <h1>PetHub Control Room</h1>
            <p className="muted">
              Monitor your platform and move quickly between admin tasks.
            </p>
          </div>
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

        <div className="grid-3">
          <article className="panel">
            <h2>Total Pets</h2>
            <p className="big">1,248</p>
          </article>
          <article className="panel">
            <h2>Pending Reports</h2>
            <p className="big">23</p>
          </article>
          <article className="panel">
            <h2>Active Shelters</h2>
            <p className="big">61</p>
          </article>
        </div>

        <button className="btn-primary" onClick={() => navigate("/dashboard")}>
          Go to Dashboard
        </button>
      </section>
    </main>
  );
}