"use client";
import { useCallback, useEffect, useState } from "react";
import { api, ApiError, type Identity } from "../lib/api";
import ProductionStudio from "../components/ProductionStudio";
export default function Home() {
  const [identity, setIdentity] = useState<Identity | null>(null);
  const [checking, setChecking] = useState(true);
  const [key, setKey] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const signedOut = useCallback(() => setIdentity(null), []);
  useEffect(() => {
    api<Identity>("/me")
      .then(setIdentity)
      .catch((e) => {
        if (!(e instanceof ApiError) || e.status !== 401) setError(e.message);
      })
      .finally(() => setChecking(false));
  }, []);
  async function signIn(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      setIdentity(
        await api<Identity>("/auth/login", {
          method: "POST",
          body: JSON.stringify({ key }),
        }),
      );
      setKey("");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (identity)
    return <ProductionStudio identity={identity} onSignOut={signedOut} />;
  return (
    <main className="login-shell">
      <div className="login-art" aria-hidden="true">
        <div className="orbit orbit-one" />
        <div className="orbit orbit-two" />
        <div className="art-sun" />
        <div className="art-mountain" />
        <div className="art-caption">
          A NEW CHAPTER
          <br />
          <span>starts here.</span>
        </div>
        <span className="art-footnote">
          FLAMINGO NEXT STUDIO / INDEPENDENT BY DESIGN
        </span>
      </div>
      <section className="login-content">
        <div className="brand">
          <span className="brand-mark">
            f<span>.</span>
          </span>
          <div>
            flamingo<span className="brand-small">NEXT STUDIO</span>
          </div>
        </div>
        <p className="eyebrow">YOUR PRIVATE CREATIVE WORKSPACE</p>
        <h1>
          Good stories.
          <br />
          Thoughtfully made.
        </h1>
        <p className="login-intro">
          Bring authorized chapters into a source-linked editorial workflow.
          Write, narrate, render and review a private film locally.
        </p>
        <form onSubmit={signIn}>
          <label htmlFor="access-key">Local studio access key</label>
          <input
            id="access-key"
            type="password"
            autoComplete="current-password"
            required
            value={key}
            onChange={(e) => setKey(e.target.value)}
            placeholder="Enter your local access key"
            disabled={checking}
          />
          <button className="primary login-button" disabled={busy || checking}>
            {checking
              ? "Connecting to studio…"
              : busy
                ? "Opening studio…"
                : "Open your studio"}
            <span>↗</span>
          </button>
        </form>
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        <p className="login-help">
          The launcher displays this key when you run{" "}
          <code>./start-studio.command</code>.
        </p>
        <div className="login-safety">
          <span className="live-dot" /> Local owner session
          <span>System voice · Publishing off · No paid providers</span>
        </div>
      </section>
    </main>
  );
}
