"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError, type Identity, type Job } from "../lib/api";

type Workspace =
  "Control Tower" | "Episode Studio" | "Quality Director" | "Operations";
const navigation: { label: Workspace; icon: string }[] = [
  { label: "Control Tower", icon: "◈" },
  { label: "Episode Studio", icon: "▤" },
  { label: "Quality Director", icon: "◎" },
  { label: "Operations", icon: "⚙" },
];
const stages = ["Accepted", "Fake provider", "Private preview", "Your review"];
const displayState = (state: Job["state"]) =>
  ({
    QUEUED: "Queued",
    RUNNING: "Preparing",
    REVIEW: "Ready for review",
    CANCELLED: "Cancelled",
    FAILED: "Needs attention",
  })[state];
const date = (value: string) =>
  new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value));

function Mark() {
  return (
    <span className="brand-mark" aria-hidden="true">
      f<span>.</span>
    </span>
  );
}

export default function Home() {
  const [identity, setIdentity] = useState<Identity | null>(null);
  const [checking, setChecking] = useState(true);
  const [key, setKey] = useState("");
  const [error, setError] = useState("");
  const [jobs, setJobs] = useState<Job[]>([]);
  const [workspace, setWorkspace] = useState<Workspace>("Control Tower");
  const [filter, setFilter] = useState("All episodes");
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [preview, setPreview] = useState("");
  const [previewError, setPreviewError] = useState("");
  const [creating, setCreating] = useState(false);
  const [title, setTitle] = useState("Beyond the Last Horizon");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const createKey = useRef<string | null>(null);
  const modalRef = useRef<HTMLElement>(null);
  useEffect(() => {
    if (!creating) return;
    const previous = document.activeElement as HTMLElement | null;
    const trap = (event: KeyboardEvent) => {
      if (event.key !== "Tab") return;
      const nodes = modalRef.current?.querySelectorAll<HTMLElement>(
        "button:not(:disabled), input:not(:disabled)",
      );
      if (!nodes?.length) return;
      const first = nodes[0],
        last = nodes[nodes.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", trap);
    return () => {
      document.removeEventListener("keydown", trap);
      previous?.focus();
    };
  }, [creating]);
  const selected = jobs.find((j) => j.id === selectedId);

  const refresh = useCallback(async () => {
    try {
      setJobs(await api<Job[]>("/jobs"));
      setError("");
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) setIdentity(null);
      setError((err as Error).message);
    }
  }, []);

  useEffect(() => {
    api<Identity>("/me")
      .then(setIdentity)
      .catch((err) => {
        if (!(err instanceof ApiError) || err.status !== 401)
          setError(err.message);
      })
      .finally(() => setChecking(false));
  }, []);
  useEffect(() => {
    if (!identity) return;
    void refresh();
    const timer = setInterval(() => void refresh(), 2500);
    return () => clearInterval(timer);
  }, [identity, refresh]);
  useEffect(() => {
    setPreview("");
    setPreviewError("");
    if (!selected?.artifact_sha || !identity) return;
    let active = true;
    const load = () =>
      api<{ url: string }>(`/jobs/${selected.id}/preview`)
        .then((data) => {
          if (active) {
            setPreview(data.url);
            setPreviewError("");
          }
        })
        .catch((err) => {
          if (active) setPreviewError(err.message);
        });
    void load();
    const timer = setInterval(() => void load(), 240000);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [selected?.id, selected?.artifact_sha, identity]);

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
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function signOut() {
    try {
      await api("/auth/logout", {
        method: "POST",
        headers: { "X-CSRF-Token": identity!.csrf },
      });
      setIdentity(null);
      setJobs([]);
      setSelectedId(null);
      setError("");
    } catch (err) {
      setError((err as Error).message);
    }
  }
  async function create(event: React.FormEvent) {
    event.preventDefault();
    if (!identity) return;
    setBusy(true);
    setError("");
    createKey.current ??= crypto.randomUUID();
    try {
      const job = await api<Job>("/jobs", {
        method: "POST",
        headers: {
          "X-CSRF-Token": identity.csrf,
          "Idempotency-Key": createKey.current,
        },
        body: JSON.stringify({ title, source_kind: "synthetic" }),
      });
      createKey.current = null;
      setSelectedId(job.id);
      setCreating(false);
      setWorkspace("Episode Studio");
      setNotice(
        "Synthetic episode queued. The local worker will prepare your preview.",
      );
      await refresh();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function cancel(job: Job) {
    setBusy(true);
    try {
      await api(`/jobs/${job.id}/cancel`, {
        method: "POST",
        headers: { "X-CSRF-Token": identity!.csrf },
        body: JSON.stringify({ revision: job.revision }),
      });
      setNotice("Job cancelled. It will stay cancelled after restart.");
      await refresh();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const reviewCount = jobs.filter((j) => j.state === "REVIEW").length;
  const activeCount = jobs.filter((j) =>
    ["QUEUED", "RUNNING"].includes(j.state),
  ).length;
  const visible = jobs.filter(
    (j) =>
      (workspace !== "Quality Director" || j.state === "REVIEW") &&
      j.title.toLowerCase().includes(query.toLowerCase()) &&
      (filter === "All episodes" ||
        (filter === "In progress"
          ? ["QUEUED", "RUNNING"].includes(j.state)
          : filter === "For review"
            ? j.state === "REVIEW"
            : ["CANCELLED", "FAILED"].includes(j.state))),
  );

  if (!identity)
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
            <Mark />
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
            A calmer place to build your next episode. Start with an original
            synthetic workflow in your local studio.
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
            <button
              className="primary login-button"
              disabled={busy || checking}
            >
              {checking
                ? "Connecting to studio…"
                : busy
                  ? "Opening studio…"
                  : "Open your studio"}{" "}
              <span>↗</span>
            </button>
          </form>
          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}
          <p className="login-help">
            Your launcher displays this key when you run{" "}
            <code>./start-studio.command</code>.
          </p>
          <div className="login-safety">
            <span className="live-dot" /> Local workspace{" "}
            <span>Publishing off · Fake providers only</span>
          </div>
        </section>
      </main>
    );

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <Mark />
          <div>
            flamingo<span className="brand-small">NEXT STUDIO</span>
          </div>
        </div>
        <div className="workspace-label">
          CREATOR WORKSPACE <span>01</span>
        </div>
        <nav aria-label="Studio workspaces">
          {navigation.map((item) => (
            <button
              key={item.label}
              className={
                workspace === item.label ? "nav-item active" : "nav-item"
              }
              onClick={() => {
                setWorkspace(item.label);
                setFilter("All episodes");
                setNotice("");
              }}
            >
              <span aria-hidden="true">{item.icon}</span>
              {item.label}
              {item.label === "Quality Director" && reviewCount > 0 && (
                <b>{reviewCount}</b>
              )}
            </button>
          ))}
        </nav>
        <div className="coming-next">
          <span className="workspace-label">ON THE ROADMAP</span>
          <span>
            Research Desk <small>Planned</small>
          </span>
          <span>
            Series Room <small>Planned</small>
          </span>
          <span>
            Packaging Studio <small>Planned</small>
          </span>
          <span>
            Publishing Desk <small>Off</small>
          </span>
        </div>
        <div className="sidebar-bottom">
          <div className="local-card">
            <span className="live-dot" /> Independent & local
            <p>Original fixtures. Zero provider spend.</p>
          </div>
          <button className="profile" onClick={signOut}>
            <span className="avatar">K</span>
            <span>
              Studio owner<small>Local session</small>
            </span>
            <span className="logout">Sign out ↗</span>
          </button>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div>
            <span className="breadcrumb">Workspace</span>
            <span className="slash">/</span>
            {workspace}
          </div>
          <div className="topbar-right">
            <span className="environment">LOCAL FOUNDATION</span>
            <span className="live-dot" />
            <span>Publishing off</span>
            <button className="mobile-signout" onClick={signOut}>
              Sign out
            </button>
          </div>
        </header>
        <main className="workspace-main">
          <div className="page-heading">
            <div>
              <p className="eyebrow">THE WORK BEHIND THE STORY</p>
              <h1>
                {workspace === "Control Tower"
                  ? "Your studio, at a glance."
                  : workspace === "Episode Studio"
                    ? "Make room for the story."
                    : workspace === "Quality Director"
                      ? "A little closer to ready."
                      : "Built on a solid foundation."}
              </h1>
              <p>
                {workspace === "Control Tower"
                  ? "One clear view of what’s moving, what’s ready, and what needs you."
                  : workspace === "Episode Studio"
                    ? "Follow your synthetic episode from the queue to a private preview."
                    : workspace === "Quality Director"
                      ? "Inspect the preview and its provenance. Final media QA comes later."
                      : "A transparent view of this independent, local environment."}
              </p>
            </div>
            <button
              className="primary"
              onClick={() => {
                setCreating(true);
                createKey.current = null;
                setError("");
              }}
            >
              <span>＋</span> New synthetic episode
            </button>
          </div>
          {error && (
            <div className="error banner" role="alert">
              {error}
            </div>
          )}
          {notice && (
            <div className="notice" role="status">
              {notice}
              <button
                onClick={() => setNotice("")}
                aria-label="Dismiss notification"
              >
                ×
              </button>
            </div>
          )}
          {workspace === "Operations" ? (
            <section className="operations">
              <article className="panel">
                <div className="section-title">
                  <h2>Environment & boundaries</h2>
                  <span className="pill green">Local only</span>
                </div>
                <dl className="settings-list">
                  <div>
                    <dt>Database</dt>
                    <dd>Dedicated PostgreSQL · durable jobs</dd>
                  </div>
                  <div>
                    <dt>Media storage</dt>
                    <dd>Private MinIO · SHA-256 verified</dd>
                  </div>
                  <div>
                    <dt>Identity</dt>
                    <dd>Local owner · revocable session</dd>
                  </div>
                  <div>
                    <dt>Provider</dt>
                    <dd>Deterministic fake · no network calls</dd>
                  </div>
                  <div>
                    <dt>Publishing / Drive / Autopilot</dt>
                    <dd>Off / Off / Off</dd>
                  </div>
                  <div>
                    <dt>Production authentication</dt>
                    <dd>Not implemented · local use only</dd>
                  </div>
                </dl>
              </article>
              <article className="panel roadmap-note">
                <span className="eyebrow">THE NEXT MILESTONE</span>
                <h2>Foundation before acceleration.</h2>
                <p>
                  This slice verifies a durable synthetic job and a protected
                  image preview. Real source ingestion, narration, MP4 exports
                  and cloud staging remain on the roadmap.
                </p>
              </article>
            </section>
          ) : (
            <>
              <section className="metrics" aria-label="Studio overview">
                <article>
                  <span className="metric-label">
                    Episode workspace <span>▤</span>
                  </span>
                  <strong>{String(jobs.length).padStart(2, "0")}</strong>
                  <span className="metric-foot">
                    Synthetic episodes in this studio
                  </span>
                </article>
                <article>
                  <span className="metric-label">
                    In progress <span className="amber">◌</span>
                  </span>
                  <strong>{String(activeCount).padStart(2, "0")}</strong>
                  <span className="metric-foot">
                    <span className="live-dot amber-bg" /> Local worker queue
                  </span>
                </article>
                <article>
                  <span className="metric-label">
                    Ready for your eye <span className="green-text">◎</span>
                  </span>
                  <strong>{String(reviewCount).padStart(2, "0")}</strong>
                  <span className="metric-foot">
                    <span className="live-dot" /> Private previews to review
                  </span>
                </article>
                <article>
                  <span className="metric-label">
                    Provider spend <span>↗</span>
                  </span>
                  <strong>
                    $0<span className="decimal">.00</span>
                  </strong>
                  <span className="metric-foot">
                    Fake providers · no billable calls
                  </span>
                </article>
              </section>
              {workspace === "Control Tower" && (
                <section className="studio-feature">
                  <div className="feature-copy">
                    <span className="eyebrow">LESS FRICTION. MORE STORY.</span>
                    <h2>
                      Every great episode
                      <br />
                      starts with a first step.
                    </h2>
                    <p>
                      Give your local workflow a test run.
                      <br />
                      Your synthetic preview is just a moment away.
                    </p>
                    <button
                      className="text-button"
                      onClick={() => {
                        setCreating(true);
                        createKey.current = null;
                      }}
                    >
                      Create a synthetic episode <span>↗</span>
                    </button>
                  </div>
                  <div className="feature-art" aria-hidden="true">
                    <div className="feature-circle" />
                    <div className="feature-lines" />
                    <div className="feature-mountain-back" />
                    <div className="feature-mountain" />
                    <span className="feature-tag">ORIGINAL BY DESIGN</span>
                    <span className="art-coordinate">FNS—001 / LOCAL</span>
                  </div>
                </section>
              )}
              <div className="content-grid">
                <section className="panel episode-panel">
                  <div className="section-title">
                    <div>
                      <span className="eyebrow">YOUR WORK, IN MOTION</span>
                      <h2>
                        {workspace === "Quality Director"
                          ? "Preview review queue"
                          : "Episode workspace"}
                        <span className="count">
                          {workspace === "Quality Director"
                            ? reviewCount
                            : jobs.length}
                        </span>
                      </h2>
                    </div>
                    <button
                      className="subtle-button"
                      onClick={() => void refresh()}
                      aria-label="Refresh episodes"
                    >
                      ↻
                    </button>
                  </div>
                  <div className="table-tools">
                    <div className="tabs" aria-label="Filter episodes">
                      {[
                        "All episodes",
                        "In progress",
                        "For review",
                        "Stopped",
                      ].map((tab) => (
                        <button
                          key={tab}
                          className={filter === tab ? "selected" : ""}
                          onClick={() => setFilter(tab)}
                        >
                          {tab}
                        </button>
                      ))}
                    </div>
                    <input
                      className="search"
                      aria-label="Search episodes"
                      placeholder="Search episodes…"
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                    />
                  </div>
                  <div className="episode-list">
                    {visible.length === 0 ? (
                      <div className="empty-state">
                        <span className="empty-icon">▤</span>
                        <h3>
                          {jobs.length
                            ? "No episodes match this view."
                            : "Your next story starts here."}
                        </h3>
                        <p>
                          {jobs.length
                            ? "Try another filter or search."
                            : "Create your first synthetic episode to explore the workflow."}
                        </p>
                        {!jobs.length && (
                          <button
                            className="secondary"
                            onClick={() => setCreating(true)}
                          >
                            ＋ Create first episode
                          </button>
                        )}
                      </div>
                    ) : (
                      visible.map((job, index) => (
                        <button
                          key={job.id}
                          className={`episode-row ${selectedId === job.id ? "row-selected" : ""}`}
                          onClick={() => {
                            setSelectedId(job.id);
                            if (workspace === "Control Tower")
                              setWorkspace("Episode Studio");
                          }}
                        >
                          <span
                            className={`episode-cover cover-${index % 3}`}
                            aria-hidden="true"
                          >
                            <span>FNS</span>
                            <i />
                          </span>
                          <span className="episode-name">
                            <strong>{job.title}</strong>
                            <small>
                              Synthetic fixture <span>·</span>{" "}
                              {date(job.created_at)}
                            </small>
                          </span>
                          <span
                            className={`pill state-${job.state.toLowerCase()}`}
                          >
                            {displayState(job.state)}
                          </span>
                          <span className="row-arrow">↗</span>
                        </button>
                      ))
                    )}
                  </div>
                  <div className="panel-footer">
                    <span>
                      <span className="live-dot" /> Saved to your local database
                    </span>
                    <span>
                      {jobs.length} episode{jobs.length === 1 ? "" : "s"}
                    </span>
                  </div>
                </section>
                <aside className="right-column">
                  {selected ? (
                    <section className="panel detail-panel">
                      <div className="section-title">
                        <span className="eyebrow">EPISODE DETAILS</span>
                        <span className="pill neutral">
                          Rev {selected.revision}
                        </span>
                      </div>
                      <h2>{selected.title}</h2>
                      {preview ? (
                        <img
                          className="private-preview"
                          src={preview}
                          alt={`Original synthetic cover preview for ${selected.title}`}
                          onError={() =>
                            setPreviewError(
                              "Preview could not load. Reopen this episode to refresh its signed link.",
                            )
                          }
                        />
                      ) : (
                        <div className="preview-placeholder">
                          {selected.state === "CANCELLED"
                            ? "This job was cancelled."
                            : selected.state === "FAILED"
                              ? "Preview unavailable."
                              : "Your private preview will appear here."}
                        </div>
                      )}
                      {previewError && (
                        <p className="error" role="alert">
                          {previewError}
                        </p>
                      )}
                      <p className="detail-caption">
                        Original synthetic image · not a video export
                      </p>
                      <ol className="stage-list">
                        {stages.map((stage, i) => {
                          const complete =
                            i === 0 || (i < 3 && selected.state === "REVIEW");
                          return (
                            <li key={stage} className={complete ? "done" : ""}>
                              <span>
                                {complete
                                  ? "✓"
                                  : String(i + 1).padStart(2, "0")}
                              </span>
                              {stage}
                              {i === 3 && selected.state === "REVIEW" && (
                                <small>Ready</small>
                              )}
                            </li>
                          );
                        })}
                      </ol>
                      {selected.error && (
                        <p className="error">{selected.error}</p>
                      )}
                      <div className="budget-row">
                        <span>Mock units</span>
                        <strong>
                          {selected.budget.settled_units ?? "—"} /{" "}
                          {selected.budget.reserved_units} reserved
                        </strong>
                      </div>
                      {["QUEUED", "RUNNING"].includes(selected.state) && (
                        <button
                          className="secondary cancel"
                          disabled={busy}
                          onClick={() => void cancel(selected)}
                        >
                          Cancel job
                        </button>
                      )}
                      <details className="provenance">
                        <summary>Provenance & job events</summary>
                        <code>{selected.id}</code>
                        {selected.artifact_sha && (
                          <p>
                            SHA-256 <code>{selected.artifact_sha}</code>
                          </p>
                        )}
                        <ul>
                          {selected.events.map((e) => (
                            <li key={e.id}>
                              {e.kind.replaceAll("_", " ")}
                              <small>{date(e.created_at)}</small>
                            </li>
                          ))}
                        </ul>
                      </details>
                    </section>
                  ) : (
                    <section className="panel next-step">
                      <span className="eyebrow">
                        A LITTLE CREATIVE MOMENTUM
                      </span>
                      <div className="next-icon">↗</div>
                      <h2>
                        Start small.
                        <br />
                        Build something real.
                      </h2>
                      <p>
                        Create a synthetic episode, follow its progress, and
                        inspect the original private preview.
                      </p>
                      <button
                        className="text-button"
                        onClick={() => {
                          setCreating(true);
                          createKey.current = null;
                        }}
                      >
                        Take the first step <span>↗</span>
                      </button>
                    </section>
                  )}
                  <section className="safety-note">
                    <span className="shield">◇</span>
                    <div>
                      <strong>Your studio. Your say.</strong>
                      <p>
                        Publishing is off. No connected channels, external
                        sources, or paid providers.
                      </p>
                    </div>
                  </section>
                </aside>
              </div>
            </>
          )}
          <footer className="workspace-footer">
            <span>Made with intention. Built for your stories.</span>
            <span>
              Flamingo Next Studio <span className="footer-separator">/</span>{" "}
              Local foundation v0.1
            </span>
          </footer>
        </main>
      </div>
      {creating && (
        <div
          className="modal-backdrop"
          onClick={(e) => {
            if (e.target === e.currentTarget && !busy) setCreating(false);
          }}
        >
          <section
            ref={modalRef}
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="new-title"
            onKeyDown={(e) => {
              if (e.key === "Escape" && !busy) setCreating(false);
            }}
          >
            <button
              className="modal-close"
              aria-label="Close new episode"
              onClick={() => setCreating(false)}
              disabled={busy}
            >
              ×
            </button>
            <span className="eyebrow">A FRESH START</span>
            <h2 id="new-title">Your next episode.</h2>
            <p>
              Test the full local job workflow with original synthetic media.
            </p>
            <form onSubmit={create}>
              <label htmlFor="episode-title">Episode title</label>
              <input
                autoFocus
                id="episode-title"
                required
                maxLength={128}
                value={title}
                onChange={(e) => {
                  setTitle(e.target.value);
                  createKey.current = null;
                }}
              />
              <div className="fixture-info">
                <span>◇</span>
                <div>
                  <strong>Original synthetic fixture</strong>
                  <p>
                    No source uploads or external providers. Reserves 2 of 100
                    daily mock units. Real cost: $0.
                  </p>
                </div>
              </div>
              {error && (
                <p className="error" role="alert">
                  {error}
                </p>
              )}
              <button className="primary" disabled={busy || !title.trim()}>
                {busy ? "Adding to the queue…" : "Create synthetic episode"}{" "}
                <span>↗</span>
              </button>
            </form>
          </section>
        </div>
      )}
    </div>
  );
}
