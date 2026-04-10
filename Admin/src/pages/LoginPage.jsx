import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function LoginPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: "", password: "" });
  const [error, setError] = useState("");

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (event) => {
    event.preventDefault();

    if (form.username === "admin" && form.password === "admin123") {
      localStorage.setItem("pethub_admin_logged_in", "true");
      navigate("/home");
      return;
    }

    setError("Invalid username or password.");
  };

  return (
    <main className="page-shell">
      <section className="auth-card fade-in-up">
        <div>
          <p className="tag">PetHub Admin</p>
          <h1>Welcome back</h1>
          <p className="muted">Use your admin account to continue.</p>
        </div>

        <form onSubmit={handleSubmit} className="stack-lg">
          <label className="field">
            <span>Username</span>
            <input
              type="text"
              name="username"
              placeholder="Enter username"
              value={form.username}
              onChange={handleChange}
              required
            />
          </label>

          <label className="field">
            <span>Password</span>
            <input
              type="password"
              name="password"
              placeholder="Enter password"
              value={form.password}
              onChange={handleChange}
              required
            />
          </label>

          {error ? <p className="error-text">{error}</p> : null}

          <button type="submit" className="btn-primary">
            Login
          </button>
        </form>

        <p className="hint">Demo credentials: admin / admin123</p>
      </section>
    </main>
  );
}