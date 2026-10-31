"use client";
import { useEffect, useState } from "react";
import { api, type Identity } from "../lib/api";
import type { Episode } from "../lib/studio";
type Finding = {
  id: string;
  kind: string;
  beat_id: string;
  page_id: string;
  description: string;
  severity: string;
  status: string;
  start_ms: number;
  export_sha: string;
  remediation: string | null;
};
export default function QualityFindings({
  episode,
  kind,
  identity,
  onChange,
  onSeek,
  onInspect,
}: {
  episode: Episode;
  kind: "longform" | "vertical";
  identity: Identity;
  onChange: () => Promise<void>;
  onSeek: (seconds: number) => void;
  onInspect: (pageId: string) => void;
}) {
  const [items, setItems] = useState<Finding[]>([]);
  const [beat, setBeat] = useState(episode.beats[0]?.id || "");
  const [category, setCategory] = useState("story");
  const [severity, setSeverity] = useState("P1");
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    api<Finding[]>(`/studio/episodes/${episode.id}/findings`)
      .then((v) => {
        if (active) setItems(v.filter((f) => f.kind === kind));
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [episode.id, episode.revision, kind]);
  async function send(path: string, body: unknown) {
    await api(path, {
      method: "POST",
      headers: {
        "X-CSRF-Token": identity.csrf,
        "Idempotency-Key": crypto.randomUUID(),
      },
      body: JSON.stringify(body),
    });
    await onChange();
  }
  return (
    <section className="quality-findings">
      <h3>Story, voice & visual findings</h3>
      <p className="help">
        Record a problem against the exact exported beat. Open P0/P1 findings
        block private approval. A new render keeps the finding open until you
        confirm a retest.
      </p>
      {items.map((finding) => (
        <FindingCard
          key={finding.id}
          finding={finding}
          onSeek={onSeek}
          onInspect={onInspect}
          resolve={async (notes) => {
            await send(
              `/studio/episodes/${episode.id}/findings/${finding.id}/resolve`,
              { revision: episode.revision, confirmed_retest: true, notes },
            );
          }}
        />
      ))}
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          setBusy(true);
          setError("");
          try {
            await send(`/studio/episodes/${episode.id}/findings`, {
              revision: episode.revision,
              kind,
              beat_id: beat,
              category,
              severity,
              description,
            });
            setDescription("");
          } catch (err) {
            setError((err as Error).message);
          } finally {
            setBusy(false);
          }
        }}
      >
        <label>
          Exported beat
          <select value={beat} onChange={(e) => setBeat(e.target.value)}>
            {episode.beats.map((b, i) => (
              <option value={b.id} key={b.id}>
                {i + 1}. {b.event}
              </option>
            ))}
          </select>
        </label>
        <div className="finding-fields">
          <label>
            Category
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              {[
                "story",
                "voice",
                "visual",
                "timing",
                "rights",
                "packaging",
              ].map((v) => (
                <option key={v}>{v}</option>
              ))}
            </select>
          </label>
          <label>
            Severity
            <select
              value={severity}
              onChange={(e) => setSeverity(e.target.value)}
            >
              <option value="P0">P0 · critical blocker</option>
              <option value="P1">P1 · approval blocker</option>
              <option value="P2">P2 · improvement</option>
              <option value="P3">P3 · minor</option>
            </select>
          </label>
        </div>
        <label>
          Problem and evidence
          <textarea
            required
            maxLength={2000}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe what the source, narration or shot gets wrong."
          />
        </label>
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
        <button
          className="secondary"
          disabled={busy || !description.trim() || !beat}
        >
          Record finding
        </button>
      </form>
    </section>
  );
}
function FindingCard({
  finding,
  onSeek,
  onInspect,
  resolve,
}: {
  finding: Finding;
  onSeek: (seconds: number) => void;
  onInspect: (pageId: string) => void;
  resolve: (notes: string) => Promise<void>;
}) {
  const [notes, setNotes] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  return (
    <article className={`finding-card ${finding.status}`}>
      <strong>
        {finding.severity} · {finding.status.replaceAll("_", " ")} ·{" "}
        {(finding.start_ms / 1000).toFixed(1)}s
      </strong>
      <p>{finding.description}</p>
      <p className="help">
        Video version {finding.export_sha.slice(0, 12)} · human observation
      </p>
      <div className="action-row">
        <button
          type="button"
          className="subtle-button"
          onClick={() => onSeek(finding.start_ms / 1000)}
        >
          Inspect current video at this time
        </button>
        <button
          type="button"
          className="subtle-button"
          onClick={() => onInspect(finding.page_id)}
        >
          Inspect source page ↗
        </button>
      </div>
      {finding.status === "open" ? (
        <details>
          <summary>Confirm repair after retest</summary>
          <form
            onSubmit={async (e) => {
              e.preventDefault();
              setBusy(true);
              setError("");
              try {
                await resolve(notes);
              } catch (err) {
                setError((err as Error).message);
              } finally {
                setBusy(false);
              }
            }}
          >
            <label>
              Repair / retest evidence
              <textarea
                required
                value={notes}
                maxLength={2000}
                onChange={(e) => setNotes(e.target.value)}
              />
            </label>
            <label className="checkbox">
              <input
                type="checkbox"
                checked={confirmed}
                onChange={(e) => setConfirmed(e.target.checked)}
              />{" "}
              I compared the current video with the source and verified this
              fix.
            </label>
            {error && (
              <p role="alert" className="error">
                {error}
              </p>
            )}
            <button
              className="secondary"
              disabled={busy || !confirmed || !notes.trim()}
            >
              Confirm verified repair
            </button>
          </form>
        </details>
      ) : (
        <p className="help">Retest: {finding.remediation}</p>
      )}
    </article>
  );
}
