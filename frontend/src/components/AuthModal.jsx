import { useState } from "react";
import { loginUser, registerUser } from "../api.js";

const DEMO_ACCOUNTS = [
  { handle: "asha", name: "Asha", bio: "Building things, one commit at a time." },
  { handle: "devpatel", name: "Dev Patel", bio: "Backend and infra." },
  { handle: "mayachen", name: "Maya Chen", bio: "Product engineer." },
  { handle: "leomartins", name: "Leo Martins", bio: "Design + frontend." },
  { handle: "zaraahmed", name: "Zara Ahmed", bio: "Learning in public." },
  { handle: "kenjiw", name: "Kenji Watanabe", bio: "Distributed systems." },
];

export default function AuthModal({ isOpen, onClose, onAuthSuccess }) {
  const [mode, setMode] = useState("login"); // "login" | "register"
  const [handle, setHandle] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [bio, setBio] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  if (!isOpen) return null;

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);
    setLoading(true);

    if (mode === "register" && password.trim().length < 8) {
      setError("Password must be at least 8 characters long");
      setLoading(false);
      return;
    }

    try {
      if (mode === "login") {
        const data = await loginUser({ handle: handle.trim(), password });
        onAuthSuccess(data.user);
        onClose();
      } else {
        await registerUser({ handle: handle.trim(), displayName: displayName.trim(), password, bio: bio.trim() }, false);
        setSuccessMsg(`Account @${handle.trim()} created successfully! Please sign in with your password.`);
        setMode("login");
        setPassword("");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleQuickLogin(accountHandle) {
    setError(null);
    setLoading(true);
    try {
      const data = await loginUser({ handle: accountHandle, password: "password123" });
      onAuthSuccess(data.user);
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        backgroundColor: "rgba(91, 112, 131, 0.4)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: "#000",
          border: "1px solid #2f3336",
          borderRadius: "16px",
          width: "90%",
          maxWidth: "460px",
          padding: "28px",
          color: "#e7e9ea",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <h2 style={{ margin: 0, fontSize: "22px" }}>
            {mode === "login" ? "Sign in to Social Feed" : "Create your account"}
          </h2>
          <button
            onClick={onClose}
            style={{
              background: "transparent",
              border: "none",
              color: "#e7e9ea",
              fontSize: "20px",
              cursor: "pointer",
            }}
          >
            ✕
          </button>
        </div>

        {/* Quick Demo Switcher */}
        <div style={{ marginBottom: "20px", padding: "12px", background: "#16181c", borderRadius: "12px" }}>
          <span style={{ fontSize: "12px", color: "#71767b", display: "block", marginBottom: "8px" }}>
            ⚡ 1-Click Sign In (Pre-seeded Accounts):
          </span>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
            {DEMO_ACCOUNTS.map((acc) => (
              <button
                key={acc.handle}
                disabled={loading}
                onClick={() => handleQuickLogin(acc.handle)}
                style={{
                  background: "#202327",
                  border: "1px solid #333",
                  color: "#e7e9ea",
                  padding: "4px 10px",
                  borderRadius: "999px",
                  fontSize: "12px",
                  cursor: "pointer",
                }}
              >
                @{acc.handle}
              </button>
            ))}
          </div>
        </div>

        {/* Mode Switcher */}
        <div style={{ display: "flex", borderBottom: "1px solid #2f3336", marginBottom: "20px" }}>
          <button
            onClick={() => { setMode("login"); setError(null); }}
            style={{
              flex: 1,
              background: "transparent",
              border: "none",
              borderBottom: mode === "login" ? "3px solid #1d9bf0" : "none",
              color: mode === "login" ? "#fff" : "#71767b",
              fontWeight: "bold",
              padding: "10px",
              cursor: "pointer",
            }}
          >
            Sign In
          </button>
          <button
            onClick={() => { setMode("register"); setError(null); }}
            style={{
              flex: 1,
              background: "transparent",
              border: "none",
              borderBottom: mode === "register" ? "3px solid #1d9bf0" : "none",
              color: mode === "register" ? "#fff" : "#71767b",
              fontWeight: "bold",
              padding: "10px",
              cursor: "pointer",
            }}
          >
            Register
          </button>
        </div>

        {successMsg && (
          <div style={{ background: "rgba(0, 186, 124, 0.15)", border: "1px solid #00ba7c", color: "#00ba7c", padding: "10px", borderRadius: "8px", marginBottom: "14px", fontSize: "14px" }}>
            ✓ {successMsg}
          </div>
        )}

        {error && (
          <div style={{ background: "rgba(244, 33, 46, 0.1)", border: "1px solid #f4212e", color: "#f4212e", padding: "10px", borderRadius: "8px", marginBottom: "14px", fontSize: "14px" }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          <div>
            <label style={{ fontSize: "13px", color: "#71767b" }}>Handle</label>
            <input
              type="text"
              required
              placeholder="e.g. johndoe"
              value={handle}
              onChange={(e) => setHandle(e.target.value)}
              style={{
                width: "100%",
                padding: "10px",
                background: "#000",
                border: "1px solid #333",
                borderRadius: "6px",
                color: "#fff",
                marginTop: "4px",
              }}
            />
          </div>

          {mode === "register" && (
            <div>
              <label style={{ fontSize: "13px", color: "#71767b" }}>Display Name</label>
              <input
                type="text"
                required
                placeholder="e.g. John Doe"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                style={{
                  width: "100%",
                  padding: "10px",
                  background: "#000",
                  border: "1px solid #333",
                  borderRadius: "6px",
                  color: "#fff",
                  marginTop: "4px",
                }}
              />
            </div>
          )}

          <div>
            <label style={{ fontSize: "13px", color: "#71767b" }}>Password</label>
            <input
              type="password"
              required
              minLength={mode === "register" ? 8 : 1}
              placeholder={mode === "register" ? "At least 8 characters" : "••••••••"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{
                width: "100%",
                padding: "10px",
                background: "#000",
                border: "1px solid #333",
                borderRadius: "6px",
                color: "#fff",
                marginTop: "4px",
              }}
            />
            {mode === "register" && (
              <span style={{ display: "block", fontSize: "12px", color: "#71767b", marginTop: "4px" }}>
                Must be at least 8 characters long
              </span>
            )}
          </div>

          {mode === "register" && (
            <div>
              <label style={{ fontSize: "13px", color: "#71767b" }}>Bio (Optional)</label>
              <textarea
                rows={2}
                placeholder="Tell us about yourself..."
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                style={{
                  width: "100%",
                  padding: "10px",
                  background: "#000",
                  border: "1px solid #333",
                  borderRadius: "6px",
                  color: "#fff",
                  marginTop: "4px",
                  resize: "none",
                }}
              />
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              marginTop: "8px",
              padding: "12px",
              background: "#1d9bf0",
              color: "#fff",
              border: "none",
              borderRadius: "999px",
              fontWeight: "bold",
              fontSize: "15px",
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            {loading ? "Processing..." : mode === "login" ? "Sign In" : "Create Account"}
          </button>
        </form>
      </div>
    </div>
  );
}
