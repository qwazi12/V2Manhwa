"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError, type Identity } from "../lib/api";
import SeriesBible from "./SeriesBible";
import RightsEditor from "./RightsEditor";
import QualityFindings from "./QualityFindings";
import type {
  Episode,
  Beat,
  Series,
  RenderJob,
  Research,
  Metric,
  PackagingProposal,
  Package as EpisodePackage,
} from "../lib/studio";

type Workspace =
  | "Control Tower"
  | "Series Room"
  | "Episode Studio"
  | "Quality Director"
  | "Packaging Studio"
  | "Publishing Desk"
  | "Research Desk"
  | "Audience Intelligence"
  | "Operations";
const tabs: Workspace[] = [
  "Control Tower",
  "Series Room",
  "Episode Studio",
  "Quality Director",
  "Packaging Studio",
  "Publishing Desk",
  "Research Desk",
  "Audience Intelligence",
  "Operations",
];
const icon = ["◈", "▦", "▤", "◎", "◫", "↗", "⌕", "◴", "⚙"];
const date = (v: string) => new Date(v).toLocaleString();
const state = (v: string) => v.replaceAll("_", " ").toLowerCase();
const emptyPackage: EpisodePackage = {
  title: "",
  description: "",
  tags: [],
  title_locked: true,
  description_locked: true,
};

function usePrivateUrl(path: string | null, version = "") {
  const [url, setUrl] = useState("");
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    setUrl("");
    setError("");
    if (!path) return;
    const load = () =>
      api<{ url: string }>(path)
        .then((v) => {
          if (active) setUrl(v.url);
        })
        .catch((e) => {
          if (active) setError(e.message);
        });
    void load();
    const timer = setInterval(() => void load(), 240000);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [path, version]);
  return { url, error };
}
function PrivateImage({ id, alt }: { id: string; alt: string }) {
  const { url, error } = usePrivateUrl(`/studio/assets/${id}/signed-url`);
  return (
    <>
      {url ? (
        <img className="source-image" src={url} alt={alt} />
      ) : (
        <div className="preview-placeholder">
          {error || "Loading private source…"}
        </div>
      )}
    </>
  );
}
function ExportPlayer({
  episode,
  kind = "longform",
  seek,
}: {
  episode: Episode;
  kind?: string;
  seek?: { seconds: number; nonce: number };
}) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const position = useRef(0);
  const playing = useRef(false);
  const version =
    (kind === "vertical" ? episode.vertical_export : episode.export)?.sha256 ||
    "";
  useEffect(() => {
    position.current = 0;
    playing.current = false;
  }, [episode.id, kind, version]);
  const { url, error } = usePrivateUrl(
    `/studio/episodes/${episode.id}/export-url?kind=${kind}`,
    version,
  );
  useEffect(() => {
    if (seek) {
      position.current = seek.seconds;
      if (videoRef.current?.readyState)
        videoRef.current.currentTime = Math.min(
          seek.seconds,
          videoRef.current.duration || seek.seconds,
        );
    }
  }, [seek]);
  const captions = usePrivateUrl(
    `/studio/episodes/${episode.id}/export-url?kind=${kind}&asset=captions`,
    version,
  );
  return (
    <>
      {url ? (
        <video
          className="export-player"
          ref={videoRef}
          key={`${episode.id}-${kind}`}
          onTimeUpdate={(e) => {
            position.current = e.currentTarget.currentTime;
          }}
          onPlay={() => {
            playing.current = true;
          }}
          onPause={(e) => {
            if (e.currentTarget.readyState >= 2) playing.current = false;
          }}
          onEnded={() => {
            playing.current = false;
          }}
          onLoadedMetadata={(e) => {
            if (position.current > 0)
              e.currentTarget.currentTime = position.current;
            if (playing.current) void e.currentTarget.play().catch(() => {});
          }}
          controls
          preload="metadata"
          src={url}
        >
          {captions.url && (
            <track
              default
              kind="captions"
              srcLang="en"
              label="English narration"
              src={captions.url}
            />
          )}
        </video>
      ) : (
        <p className="error">{error || "Loading private film…"}</p>
      )}
    </>
  );
}

export default function ProductionStudio({
  identity,
  onSignOut,
}: {
  identity: Identity;
  onSignOut: () => void;
}) {
  const [workspace, setWorkspace] = useState<Workspace>("Control Tower");
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [series, setSeries] = useState<Series[]>([]);
  const [jobs, setJobs] = useState<RenderJob[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [showImport, setShowImport] = useState(false);
  const [beats, setBeats] = useState<Beat[]>([]);
  const [dirty, setDirty] = useState(false);
  const [notes, setNotes] = useState("");
  const [voice, setVoice] = useState("system-default");
  const [scriptReviewed, setScriptReviewed] = useState(false);
  const [editorTab, setEditorTab] = useState("Source & script");
  const [pageIndex, setPageIndex] = useState(0);
  const [pack, setPack] = useState<EpisodePackage>(emptyPackage);
  const [packageDirty, setPackageDirty] = useState(false);
  const [proposals, setProposals] = useState<PackagingProposal[]>([]);
  const [seekRequest, setSeekRequest] = useState({ seconds: 0, nonce: 0 });
  const [reviewKind, setReviewKind] = useState<"longform" | "vertical">(
    "longform",
  );
  const [reviewNotes, setReviewNotes] = useState("");
  const [watched, setWatched] = useState(false);
  const [rightsChecked, setRightsChecked] = useState(false);
  const [research, setResearch] = useState<Research[]>([]);
  const [metrics, setMetrics] = useState<Metric[]>([]);
  const [history, setHistory] = useState<
    { revision: number; sha256: string; created_at: string }[]
  >([]);
  const [bibleSeries, setBibleSeries] = useState<Series | null>(null);
  const [seriesTitle, setSeriesTitle] = useState("");
  const [aliases, setAliases] = useState("");
  const selected = episodes.find((e) => e.id === selectedId);
  const currentExport =
    reviewKind === "vertical" ? selected?.vertical_export : selected?.export;
  const currentQa =
    reviewKind === "vertical" ? selected?.vertical_qa : selected?.qa;
  const selectedJobs = jobs.filter((j) => j.production_id === selectedId);
  const currentPage = selected?.pages[pageIndex] || selected?.pages[0];
  const active = jobs.filter((j) => ["queued", "running"].includes(j.state));
  const refresh = useCallback(async () => {
    try {
      const [e, s, j] = await Promise.all([
        api<Episode[]>("/studio/episodes"),
        api<Series[]>("/studio/series"),
        api<RenderJob[]>("/studio/render-jobs"),
      ]);
      setEpisodes(e);
      setSeries(s);
      setJobs(j);
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) onSignOut();
      else setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [onSignOut]);
  useEffect(() => {
    void refresh();
    const timer = setInterval(() => void refresh(), 3000);
    return () => clearInterval(timer);
  }, [refresh]);
  useEffect(() => {
    if (!dirty) {
      setBeats(selected?.beats || []);
      setNotes(selected?.notes || "");
      setVoice(selected?.voice || "system-default");
    }
    if (!packageDirty) setPack(selected?.packaging || emptyPackage);
    setScriptReviewed(false);
    setWatched(false);
    setRightsChecked(false);
  }, [selectedId, selected?.revision, dirty, packageDirty, reviewKind]);
  useEffect(() => {
    if (workspace === "Research Desk")
      api<Research[]>("/studio/research")
        .then(setResearch)
        .catch((e) => setError(e.message));
    if (workspace === "Audience Intelligence")
      api<Metric[]>("/studio/analytics")
        .then(setMetrics)
        .catch((e) => setError(e.message));
    if (workspace === "Packaging Studio" && selectedId)
      api<PackagingProposal[]>(
        `/studio/episodes/${selectedId}/packaging-proposals`,
      )
        .then(setProposals)
        .catch((e) => setError(e.message));
    if (selectedId && editorTab === "Versions")
      api<typeof history>(`/studio/episodes/${selectedId}/history`)
        .then(setHistory)
        .catch((e) => setError(e.message));
  }, [workspace, selectedId, selected?.revision, editorTab, notice]);
  const mutate = async <T,>(
    path: string,
    body: unknown = {},
    method = "POST",
  ) =>
    api<T>(path, {
      method,
      headers: {
        "X-CSRF-Token": identity.csrf,
        "Idempotency-Key": crypto.randomUUID(),
      },
      body: JSON.stringify(body),
    });
  async function action(fn: () => Promise<unknown>, message: string) {
    setBusy(true);
    setError("");
    try {
      await fn();
      setNotice(message);
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  function openEpisode(id: string, next: Workspace = "Episode Studio") {
    if (
      (dirty || packageDirty) &&
      !window.confirm("Discard unsaved editing changes?")
    )
      return;
    setDirty(false);
    setPackageDirty(false);
    setSelectedId(id);
    setPageIndex(0);
    setWorkspace(next);
  }
  async function demo() {
    await action(async () => {
      const e = await mutate<Episode>("/studio/demo-episode");
      setSelectedId(e.id);
      setWorkspace("Episode Studio");
    }, "Original chapter imported. Review its source-linked script before rendering.");
  }
  async function saveScript() {
    if (!selected) return;
    await action(async () => {
      await mutate(
        `/studio/episodes/${selected.id}/script`,
        { revision: selected.revision, beats, notes, voice },
        "PUT",
      );
      setDirty(false);
    }, "Script saved as a new revision. Previous media approvals are invalidated.");
  }
  async function signOut() {
    try {
      await api("/auth/logout", {
        method: "POST",
        headers: { "X-CSRF-Token": identity.csrf },
      });
      onSignOut();
    } catch (e) {
      setError((e as Error).message);
    }
  }
  const choose = (name: Workspace) => {
    setWorkspace(name);
    setError("");
    setNotice("");
  };
  const visible = episodes.filter((e) =>
    (e.title + " " + e.series_title)
      .toLowerCase()
      .includes(query.toLowerCase()),
  );
  return (
    <div className="app-shell product-app">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">
            f<span>.</span>
          </span>
          <div>
            flamingo<span className="brand-small">NEXT STUDIO</span>
          </div>
        </div>
        <div className="workspace-label">
          CREATOR WORKSPACE <span>01</span>
        </div>
        <nav aria-label="Studio workspaces">
          {tabs.map((name, i) => (
            <button
              key={name}
              className={`nav-item ${workspace === name ? "active" : ""}`}
              onClick={() => choose(name)}
            >
              <span aria-hidden="true">{icon[i]}</span>
              {name}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="local-card">
            <span className="live-dot" /> Independent & local
            <p>Local narration · publishing off</p>
          </div>
          <button className="profile" onClick={signOut}>
            <span className="avatar">F</span>
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
            <span className="environment">LOCAL PRODUCTION</span>
            <span className="live-dot" />
            Publishing off
            <button className="mobile-signout" onClick={signOut}>
              Sign out
            </button>
          </div>
        </header>
        <main className="workspace-main">
          <div className="page-heading">
            <div>
              <p className="eyebrow">FROM SOURCE TO PRIVATE FILM</p>
              <h1>
                {workspace === "Control Tower"
                  ? "Your next chapter starts here."
                  : workspace}
              </h1>
              <p>
                Source-linked editorial work, offline narration, and a film you
                can inspect.
              </p>
            </div>
            <button className="primary" onClick={() => setShowImport(true)}>
              ＋ Import authorized chapter
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
          {workspace === "Control Tower" && (
            <>
              <section className="metrics">
                <article>
                  <span className="metric-label">Episode library</span>
                  <strong>{episodes.length}</strong>
                  <span className="metric-foot">
                    Persisted source-backed productions
                  </span>
                </article>
                <article>
                  <span className="metric-label">Rendering</span>
                  <strong>{active.length}</strong>
                  <span className="metric-foot">Queued or running locally</span>
                </article>
                <article>
                  <span className="metric-label">Private films</span>
                  <strong>{episodes.filter((e) => e.export).length}</strong>
                  <span className="metric-foot">Actual MP4 exports</span>
                </article>
                <article>
                  <span className="metric-label">Provider spend</span>
                  <strong>
                    $0<span className="decimal">.00</span>
                  </strong>
                  <span className="metric-foot">No paid adapters enabled</span>
                </article>
              </section>
              <section className="studio-feature">
                <div className="feature-copy">
                  <span className="eyebrow">ONE CONNECTED WORKFLOW</span>
                  <h2>
                    Meet the keeper
                    <br />
                    of the last beacon.
                  </h2>
                  <p>
                    An original three-page chapter, ready for source review.
                    <br />
                    Make its first narrated private film with your local voice
                    engine.
                  </p>
                  <button
                    className="text-button"
                    onClick={demo}
                    disabled={busy}
                  >
                    Start original sample episode <span>↗</span>
                  </button>
                </div>
                <div className="feature-art" aria-hidden="true">
                  <div className="feature-circle" />
                  <div className="feature-mountain-back" />
                  <div className="feature-mountain" />
                  <span className="feature-tag">ORIGINAL BY DESIGN</span>
                </div>
              </section>
            </>
          )}
          {[
            "Control Tower",
            "Episode Studio",
            "Quality Director",
            "Packaging Studio",
          ].includes(workspace) && (
            <div className={`production-grid ${selected ? "with-editor" : ""}`}>
              <section className="panel library-panel">
                <div className="section-title">
                  <h2>
                    Episode library{" "}
                    <span className="count">{episodes.length}</span>
                  </h2>
                  <button
                    className="subtle-button"
                    aria-label="Refresh episodes"
                    onClick={() => void refresh()}
                  >
                    ↻
                  </button>
                </div>
                <div className="library-search">
                  <input
                    aria-label="Search episodes"
                    placeholder="Search episodes…"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                  />
                </div>
                {loading ? (
                  <div className="empty-state">Loading your library…</div>
                ) : visible.length === 0 ? (
                  <div className="empty-state">
                    <span className="empty-icon">▤</span>
                    <h3>
                      {episodes.length
                        ? "No matching episodes."
                        : "Bring a chapter to life."}
                    </h3>
                    <p>
                      Import authorized pages or begin with the original sample.
                    </p>
                    <button
                      className="secondary"
                      disabled={busy}
                      onClick={demo}
                    >
                      Start original sample
                    </button>
                  </div>
                ) : (
                  visible.map((e) => (
                    <button
                      key={e.id}
                      className={`episode-row ${e.id === selectedId ? "row-selected" : ""}`}
                      onClick={() =>
                        openEpisode(
                          e.id,
                          workspace === "Quality Director"
                            ? "Quality Director"
                            : workspace === "Packaging Studio"
                              ? "Packaging Studio"
                              : "Episode Studio",
                        )
                      }
                    >
                      <span className="episode-cover">
                        <span>FNS</span>
                        <i />
                      </span>
                      <span className="episode-name">
                        <strong>{e.title}</strong>
                        <small>
                          {e.series_title} · {e.chapter_key}
                        </small>
                      </span>
                      <span
                        className={`pill ${e.export ? "green" : "neutral"}`}
                      >
                        {state(e.status)}
                      </span>
                    </button>
                  ))
                )}
                <div className="panel-footer">
                  <span>Saved locally · source versions preserved</span>
                </div>
              </section>
              {selected && (
                <section className="panel episode-editor">
                  <div className="section-title">
                    <div>
                      <p className="eyebrow">
                        {selected.series_title} / {selected.chapter_key}
                      </p>
                      <h2>{selected.title}</h2>
                    </div>
                    <span className="pill neutral">
                      Revision {selected.revision}
                    </span>
                  </div>
                  <div className="editor-toolbar">
                    {[
                      "Source & script",
                      "Voice & shots",
                      "Video & QA",
                      "Versions",
                    ].map((t) => (
                      <button
                        key={t}
                        className={editorTab === t ? "current" : ""}
                        onClick={() => setEditorTab(t)}
                      >
                        {t}
                      </button>
                    ))}
                    <span className={dirty ? "unsaved" : "saved"}>
                      {dirty ? "Unsaved changes" : "Saved"}
                    </span>
                  </div>
                  {workspace === "Packaging Studio" ? (
                    <div className="editor-body">
                      <h3>The promise your episode makes.</h3>
                      <p className="help">
                        These are owner-authored fields. Automated preparation
                        cannot overwrite a locked field.
                      </p>
                      <label htmlFor="package-title">Episode title</label>
                      <input
                        id="package-title"
                        maxLength={100}
                        value={pack.title}
                        onChange={(e) => {
                          setPack({ ...pack, title: e.target.value });
                          setPackageDirty(true);
                        }}
                      />
                      <label htmlFor="package-description">
                        Episode-specific description
                      </label>
                      <textarea
                        id="package-description"
                        rows={7}
                        value={pack.description}
                        onChange={(e) => {
                          setPack({ ...pack, description: e.target.value });
                          setPackageDirty(true);
                        }}
                      />
                      <label htmlFor="package-tags">
                        Tags, separated by commas
                      </label>
                      <input
                        id="package-tags"
                        value={pack.tags.join(", ")}
                        onChange={(e) => {
                          setPack({
                            ...pack,
                            tags: e.target.value
                              .split(",")
                              .map((t) => t.trim())
                              .filter(Boolean),
                          });
                          setPackageDirty(true);
                        }}
                      />
                      <label className="checkbox">
                        <input
                          type="checkbox"
                          checked={pack.title_locked}
                          onChange={(e) => {
                            setPack({
                              ...pack,
                              title_locked: e.target.checked,
                            });
                            setPackageDirty(true);
                          }}
                        />{" "}
                        Lock owner title
                      </label>
                      <label className="checkbox">
                        <input
                          type="checkbox"
                          checked={pack.description_locked}
                          onChange={(e) => {
                            setPack({
                              ...pack,
                              description_locked: e.target.checked,
                            });
                            setPackageDirty(true);
                          }}
                        />{" "}
                        Lock owner description
                      </label>
                      <button
                        className="primary"
                        disabled={busy}
                        onClick={() =>
                          void action(async () => {
                            await mutate(
                              `/studio/episodes/${selected.id}/package`,
                              {
                                revision: selected.revision,
                                title: pack.title,
                                description: pack.description,
                                tags: pack.tags,
                                title_locked: pack.title_locked,
                                description_locked: pack.description_locked,
                              },
                              "PUT",
                            );
                            setPackageDirty(false);
                          }, "Package saved. The prior release review is invalidated.")
                        }
                      >
                        Save packaging
                      </button>
                      {pack.thumbnail_asset_id && (
                        <figure className="selected-thumbnail">
                          <PrivateImage
                            id={pack.thumbnail_asset_id}
                            alt="Selected source-backed episode thumbnail"
                          />
                          <figcaption>Selected thumbnail · private</figcaption>
                        </figure>
                      )}
                      <h3>Three source-backed concepts</h3>
                      <p className="help">
                        These layouts use the first, middle and final approved
                        story beats. Their titles come from your event labels.
                        Performance is unknown. Apply a concept explicitly to
                        replace the title and thumbnail; your description stays
                        intact.
                      </p>
                      <button
                        className="secondary"
                        disabled={
                          busy || !selected.script_approval || packageDirty
                        }
                        onClick={() =>
                          void action(async () => {
                            await mutate(
                              `/studio/episodes/${selected.id}/packaging-proposals`,
                              { revision: selected.revision },
                            );
                          }, "Three private packaging concepts prepared. Your fields are unchanged until you apply one.")
                        }
                      >
                        Prepare three concepts
                      </button>
                      <div className="packaging-proposals">
                        {proposals.map((proposal) => (
                          <article
                            className="packaging-concept"
                            key={proposal.id}
                          >
                            <PrivateImage
                              id={proposal.asset_id}
                              alt={`${proposal.style}: ${proposal.title}`}
                            />
                            <h4>{proposal.title}</h4>
                            <p className="help">
                              {proposal.style} · source page{" "}
                              {
                                selected.pages.find(
                                  (p) => p.id === proposal.source_page_id,
                                )?.order
                              }{" "}
                              ·{" "}
                              {proposal.stale
                                ? "Outdated after script changes"
                                : proposal.method}
                            </p>
                            <button
                              className="secondary"
                              disabled={busy || proposal.stale || packageDirty}
                              onClick={() =>
                                void action(async () => {
                                  await mutate(
                                    `/studio/episodes/${selected.id}/packaging-proposals/${proposal.id}/apply`,
                                    { revision: selected.revision },
                                  );
                                }, "Selected title and thumbnail applied as a new revision. Review the updated package before release.")
                              }
                            >
                              Apply title & thumbnail
                            </button>
                          </article>
                        ))}
                      </div>
                      <div className="boundary-card">
                        <strong>Social drafts stay private.</strong>
                        <p>
                          Plan a separate vertical variant from the Voice &
                          shots tab, review its real video, then write
                          platform-specific copy. No account is connected.
                        </p>
                      </div>
                    </div>
                  ) : workspace === "Quality Director" ||
                    editorTab === "Video & QA" ? (
                    <div className="editor-body">
                      <label htmlFor="review-format">Export to review</label>
                      <select
                        id="review-format"
                        value={reviewKind}
                        onChange={(e) =>
                          setReviewKind(
                            e.target.value as "longform" | "vertical",
                          )
                        }
                      >
                        <option value="longform">Long-form film</option>
                        <option value="vertical">
                          Vertical film · separate review
                        </option>
                      </select>
                      {currentExport ? (
                        <>
                          <ExportPlayer
                            episode={selected}
                            kind={reviewKind}
                            seek={seekRequest}
                          />
                          <div className="export-facts">
                            <span>
                              {currentExport.width} × {currentExport.height}
                            </span>
                            <span>
                              {currentExport.duration_seconds.toFixed(1)}{" "}
                              seconds
                            </span>
                            <span>
                              {(currentExport.size_bytes / 1e6).toFixed(2)} MB
                            </span>
                          </div>
                          <details className="technical-report">
                            <summary>
                              Technical QA · {currentQa?.status}
                            </summary>
                            <ul>
                              {currentQa?.checks.map((c) => (
                                <li key={c}>✓ {c.replaceAll("_", " ")}</li>
                              ))}
                            </ul>
                            {currentQa?.limitations.map((v) => (
                              <p className="help" key={v}>
                                {v}
                              </p>
                            ))}
                            <code>MP4 SHA-256: {currentExport.sha256}</code>
                          </details>
                          <QualityFindings
                            key={`${selected.id}-${reviewKind}-${currentExport.sha256}`}
                            episode={selected}
                            kind={reviewKind}
                            identity={identity}
                            onChange={refresh}
                            onSeek={(seconds) =>
                              setSeekRequest({ seconds, nonce: Date.now() })
                            }
                            onInspect={(pageId) => {
                              setPageIndex(
                                Math.max(
                                  0,
                                  selected.pages.findIndex(
                                    (p) => p.id === pageId,
                                  ),
                                ),
                              );
                              setWorkspace("Episode Studio");
                              setEditorTab("Source & script");
                            }}
                          />
                          <h3>Watch. Compare. Decide.</h3>
                          <p className="help">
                            Technical checks do not judge factual accuracy,
                            voice performance, or creative quality. Complete
                            your own review against the source.
                          </p>
                          <label className="checkbox">
                            <input
                              type="checkbox"
                              checked={watched}
                              onChange={(e) => setWatched(e.target.checked)}
                            />{" "}
                            I watched and listened to the exact current export.
                          </label>
                          <label className="checkbox">
                            <input
                              type="checkbox"
                              checked={rightsChecked}
                              onChange={(e) =>
                                setRightsChecked(e.target.checked)
                              }
                            />{" "}
                            I checked the source and its rights declaration.
                          </label>
                          <label htmlFor="review-notes">Review notes</label>
                          <textarea
                            id="review-notes"
                            rows={3}
                            value={reviewNotes}
                            onChange={(e) => setReviewNotes(e.target.value)}
                          />
                          <div className="action-row">
                            <button
                              className="primary"
                              disabled={
                                busy ||
                                !watched ||
                                !rightsChecked ||
                                !reviewNotes.trim()
                              }
                              onClick={() =>
                                void action(
                                  () =>
                                    mutate(
                                      `/studio/episodes/${selected.id}/review`,
                                      {
                                        revision: selected.revision,
                                        kind: reviewKind,
                                        confirmed_watched: true,
                                        confirmed_rights: true,
                                        decision: "approve",
                                        notes: reviewNotes,
                                      },
                                    ),
                                  "Private export approved. Publishing remains disabled.",
                                )
                              }
                            >
                              Approve private export
                            </button>
                            <button
                              className="secondary"
                              disabled={
                                busy ||
                                !watched ||
                                !rightsChecked ||
                                !reviewNotes.trim()
                              }
                              onClick={() =>
                                void action(
                                  () =>
                                    mutate(
                                      `/studio/episodes/${selected.id}/review`,
                                      {
                                        revision: selected.revision,
                                        kind: reviewKind,
                                        confirmed_watched: true,
                                        confirmed_rights: true,
                                        decision: "needs_changes",
                                        notes: reviewNotes,
                                      },
                                    ),
                                  "Episode returned for changes.",
                                )
                              }
                            >
                              Request changes
                            </button>
                          </div>
                          <ExportLinks episode={selected} kind={reviewKind} />
                        </>
                      ) : (
                        <div className="empty-state">
                          <h3>No current film yet.</h3>
                          <p>
                            Approve the saved script and render a local MP4
                            first.
                          </p>
                        </div>
                      )}
                    </div>
                  ) : editorTab === "Versions" ? (
                    <div className="editor-body">
                      <h3>Immutable revision history</h3>
                      <p className="help">
                        Changes preserve the previous source and editing
                        snapshots. A new script invalidates dependent media and
                        review.
                      </p>
                      {history.map((h) => (
                        <article className="history-item" key={h.revision}>
                          <strong>Revision {h.revision}</strong>
                          <span>{date(h.created_at)}</span>
                          <code>{h.sha256}</code>
                          <button
                            className="secondary"
                            disabled={busy || h.revision === selected.revision}
                            onClick={() => {
                              if (
                                window.confirm(
                                  `Restore only the script from revision ${h.revision}? Current media approval will be invalidated.`,
                                )
                              )
                                void action(
                                  () =>
                                    mutate(
                                      `/studio/episodes/${selected.id}/restore-script`,
                                      {
                                        revision: selected.revision,
                                        restore_revision: h.revision,
                                      },
                                    ),
                                  "Script restored into a new revision; previous files and packaging are preserved.",
                                );
                            }}
                          >
                            Restore this script
                          </button>
                        </article>
                      ))}
                    </div>
                  ) : editorTab === "Voice & shots" ? (
                    <div className="editor-body">
                      <h3>Local narration</h3>
                      <p className="help">
                        Choose the system voice or a local neural narrator.
                        Neural voices require the pinned files from
                        download-voice-models.command. No paid provider or
                        network fallback is used. Narration is cached by exact
                        text, voice and model version.
                      </p>
                      <label htmlFor="voice-profile">Narrator</label>
                      <select
                        id="voice-profile"
                        value={voice}
                        onChange={(e) => {
                          setVoice(e.target.value);
                          setDirty(true);
                        }}
                      >
                        <option value="system-default">
                          System voice · built in
                        </option>
                        <option value="kokoro-am_michael-v1">
                          Michael · US English · local neural voice
                        </option>
                        <option value="kokoro-bm_george-v1">
                          George · UK English · local neural voice
                        </option>
                        <option value="kokoro-af_heart-v1">
                          Heart · US English · local neural voice
                        </option>
                      </select>
                      <button
                        className="secondary"
                        disabled={busy || !dirty}
                        onClick={() => void saveScript()}
                      >
                        Save voice & shot settings
                      </button>
                      <p className="help">
                        Changing the narrator requires a new saved script
                        approval before rendering.
                      </p>
                      <div className="boundary-card">
                        Source-linked beats: {selected.beats.length} · Script
                        review:{" "}
                        {selected.script_approval ? "current" : "required"} ·
                        Frame rate: 24 fps
                      </div>
                      <div className="action-row">
                        <button
                          className="primary"
                          disabled={busy || !selected.script_approval || dirty}
                          onClick={() =>
                            void action(
                              () =>
                                mutate(
                                  `/studio/episodes/${selected.id}/render`,
                                  { revision: selected.revision },
                                ),
                              "Private film queued. Keep the local render worker running.",
                            )
                          }
                        >
                          Render private film
                        </button>
                        <button
                          className="secondary"
                          disabled={busy || !selected.script_approval || dirty}
                          onClick={() =>
                            void action(
                              () =>
                                mutate(
                                  `/studio/episodes/${selected.id}/render-vertical`,
                                  { revision: selected.revision },
                                ),
                              "Vertical film queued. It must fit 60 seconds and be reviewed separately.",
                            )
                          }
                        >
                          Render vertical preview
                        </button>
                      </div>
                      {selectedJobs.map((j) => (
                        <article key={j.id} className="render-job">
                          <div>
                            <strong>
                              {j.kind} · {j.state}
                            </strong>
                            <small>
                              Attempt {j.attempt} · {j.id}
                            </small>
                            {j.error && <p className="error">{j.error}</p>}
                          </div>
                          {["queued", "running"].includes(j.state) && (
                            <button
                              className="secondary"
                              disabled={busy}
                              onClick={() =>
                                void action(
                                  () =>
                                    mutate(
                                      `/studio/render-jobs/${j.id}/cancel`,
                                    ),
                                  "Render cancelled and fenced from committing an output.",
                                )
                              }
                            >
                              Cancel render
                            </button>
                          )}
                          {["failed", "cancelled"].includes(j.state) &&
                            j.attempt < 3 && (
                              <button
                                className="secondary"
                                disabled={busy}
                                onClick={() =>
                                  void action(
                                    () =>
                                      mutate(
                                        `/studio/render-jobs/${j.id}/retry`,
                                        { revision: selected.revision },
                                      ),
                                    "Stopped job requeued with its original input fingerprint.",
                                  )
                                }
                              >
                                Retry this job
                              </button>
                            )}
                        </article>
                      ))}
                      {selected.vertical_export && (
                        <>
                          <h3>Vertical preview</h3>
                          <ExportPlayer episode={selected} kind="vertical" />
                        </>
                      )}
                      <div className="action-row">
                        <button
                          className="secondary"
                          disabled={busy}
                          onClick={() => {
                            if (
                              window.confirm(
                                "Create a separate owner-requested variant while preserving this production?",
                              )
                            )
                              void action(async () => {
                                const e = await mutate<Episode>(
                                  `/studio/episodes/${selected.id}/variant`,
                                  { revision: selected.revision },
                                );
                                setSelectedId(e.id);
                              }, "Explicit variant created. Prior production and ledger are preserved.");
                          }}
                        >
                          Create separate variant
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="editor-body">
                      <div className="source-script-grid">
                        <div className="source-pane">
                          <div className="page-selector">
                            <label htmlFor="source-page">
                              Original source page
                            </label>
                            <select
                              id="source-page"
                              value={pageIndex}
                              onChange={(e) =>
                                setPageIndex(Number(e.target.value))
                              }
                            >
                              {selected.pages.map((p, i) => (
                                <option key={p.id} value={i}>
                                  Page {p.order} · {p.filename}
                                </option>
                              ))}
                            </select>
                          </div>
                          {currentPage && (
                            <>
                              <PrivateImage
                                id={currentPage.asset_id}
                                alt={`Original page ${currentPage.order} of ${selected.title}`}
                              />
                              <details open>
                                <summary>Owner-transcribed text</summary>
                                <p className="transcript">
                                  {currentPage.text ||
                                    "No transcript supplied. Read and transcribe the original before writing."}
                                </p>
                              </details>
                            </>
                          )}
                          <p className="help">
                            Original uploaded bytes are retained. Local OCR and
                            gutter regions are proposals requiring review.
                          </p>
                          <RightsEditor
                            key={`${selected.id}-${selected.rights_id}`}
                            episode={selected}
                            identity={identity}
                            onChange={refresh}
                          />
                          <button
                            className="secondary"
                            disabled={
                              busy ||
                              selectedJobs.some(
                                (j) =>
                                  j.kind === "analysis" &&
                                  ["queued", "running"].includes(j.state),
                              )
                            }
                            onClick={() =>
                              void action(
                                () =>
                                  mutate(
                                    `/studio/episodes/${selected.id}/analyze-source`,
                                    { revision: selected.revision },
                                  ),
                                "Local OCR and panel proposals queued. Original text and artwork remain unchanged.",
                              )
                            }
                          >
                            Analyze source locally
                          </button>
                          {selected.analysis?.pages.find(
                            (p) => p.page_id === currentPage?.id,
                          ) && (
                            <details className="ocr-results" open>
                              <summary>
                                Unreviewed local OCR & panel proposals
                              </summary>
                              <p className="transcript">
                                {selected.analysis.pages.find(
                                  (p) => p.page_id === currentPage?.id,
                                )?.proposed_text ||
                                  "No readable English text detected."}
                              </p>
                              {selected.analysis.pages
                                .find((p) => p.page_id === currentPage?.id)
                                ?.panels.map((p) => (
                                  <button
                                    key={p.order}
                                    className="secondary"
                                    onClick={() => {
                                      setBeats([
                                        ...beats,
                                        {
                                          id: crypto.randomUUID(),
                                          page_id: currentPage!.id,
                                          spoken_text: "",
                                          event:
                                            "Review this proposed source region",
                                          crop: p.crop,
                                        },
                                      ]);
                                      setDirty(true);
                                    }}
                                  >
                                    Use region {p.order} for a new beat
                                  </button>
                                ))}
                              <p className="help">
                                Heuristic reading order and speaker identity are
                                not verified. Review against the source.
                              </p>
                            </details>
                          )}
                        </div>
                        <div className="script-pane">
                          <div className="action-row">
                            <h3>Source-linked narration</h3>
                            <button
                              className="secondary"
                              onClick={() => {
                                setBeats(
                                  selected.pages
                                    .filter((p) => p.kind === "story")
                                    .map((p) => ({
                                      id: crypto.randomUUID(),
                                      page_id: p.id,
                                      spoken_text:
                                        p.text ||
                                        selected.analysis?.pages.find(
                                          (v) => v.page_id === p.id,
                                        )?.proposed_text ||
                                        "Write source-supported narration here.",
                                      event: `Review the visible event on page ${p.order}`,
                                      crop: [0, 0, 1, 1],
                                    })),
                                );
                                setDirty(true);
                              }}
                            >
                              Draft from transcripts
                            </button>
                          </div>
                          {beats.map((b, i) => (
                            <article className="beat-card" key={b.id}>
                              <div className="beat-heading">
                                <strong>Beat {i + 1}</strong>
                                <button
                                  className="subtle-button"
                                  aria-label={`Remove beat ${i + 1}`}
                                  onClick={() => {
                                    setBeats(
                                      beats.filter((v) => v.id !== b.id),
                                    );
                                    setDirty(true);
                                  }}
                                >
                                  ×
                                </button>
                              </div>
                              <label htmlFor={`beat-source-${b.id}`}>
                                Source page
                              </label>
                              <select
                                id={`beat-source-${b.id}`}
                                value={b.page_id}
                                onChange={(e) => {
                                  setBeats(
                                    beats.map((v) =>
                                      v.id === b.id
                                        ? { ...v, page_id: e.target.value }
                                        : v,
                                    ),
                                  );
                                  setDirty(true);
                                }}
                              >
                                {selected.pages.map((p) => (
                                  <option key={p.id} value={p.id}>
                                    Page {p.order}
                                  </option>
                                ))}
                              </select>
                              <label htmlFor={`beat-event-${b.id}`}>
                                Observed event / evidence
                              </label>
                              <input
                                id={`beat-event-${b.id}`}
                                value={b.event}
                                onChange={(e) => {
                                  setBeats(
                                    beats.map((v) =>
                                      v.id === b.id
                                        ? { ...v, event: e.target.value }
                                        : v,
                                    ),
                                  );
                                  setDirty(true);
                                }}
                              />
                              <label htmlFor={`beat-text-${b.id}`}>
                                Spoken narration
                              </label>
                              <textarea
                                id={`beat-text-${b.id}`}
                                rows={4}
                                value={b.spoken_text}
                                onChange={(e) => {
                                  setBeats(
                                    beats.map((v) =>
                                      v.id === b.id
                                        ? { ...v, spoken_text: e.target.value }
                                        : v,
                                    ),
                                  );
                                  setDirty(true);
                                }}
                              />
                              <label htmlFor={`beat-motion-${b.id}`}>
                                Panel movement
                              </label>
                              <select
                                id={`beat-motion-${b.id}`}
                                value={b.motion || "static"}
                                onChange={(e) => {
                                  setBeats(
                                    beats.map((v) =>
                                      v.id === b.id
                                        ? {
                                            ...v,
                                            motion: e.target
                                              .value as Beat["motion"],
                                          }
                                        : v,
                                    ),
                                  );
                                  setDirty(true);
                                }}
                              >
                                <option value="static">
                                  Hold the source panel
                                </option>
                                <option value="zoom_in">Slow push in</option>
                                <option value="zoom_out">Slow pull out</option>
                                <option value="pan_left">Pan left</option>
                                <option value="pan_right">Pan right</option>
                                <option value="scroll_down">
                                  Scroll down the selected source
                                </option>
                              </select>
                              <details>
                                <summary>
                                  Crop (x, y, width, height · 0–1)
                                </summary>
                                <div className="crop-controls">
                                  {b.crop.map((v, k) => (
                                    <input
                                      key={k}
                                      aria-label={`Beat ${i + 1} crop ${["x", "y", "width", "height"][k]}`}
                                      type="number"
                                      min="0"
                                      max="1"
                                      step="0.05"
                                      value={v}
                                      onChange={(e) => {
                                        const crop = [
                                          ...b.crop,
                                        ] as Beat["crop"];
                                        crop[k] = Number(e.target.value);
                                        setBeats(
                                          beats.map((a) =>
                                            a.id === b.id ? { ...a, crop } : a,
                                          ),
                                        );
                                        setDirty(true);
                                      }}
                                    />
                                  ))}
                                </div>
                              </details>
                              <button
                                className="text-button"
                                onClick={() =>
                                  setPageIndex(
                                    selected.pages.findIndex(
                                      (p) => p.id === b.page_id,
                                    ),
                                  )
                                }
                              >
                                Inspect this source ↗
                              </button>
                            </article>
                          ))}
                          <button
                            className="secondary"
                            onClick={() => {
                              setBeats([
                                ...beats,
                                {
                                  id: crypto.randomUUID(),
                                  page_id: currentPage!.id,
                                  spoken_text: "",
                                  event: "",
                                  crop: [0, 0, 1, 1],
                                },
                              ]);
                              setDirty(true);
                            }}
                          >
                            ＋ Add source-linked beat
                          </button>
                        </div>
                      </div>
                      <label htmlFor="editor-notes">
                        Editorial notes / uncertainty
                      </label>
                      <textarea
                        id="editor-notes"
                        rows={2}
                        value={notes}
                        onChange={(e) => {
                          setNotes(e.target.value);
                          setDirty(true);
                        }}
                      />
                      <div className="action-row">
                        <button
                          className="primary"
                          disabled={busy || !dirty || beats.length === 0}
                          onClick={saveScript}
                        >
                          Save script revision
                        </button>
                        <label className="checkbox">
                          <input
                            type="checkbox"
                            checked={scriptReviewed}
                            onChange={(e) =>
                              setScriptReviewed(e.target.checked)
                            }
                          />{" "}
                          I compared every story page with the saved script.
                        </label>
                        <button
                          className="secondary"
                          disabled={
                            busy ||
                            dirty ||
                            !scriptReviewed ||
                            !selected.beats.length
                          }
                          onClick={() =>
                            void action(
                              () =>
                                mutate(
                                  `/studio/episodes/${selected.id}/approve-script`,
                                  {
                                    revision: selected.revision,
                                    confirmed_source_review: true,
                                  },
                                ),
                              "Script approved for local narration and rendering.",
                            )
                          }
                        >
                          Approve saved script
                        </button>
                      </div>
                      <p className="help">
                        Every story page must have a beat. Approval is bound to
                        the exact source, script and voice revision.
                      </p>
                    </div>
                  )}
                </section>
              )}
            </div>
          )}
          {workspace === "Series Room" && (
            <section className="panel editor-body">
              <h2>Canonical series identities</h2>
              <p className="help">
                Stable UUIDs preserve identity. Matching titles and
                Unicode-normalized aliases never merge unrelated works
                automatically.
              </p>
              <form
                className="inline-form"
                onSubmit={(e) => {
                  e.preventDefault();
                  void action(async () => {
                    await mutate("/studio/series", {
                      title: seriesTitle,
                      language: "en",
                      aliases: aliases
                        .split(",")
                        .map((a) => a.trim())
                        .filter(Boolean),
                    });
                    setSeriesTitle("");
                    setAliases("");
                  }, "Independent series identity created.");
                }}
              >
                <label>
                  Series title
                  <input
                    required
                    value={seriesTitle}
                    onChange={(e) => setSeriesTitle(e.target.value)}
                  />
                </label>
                <label>
                  Aliases, comma separated
                  <input
                    value={aliases}
                    onChange={(e) => setAliases(e.target.value)}
                  />
                </label>
                <button className="primary" disabled={busy}>
                  Create series
                </button>
              </form>
              {bibleSeries && (
                <SeriesBible
                  series={bibleSeries}
                  episodes={episodes}
                  identity={identity}
                  onChange={() => void refresh()}
                />
              )}
              {series.map((s) => (
                <article className="series-card" key={s.id}>
                  <div>
                    <h3>{s.canonical_title}</h3>
                    <p>{s.aliases.join(" · ")}</p>
                    <code>{s.id}</code>
                    <button
                      className="secondary"
                      onClick={() =>
                        setBibleSeries(bibleSeries?.id === s.id ? null : s)
                      }
                    >
                      Open Series Bible
                    </button>
                  </div>
                  <div>
                    {episodes
                      .filter((e) => e.series_id === s.id)
                      .map((e) => (
                        <button
                          className="secondary"
                          key={e.id}
                          onClick={() => openEpisode(e.id)}
                        >
                          {e.chapter_key} ↗
                        </button>
                      ))}
                  </div>
                </article>
              ))}
            </section>
          )}
          {workspace === "Research Desk" && (
            <ResearchDesk
              rows={research}
              busy={busy}
              submit={(body) =>
                action(
                  () => mutate("/studio/research/observations", body),
                  "Research observation saved with its provenance.",
                )
              }
            />
          )}
          {workspace === "Audience Intelligence" && (
            <AnalyticsDesk
              rows={metrics}
              episodes={episodes}
              busy={busy}
              submit={(body) =>
                action(
                  () => mutate("/studio/analytics", body),
                  "Manual metrics saved with their observation time.",
                )
              }
            />
          )}
          {workspace === "Publishing Desk" && (
            <section className="panel editor-body">
              <div className="section-title">
                <h2>Private release desk</h2>
                <span className="pill neutral">Publishing disabled</span>
              </div>
              <div className="boundary-card">
                <strong>No destination is connected.</strong>
                <p>
                  Private approval does not authorize a YouTube upload, public
                  release, account connection, or Drive copy.
                </p>
              </div>
              {episodes
                .filter((e) => e.export)
                .map((e) => (
                  <article className="series-card" key={e.id}>
                    <div>
                      <h3>{e.packaging.title}</h3>
                      <p>
                        {e.review?.decision === "approve"
                          ? "Reviewed for private use"
                          : "Owner review required"}{" "}
                        · Distribution rights:{" "}
                        {e.rights.allow_distribution
                          ? "declared"
                          : "not granted"}
                      </p>
                      <code>{e.export?.sha256}</code>
                    </div>
                    <button
                      className="secondary"
                      onClick={() => openEpisode(e.id, "Quality Director")}
                    >
                      Inspect exact export ↗
                    </button>
                  </article>
                ))}
            </section>
          )}
          {workspace === "Operations" && (
            <section className="operations">
              <article className="panel editor-body">
                <h2>Independent local environment</h2>
                <dl className="settings-list">
                  <div>
                    <dt>Database</dt>
                    <dd>Dedicated PostgreSQL · versioned product records</dd>
                  </div>
                  <div>
                    <dt>Media</dt>
                    <dd>Private hash-addressed MinIO · signed access</dd>
                  </div>
                  <div>
                    <dt>Narration</dt>
                    <dd>Local system speech · exact-text audio cache</dd>
                  </div>
                  <div>
                    <dt>Renderer</dt>
                    <dd>FFmpeg · 24 fps · decoded final QA</dd>
                  </div>
                  <div>
                    <dt>Paid AI / external research</dt>
                    <dd>Disconnected</dd>
                  </div>
                  <div>
                    <dt>Publishing / Drive / autopilot</dt>
                    <dd>Off / Off / Off</dd>
                  </div>
                  <div>
                    <dt>Auth / hosting</dt>
                    <dd>Local owner only · no cloud deployment</dd>
                  </div>
                </dl>
              </article>
              <article className="panel editor-body">
                <h2>Capability boundaries</h2>
                <p className="help">
                  This workflow supports owner-authored scripts and transcripts.
                  Local English OCR and gutter-based panel proposals require
                  human review. Model story interpretation, licensed cloud voice
                  adapters, connected market data, production OIDC and cloud
                  recovery remain disconnected. Technical video QA does not
                  establish semantic accuracy or creative quality.
                </p>
                <h3>Render queue</h3>
                {jobs.slice(0, 20).map((j) => (
                  <p className="help" key={j.id}>
                    {j.kind}: {j.state} · attempt {j.attempt}
                  </p>
                ))}
              </article>
            </section>
          )}
          <footer className="workspace-footer">
            <span>Made with intention. Source reviewed by you.</span>
            <span>Flamingo Next Studio / independent local production</span>
          </footer>
        </main>
      </div>
      {showImport && (
        <ImportDialog
          series={series}
          busy={busy}
          serverError={error}
          close={() => setShowImport(false)}
          submit={async (body) => {
            await action(async () => {
              const record = await mutate<Episode>("/studio/sources", body);
              setSelectedId(record.id);
              setWorkspace("Episode Studio");
              setShowImport(false);
            }, "Authorized source imported. Add and review the source-linked narration next.");
          }}
        />
      )}
    </div>
  );
}

function ExportLinks({
  episode,
  kind = "longform",
}: {
  episode: Episode;
  kind?: string;
}) {
  const [error, setError] = useState("");
  async function download(asset: string) {
    try {
      const response = await api<{ url: string }>(
        `/studio/episodes/${episode.id}/export-url?kind=${kind}&asset=${asset}`,
      );
      const a = document.createElement("a");
      a.href = response.url;
      a.download = `episode-${episode.chapter_key}.${asset === "video" ? "mp4" : asset === "voice" ? "wav" : asset === "captions" ? "vtt" : "json"}`;
      a.click();
    } catch (e) {
      setError((e as Error).message);
    }
  }
  return (
    <div className="export-downloads">
      {["video", "voice", "captions", "manifest"].map((v) => (
        <button key={v} className="secondary" onClick={() => void download(v)}>
          Download {v}
        </button>
      ))}
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
    </div>
  );
}

function ImportDialog({
  series,
  busy,
  serverError,
  close,
  submit,
}: {
  series: Series[];
  busy: boolean;
  serverError: string;
  close: () => void;
  submit: (body: unknown) => Promise<void>;
}) {
  const [selectedSeries, setSelectedSeries] = useState(series[0]?.id || "");
  const [title, setTitle] = useState("");
  const [chapter, setChapter] = useState("");
  const [basis, setBasis] = useState("unknown");
  const [holder, setHolder] = useState("");
  const [evidence, setEvidence] = useState("");
  const [internal, setInternal] = useState(false);
  const [distribution, setDistribution] = useState(false);
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState("");
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    dialog.current?.showModal();
  }, []);
  async function send(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      if (
        files.length === 0 ||
        files.length > 80 ||
        files.some((f) => f.size > 5_000_000) ||
        files.reduce((a, f) => a + f.size, 0) > 32_000_000
      )
        throw new Error(
          "Choose 1–80 PNG/JPEG/WebP pages, up to 5 MB each and 32 MB total.",
        );
      const pages = await Promise.all(
        files.map(async (f, i) => ({
          order: i + 1,
          filename: f.name,
          kind: "story",
          text: "",
          data_base64: await new Promise<string>((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(String(reader.result).split(",")[1]);
            reader.onerror = reject;
            reader.readAsDataURL(f);
          }),
        })),
      );
      await submit({
        series_id: selectedSeries,
        title,
        chapter_key: chapter,
        rights: {
          basis,
          rightsholder: holder,
          evidence,
          allow_internal: internal,
          allow_distribution: distribution,
        },
        pages,
      });
    } catch (e) {
      setError((e as Error).message);
    }
  }
  return (
    <dialog
      ref={dialog}
      className="import-dialog"
      onCancel={(e) => {
        if (busy) e.preventDefault();
        else close();
      }}
    >
      <button
        className="modal-close"
        onClick={close}
        disabled={busy}
        aria-label="Close import"
      >
        ×
      </button>
      <p className="eyebrow">IMMUTABLE SOURCE INGESTION</p>
      <h2>Bring an authorized chapter.</h2>
      <p className="help">
        Use source images you have permission to process. No URL downloading or
        archives are accepted.
      </p>
      <form onSubmit={send}>
        <label htmlFor="import-series">Series</label>
        <select
          required
          id="import-series"
          value={selectedSeries}
          onChange={(e) => setSelectedSeries(e.target.value)}
        >
          <option value="">Choose a series</option>
          {series.map((s) => (
            <option key={s.id} value={s.id}>
              {s.canonical_title}
            </option>
          ))}
        </select>
        {!series.length && (
          <p className="help">
            Create a series in Series Room first, or start the original sample.
          </p>
        )}
        <label htmlFor="import-title">Episode title</label>
        <input
          id="import-title"
          required
          maxLength={160}
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
        <label htmlFor="chapter-key">Chapter key</label>
        <input
          id="chapter-key"
          required
          maxLength={80}
          value={chapter}
          onChange={(e) => setChapter(e.target.value)}
          placeholder="For example, 01 or special-1"
        />
        <label htmlFor="source-files">
          PNG/JPEG/WebP pages, selected in reading order
        </label>
        <input
          id="source-files"
          type="file"
          accept="image/png,image/jpeg,image/webp"
          multiple
          required
          onChange={(e) => setFiles(Array.from(e.target.files || []))}
        />
        <ol className="file-order">
          {files.map((f, i) => (
            <li key={`${f.name}-${i}`}>
              {i + 1}. {f.name}
            </li>
          ))}
        </ol>
        <label htmlFor="rights-basis">Rights basis</label>
        <select
          id="rights-basis"
          value={basis}
          onChange={(e) => setBasis(e.target.value)}
        >
          <option value="unknown">Unknown — processing blocked</option>
          <option value="original">Original work</option>
          <option value="licensed">Licensed permission</option>
          <option value="public_domain">Public domain</option>
          <option value="reviewed_exception">
            Independently reviewed exception
          </option>
        </select>
        <label htmlFor="rightsholder">Rightsholder</label>
        <input
          id="rightsholder"
          required
          value={holder}
          onChange={(e) => setHolder(e.target.value)}
        />
        <label htmlFor="rights-evidence">Permission / evidence notes</label>
        <textarea
          id="rights-evidence"
          required
          rows={3}
          value={evidence}
          onChange={(e) => setEvidence(e.target.value)}
        />
        <label className="checkbox">
          <input
            type="checkbox"
            checked={internal}
            onChange={(e) => setInternal(e.target.checked)}
          />{" "}
          I have permission for internal processing.
        </label>
        <label className="checkbox">
          <input
            type="checkbox"
            checked={distribution}
            onChange={(e) => setDistribution(e.target.checked)}
          />{" "}
          The recorded permission separately allows distribution.
        </label>
        {(error || serverError) && (
          <p className="error" role="alert">
            {error || serverError}
          </p>
        )}
        <button
          className="primary"
          disabled={busy || !internal || basis === "unknown"}
        >
          {busy ? "Importing validated pages…" : "Import source revision"}
        </button>
      </form>
    </dialog>
  );
}

function ResearchDesk({
  rows,
  busy,
  submit,
}: {
  rows: Research[];
  busy: boolean;
  submit: (body: unknown) => Promise<void>;
}) {
  const [title, setTitle] = useState("");
  const [url, setUrl] = useState("");
  const [video, setVideo] = useState("");
  const [views, setViews] = useState("");
  const [observed, setObserved] = useState("");
  return (
    <section className="panel editor-body">
      <h2>Evidence, with its limits visible.</h2>
      <p className="help">
        Enter permitted public observations manually. The app does not fetch
        these URLs. A single lifetime view count is never described as current
        velocity. Confidence stays unverified.
      </p>
      <form
        className="insight-form"
        onSubmit={(e) => {
          e.preventDefault();
          void submit({
            title,
            source_url: url,
            video_id: video,
            views: Number(views),
            observed_at: new Date(observed).toISOString(),
          });
        }}
      >
        <label>
          Candidate / series
          <input
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
        </label>
        <label>
          Public evidence URL
          <input
            type="url"
            required
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />
        </label>
        <label>
          Exact video identifier
          <input
            required
            value={video}
            onChange={(e) => setVideo(e.target.value)}
          />
        </label>
        <label>
          Observed views
          <input
            type="number"
            min="0"
            required
            value={views}
            onChange={(e) => setViews(e.target.value)}
          />
        </label>
        <label>
          Observation time
          <input
            type="datetime-local"
            required
            value={observed}
            onChange={(e) => setObserved(e.target.value)}
          />
        </label>
        <button className="primary" disabled={busy}>
          Save observation
        </button>
      </form>
      {rows.map((r) => (
        <article className="insight-card" key={r.id}>
          <div className="action-row">
            <h3>{r.proposed_title}</h3>
            <span className="pill neutral">{r.confidence}</span>
          </div>
          <p>
            {r.views_per_hour === null
              ? "Current velocity unknown"
              : `${r.views_per_hour} observed views/hour over ${r.interval_hours?.toFixed(2)} hours`}
          </p>
          <p className="help">
            Demand: {r.demand} · Competition: {r.competition}
          </p>
          {r.flags.map((f) => (
            <p className="error" key={f}>
              {f}
            </p>
          ))}
          <details>
            <summary>{r.observations.length} dated observations</summary>
            {r.observations.map((o) => (
              <p className="help" key={o.id}>
                <a href={o.source_url} target="_blank" rel="noreferrer">
                  Source
                </a>{" "}
                · {String(o.metric_value)} views · {date(o.observed_at)}
              </p>
            ))}
            <p className="help">{r.methodology}</p>
          </details>
        </article>
      ))}
    </section>
  );
}
function AnalyticsDesk({
  rows,
  episodes,
  busy,
  submit,
}: {
  rows: Metric[];
  episodes: Episode[];
  busy: boolean;
  submit: (body: unknown) => Promise<void>;
}) {
  const [pid, setPid] = useState("");
  const [observed, setObserved] = useState("");
  const [impressions, setImpressions] = useState("");
  const [clicks, setClicks] = useState("");
  const [views, setViews] = useState("");
  const [average, setAverage] = useState("");
  const [retention, setRetention] = useState("");
  return (
    <section className="panel editor-body">
      <h2>Observed outcomes. Honest attribution.</h2>
      <p className="help">
        Manual first-party metrics only. These figures are owner-supplied, not
        platform-verified. Changes in title and thumbnail together cannot
        establish which caused a result.
      </p>
      <form
        className="insight-form"
        onSubmit={(e) => {
          e.preventDefault();
          void submit({
            production_id: pid,
            observed_at: new Date(observed).toISOString(),
            impressions: Number(impressions),
            clicks: Number(clicks),
            views: Number(views),
            average_view_seconds: Number(average),
            retention: retention
              .split(",")
              .map((s) => s.trim())
              .filter(Boolean)
              .map(Number),
          });
        }}
      >
        <label>
          Episode
          <select required value={pid} onChange={(e) => setPid(e.target.value)}>
            <option value="">Choose an episode</option>
            {episodes.map((e) => (
              <option key={e.id} value={e.id}>
                {e.title}
              </option>
            ))}
          </select>
        </label>
        <label>
          Observed at
          <input
            required
            type="datetime-local"
            value={observed}
            onChange={(e) => setObserved(e.target.value)}
          />
        </label>
        <label>
          Impressions
          <input
            required
            min="0"
            type="number"
            value={impressions}
            onChange={(e) => setImpressions(e.target.value)}
          />
        </label>
        <label>
          Clicks
          <input
            required
            min="0"
            type="number"
            value={clicks}
            onChange={(e) => setClicks(e.target.value)}
          />
        </label>
        <label>
          Views
          <input
            required
            min="0"
            type="number"
            value={views}
            onChange={(e) => setViews(e.target.value)}
          />
        </label>
        <label>
          Average view seconds
          <input
            required
            min="0"
            step="0.1"
            type="number"
            value={average}
            onChange={(e) => setAverage(e.target.value)}
          />
        </label>
        <label>
          Retention ratios (0–1, comma separated)
          <input
            value={retention}
            onChange={(e) => setRetention(e.target.value)}
            placeholder="1, 0.82, 0.65"
          />
        </label>
        <button className="primary" disabled={busy}>
          Save metric snapshot
        </button>
      </form>
      {rows.map((r, i) => (
        <article className="insight-card" key={`${r.production_id}-${i}`}>
          <h3>{r.episode_title}</h3>
          <p>
            {r.views} views · CTR{" "}
            {r.ctr === null ? "unknown" : `${(r.ctr * 100).toFixed(2)}%`} ·{" "}
            {r.average_view_seconds}s average view
          </p>
          <p className="help">
            Observed {date(r.observed_at)} · Owner supplied, unverified
          </p>
          {r.timeline.length > 0 && (
            <div
              className="retention-bars"
              aria-label="Retention ratios across episode timeline"
            >
              {r.timeline.map((p, n) => (
                <div
                  key={n}
                  title={`${p.seconds ?? "Unknown"} seconds: ${(p.ratio * 100).toFixed(1)}%`}
                >
                  <span style={{ height: `${p.ratio * 100}%` }} />
                  <small>{p.seconds ?? "?"}</small>
                </div>
              ))}
            </div>
          )}
        </article>
      ))}
    </section>
  );
}
