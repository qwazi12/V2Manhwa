"use client";
import { useEffect, useState } from "react";
import { api, type Identity } from "../lib/api";
import type { Episode, Series } from "../lib/studio";
type Bible = {
  revision: number;
  characters: {
    id: string;
    canonical_name: string;
    notes: string;
    aliases: { alias: string; pronunciation: string }[];
  }[];
  facts: { id: string; value: { text: string } }[];
};
export default function SeriesBible({
  series,
  episodes,
  identity,
  onChange,
}: {
  series: Series;
  episodes: Episode[];
  identity: Identity;
  onChange: () => void;
}) {
  const [bible, setBible] = useState<Bible | null>(null);
  const [name, setName] = useState("");
  const [characterId, setCharacterId] = useState("");
  const [aliases, setAliases] = useState("");
  const [pronunciation, setPronunciation] = useState("");
  const [fact, setFact] = useState("");
  const [evidence, setEvidence] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  async function load() {
    setBible(await api<Bible>(`/studio/series/${series.id}/bible`));
  }
  useEffect(() => {
    void load().catch((e) => setError(e.message));
  }, [series.id]);
  async function save(e: React.FormEvent) {
    e.preventDefault();
    if (!bible) return;
    setBusy(true);
    setError("");
    try {
      const result = await api<{ invalidated_production_ids: string[] }>(
        `/studio/series/${series.id}/bible/approve`,
        {
          method: "POST",
          headers: {
            "X-CSRF-Token": identity.csrf,
            "Idempotency-Key": crypto.randomUUID(),
          },
          body: JSON.stringify({
            revision: bible.revision,
            confirmed_source_review: true,
            character: {
              id: characterId || null,
              name,
              aliases: aliases
                .split(",")
                .map((s) => s.trim())
                .filter(Boolean),
              pronunciation,
              evidence_page_id: evidence,
            },
            fact,
          }),
        },
      );
      setNotice(
        `Bible revision approved. ${result.invalidated_production_ids.length} affected episode(s) require renewed script review.`,
      );
      setConfirmed(false);
      await load();
      onChange();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const related = episodes.filter((e) => e.series_id === series.id);
  return (
    <section className="boundary-card series-bible">
      <h3>{series.canonical_title} · Series Bible</h3>
      <p className="help">
        Owner-reviewed identities and facts only. Research observations cannot
        write canon. Name corrections invalidate affected narration and release
        approvals.
      </p>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {notice && <p role="status">{notice}</p>}
      {bible && (
        <>
          <p className="help">Canon revision {bible.revision}</p>
          <div className="bible-characters">
            {bible.characters.map((c) => (
              <button
                className="secondary"
                key={c.id}
                onClick={() => {
                  setCharacterId(c.id);
                  setName(c.canonical_name);
                  setAliases(c.aliases.map((a) => a.alias).join(", "));
                  setPronunciation(c.aliases[0]?.pronunciation || "");
                }}
              >
                {c.canonical_name} · edit identity
              </button>
            ))}
          </div>
          {bible.facts.map((f) => (
            <p key={f.id}>{f.value.text}</p>
          ))}
          <form className="insight-form" onSubmit={save}>
            <label>
              Canonical character name
              <input
                required
                maxLength={100}
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </label>
            <label>
              Aliases
              <input
                value={aliases}
                onChange={(e) => setAliases(e.target.value)}
              />
            </label>
            <label>
              Pronunciation note
              <input
                maxLength={180}
                value={pronunciation}
                onChange={(e) => setPronunciation(e.target.value)}
              />
            </label>
            <label>
              Evidence source page
              <select
                required
                value={evidence}
                onChange={(e) => setEvidence(e.target.value)}
              >
                <option value="">Select exact source</option>
                {related.flatMap((ep) =>
                  ep.pages.map((p) => (
                    <option key={p.id} value={p.id}>
                      {ep.chapter_key} · page {p.order}
                    </option>
                  )),
                )}
              </select>
            </label>
            <label>
              Source-supported fact (optional)
              <input
                maxLength={1000}
                value={fact}
                onChange={(e) => setFact(e.target.value)}
              />
            </label>
            <label className="checkbox">
              <input
                type="checkbox"
                checked={confirmed}
                onChange={(e) => setConfirmed(e.target.checked)}
              />{" "}
              I reviewed the named source page.
            </label>
            <button
              className="primary"
              disabled={busy || !confirmed || !evidence}
            >
              Approve canon revision
            </button>
            <button
              type="button"
              className="secondary"
              onClick={() => {
                setCharacterId("");
                setName("");
                setAliases("");
                setPronunciation("");
              }}
            >
              New character
            </button>
          </form>
        </>
      )}
    </section>
  );
}
