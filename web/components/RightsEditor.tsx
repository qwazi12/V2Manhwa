"use client";
import { useState } from "react";
import { api, type Identity } from "../lib/api";
import type { Episode } from "../lib/studio";

export default function RightsEditor({
  episode,
  identity,
  onChange,
}: {
  episode: Episode;
  identity: Identity;
  onChange: () => Promise<void>;
}) {
  const [rights, setRights] = useState(episode.rights);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  return (
    <details className="rights-editor">
      <summary>Review or revise source permission</summary>
      <p className="help">
        A new declaration preserves the previous record and invalidates
        approvals for all variants using it. Public availability does not set a
        rights basis.
      </p>
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          setBusy(true);
          setError("");
          try {
            await api(`/studio/episodes/${episode.id}/rights`, {
              method: "PUT",
              headers: {
                "X-CSRF-Token": identity.csrf,
                "Idempotency-Key": crypto.randomUUID(),
              },
              body: JSON.stringify({ revision: episode.revision, rights }),
            });
            await onChange();
          } catch (err) {
            setError((err as Error).message);
          } finally {
            setBusy(false);
          }
        }}
      >
        <label>
          Rights basis
          <select
            value={rights.basis}
            onChange={(e) => setRights({ ...rights, basis: e.target.value })}
          >
            <option value="unknown">Unknown · generation blocked</option>
            <option value="original">Original work</option>
            <option value="licensed">Licensed</option>
            <option value="public_domain">Public domain</option>
            <option value="reviewed_exception">Reviewed exception</option>
          </select>
        </label>
        <label>
          Rightsholder
          <input
            required
            value={rights.rightsholder}
            maxLength={200}
            onChange={(e) =>
              setRights({ ...rights, rightsholder: e.target.value })
            }
          />
        </label>
        <label>
          Evidence / permission notes
          <textarea
            required
            value={rights.evidence}
            maxLength={2000}
            onChange={(e) => setRights({ ...rights, evidence: e.target.value })}
          />
        </label>
        <label>
          Expiry (UTC)
          <input
            type="datetime-local"
            value={rights.expires_at?.slice(0, 16) || ""}
            onChange={(e) =>
              setRights({
                ...rights,
                expires_at: e.target.value ? `${e.target.value}:00Z` : null,
              })
            }
          />
        </label>
        <label className="checkbox">
          <input
            type="checkbox"
            checked={rights.allow_internal}
            onChange={(e) =>
              setRights({ ...rights, allow_internal: e.target.checked })
            }
          />{" "}
          Internal processing permitted
        </label>
        <label className="checkbox">
          <input
            type="checkbox"
            checked={rights.allow_distribution}
            onChange={(e) =>
              setRights({ ...rights, allow_distribution: e.target.checked })
            }
          />{" "}
          Distribution permitted by this declaration
        </label>
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
        <button className="secondary" disabled={busy}>
          Save new rights declaration
        </button>
      </form>
    </details>
  );
}
