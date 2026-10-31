-- Flamingo Next Studio reference PostgreSQL schema v1.0
-- INDEPENDENT NEW DATABASE ONLY. Not a migration of any existing manhwa project.
-- Validate through Alembic migrations and PostgreSQL integration tests before production.
-- PostgreSQL >=16 recommended. All timestamps are UTC timestamptz.
BEGIN;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE app_users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  oidc_subject text NOT NULL UNIQUE,
  email text NOT NULL,
  display_name text NOT NULL DEFAULT '',
  role text NOT NULL CHECK (role IN ('owner','editor','viewer')),
  disabled_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE media_assets (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  bucket text NOT NULL, object_key text NOT NULL,
  sha256 char(64) NOT NULL, size_bytes bigint NOT NULL CHECK (size_bytes >= 0),
  mime_type text NOT NULL, width int, height int, duration_ms bigint,
  stage text NOT NULL CHECK (stage IN ('source','intermediate','final','thumbnail','evidence','backup')),
  visibility text NOT NULL DEFAULT 'private' CHECK (visibility IN ('private','approved_public')),
  rights_scope text NOT NULL DEFAULT 'unresolved',
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (bucket,object_key)
);
CREATE INDEX media_sha_ix ON media_assets(sha256);

CREATE TABLE rights_manifests (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  revision int NOT NULL DEFAULT 1 CHECK (revision > 0),
  rightsholder text, basis text NOT NULL CHECK (basis IN ('original','licensed','public_domain','reviewed_exception','unknown')),
  allowed_actions jsonb NOT NULL DEFAULT '{}'::jsonb,
  allowed_platforms text[] NOT NULL DEFAULT '{}',
  territories text[] NOT NULL DEFAULT '{}',
  evidence_asset_id uuid REFERENCES media_assets(id),
  reviewer_id uuid REFERENCES app_users(id), reviewed_at timestamptz,
  expires_at timestamptz, notes text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE works (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  canonical_title text NOT NULL, original_language text,
  work_kind text NOT NULL DEFAULT 'comic' CHECK (work_kind IN ('comic','novel','animation','other')),
  status text NOT NULL DEFAULT 'candidate' CHECK (status IN ('candidate','verified','active','paused','complete','retired')),
  latest_canon_revision int NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE work_aliases (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  work_id uuid NOT NULL REFERENCES works(id),
  alias text NOT NULL CHECK (length(trim(alias))>0), normalized_alias text NOT NULL CHECK (length(trim(normalized_alias))>0),
  locale text, status text NOT NULL DEFAULT 'candidate' CHECK (status IN ('candidate','verified','rejected','ambiguous')),
  evidence_ref text, created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(work_id,normalized_alias,locale)
);
-- No UNIQUE(normalized_alias) globally. Multiple works may have same alias.
CREATE INDEX work_alias_lookup ON work_aliases(normalized_alias);

CREATE TABLE editions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  work_id uuid NOT NULL REFERENCES works(id),
  format text NOT NULL CHECK (format IN ('webtoon','comic','novel','animation','other')),
  provider text NOT NULL, provider_native_id text,
  language text NOT NULL, title text NOT NULL,
  public_url text, rights_manifest_id uuid REFERENCES rights_manifests(id),
  release_status text NOT NULL DEFAULT 'unknown' CHECK (release_status IN ('unknown','ongoing','hiatus','complete','cancelled')),
  last_checked_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(provider, provider_native_id, language)
);

CREATE TABLE episodes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  edition_id uuid NOT NULL REFERENCES editions(id),
  chapter_key text NOT NULL CHECK (length(trim(chapter_key))>0),
  title text, ordering_value numeric(12,4),
  release_date date, latest_source_revision int NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(edition_id,chapter_key)
);
CREATE TABLE source_revisions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  episode_id uuid NOT NULL REFERENCES episodes(id), revision int NOT NULL CHECK (revision > 0),
  manifest_sha256 char(64) NOT NULL, page_count int NOT NULL CHECK (page_count >= 0),
  status text NOT NULL CHECK (status IN ('imported','inspected','blocked','approved')),
  import_method text NOT NULL, rights_manifest_id uuid NOT NULL REFERENCES rights_manifests(id),
  imported_by uuid REFERENCES app_users(id), imported_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(episode_id,revision), UNIQUE(episode_id,manifest_sha256)
);
CREATE TABLE source_pages (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_revision_id uuid NOT NULL REFERENCES source_revisions(id),
  page_order int NOT NULL CHECK (page_order>0), asset_id uuid NOT NULL REFERENCES media_assets(id),
  page_kind text NOT NULL DEFAULT 'story' CHECK (page_kind IN ('story','cover','credit','advert','divider','unknown')),
  quality_json jsonb NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE(source_revision_id,page_order)
);
CREATE TABLE source_panels (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  page_id uuid NOT NULL REFERENCES source_pages(id),
  panel_order int NOT NULL CHECK (panel_order>0),
  box jsonb NOT NULL, panel_kind text NOT NULL DEFAULT 'art' CHECK (panel_kind IN ('art','bubble_only','credit','decoration','unknown')),
  source_crop_asset_id uuid REFERENCES media_assets(id), evidence_sha256 char(64),
  UNIQUE(page_id,panel_order)
);
CREATE TABLE ocr_lines (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  panel_id uuid NOT NULL REFERENCES source_panels(id),
  line_order int NOT NULL CHECK (line_order>0), raw_text text NOT NULL,
  corrected_text text, language text, bounding_box jsonb,
  classification text NOT NULL CHECK (classification IN ('dialogue','narration','caption','sfx','credits','other')),
  confidence numeric(5,4) CHECK (confidence BETWEEN 0 AND 1),
  speaker_character_id uuid, review_status text NOT NULL DEFAULT 'unreviewed',
  UNIQUE(panel_id,line_order)
);

CREATE TABLE characters (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  work_id uuid NOT NULL REFERENCES works(id), canonical_name text NOT NULL,
  identity_status text NOT NULL DEFAULT 'unreviewed' CHECK (identity_status IN ('unreviewed','approved','disputed')),
  notes text, created_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE ocr_lines ADD CONSTRAINT ocr_speaker_fk FOREIGN KEY (speaker_character_id) REFERENCES characters(id);
CREATE TABLE character_aliases (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  character_id uuid NOT NULL REFERENCES characters(id), alias text NOT NULL,
  locale text, romanization_method text, pronunciation text,
  status text NOT NULL DEFAULT 'candidate', evidence jsonb,
  UNIQUE(character_id,alias,locale)
);
CREATE TABLE canon_revisions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  work_id uuid NOT NULL REFERENCES works(id), revision int NOT NULL CHECK (revision > 0),
  reviewed_by uuid NOT NULL REFERENCES app_users(id), reason text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(work_id,revision)
);
CREATE TABLE canon_claims (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  work_id uuid NOT NULL REFERENCES works(id), revision_id uuid REFERENCES canon_revisions(id),
  subject_character_id uuid REFERENCES characters(id), predicate text NOT NULL,
  value jsonb NOT NULL, truth_class text NOT NULL CHECK (truth_class IN ('source_observation','interpretation','market_hypothesis','approved_canon')),
  status text NOT NULL CHECK (status IN ('proposed','approved','disputed','superseded')),
  valid_from_chapter text, valid_to_chapter text, supersedes_id uuid REFERENCES canon_claims(id),
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE term_dictionary (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  work_id uuid NOT NULL REFERENCES works(id), term text NOT NULL,
  phonetic_hint text, ipa text, locale text, status text NOT NULL DEFAULT 'candidate',
  approved_by uuid REFERENCES app_users(id),
  UNIQUE(work_id,term,locale)
);
CREATE TABLE evidence_refs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  evidence_kind text NOT NULL CHECK (evidence_kind IN ('source_panel','ocr_line','official_page','research_observation','owner_note','other')),
  panel_id uuid REFERENCES source_panels(id), ocr_line_id uuid REFERENCES ocr_lines(id),
  external_url text, external_provider text, source_asset_id uuid REFERENCES media_assets(id),
  source_hash char(64), observed_at timestamptz,
  rights_scope text NOT NULL DEFAULT 'unknown',
  description text, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE canon_claim_evidence (
  claim_id uuid NOT NULL REFERENCES canon_claims(id), evidence_id uuid NOT NULL REFERENCES evidence_refs(id),
  support_type text NOT NULL CHECK (support_type IN ('supports','contradicts','context')),
  PRIMARY KEY(claim_id,evidence_id)
);

CREATE TABLE episode_evidence_revisions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  episode_id uuid NOT NULL REFERENCES episodes(id), source_revision_id uuid NOT NULL REFERENCES source_revisions(id),
  canon_revision_id uuid REFERENCES canon_revisions(id), revision int NOT NULL CHECK(revision>0),
  status text NOT NULL CHECK (status IN ('generating','needs_review','approved','superseded')),
  coverage jsonb NOT NULL DEFAULT '{}'::jsonb, sha256 char(64), created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(episode_id,revision)
);
CREATE TABLE story_scenes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  evidence_revision_id uuid NOT NULL REFERENCES episode_evidence_revisions(id),
  scene_order int NOT NULL, scene_purpose text, summary text,
  source_panel_ids uuid[] NOT NULL DEFAULT '{}',
  UNIQUE(evidence_revision_id,scene_order)
);
CREATE TABLE story_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  evidence_revision_id uuid NOT NULL REFERENCES episode_evidence_revisions(id),
  scene_id uuid NOT NULL REFERENCES story_scenes(id), event_order int NOT NULL,
  description text NOT NULL, actors uuid[] NOT NULL DEFAULT '{}',
  significance text NOT NULL CHECK (significance IN ('critical','major','minor','background')),
  fact_type text NOT NULL CHECK (fact_type IN ('observed','interpreted','owner_approved')),
  uncertainty text, reviewed_by uuid REFERENCES app_users(id),
  UNIQUE(evidence_revision_id,event_order)
);
CREATE TABLE story_event_evidence (
  event_id uuid NOT NULL REFERENCES story_events(id), evidence_id uuid NOT NULL REFERENCES evidence_refs(id),
  relationship text NOT NULL CHECK (relationship IN ('supports','context','disputes')),
  PRIMARY KEY(event_id,evidence_id)
);
CREATE TABLE episode_open_questions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  evidence_revision_id uuid NOT NULL REFERENCES episode_evidence_revisions(id),
  question text NOT NULL, severity text NOT NULL DEFAULT 'P2',
  status text NOT NULL DEFAULT 'open', resolution text,
  resolved_by uuid REFERENCES app_users(id)
);

CREATE TABLE channels (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  platform text NOT NULL, provider_channel_id text NOT NULL,
  display_name text NOT NULL, approved_by uuid REFERENCES app_users(id),
  verified_at timestamptz, status text NOT NULL DEFAULT 'disconnected',
  UNIQUE(platform,provider_channel_id)
);
CREATE TABLE provider_connections (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  provider text NOT NULL, environment text NOT NULL,
  external_account_id text, secret_reference text NOT NULL,
  scopes text[] NOT NULL DEFAULT '{}', status text NOT NULL DEFAULT 'disabled',
  verified_at timestamptz, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE productions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  work_id uuid NOT NULL REFERENCES works(id), channel_id uuid REFERENCES channels(id),
  format text NOT NULL CHECK (format IN ('single','compilation','short','reel','community')),
  variant_of uuid REFERENCES productions(id),
  is_qa_only boolean NOT NULL DEFAULT true,
  owner_requested_remake boolean NOT NULL DEFAULT false,
  status text NOT NULL DEFAULT 'DRAFT',
  source_evidence_revision_id uuid REFERENCES episode_evidence_revisions(id),
  rights_manifest_id uuid REFERENCES rights_manifests(id),
  revision int NOT NULL DEFAULT 1,
  created_by uuid REFERENCES app_users(id),
  created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE production_episodes (
  production_id uuid NOT NULL REFERENCES productions(id), episode_id uuid NOT NULL REFERENCES episodes(id),
  ordinal int NOT NULL CHECK(ordinal>0), start_ms bigint, end_ms bigint,
  PRIMARY KEY (production_id,episode_id), UNIQUE(production_id,ordinal)
);
CREATE TABLE production_revisions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  production_id uuid NOT NULL REFERENCES productions(id), revision int NOT NULL,
  kind text NOT NULL CHECK (kind IN ('outline','script','voice','storyboard','package','other')),
  input_fingerprint char(64) NOT NULL, status text NOT NULL DEFAULT 'draft',
  payload jsonb NOT NULL DEFAULT '{}'::jsonb, created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(production_id,revision,kind)
);
CREATE TABLE script_beats (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  script_revision_id uuid NOT NULL REFERENCES production_revisions(id),
  beat_order int NOT NULL, scene_id uuid REFERENCES story_scenes(id),
  narration_text text NOT NULL, emotion text, pace text,
  event_ids uuid[] NOT NULL DEFAULT '{}', source_line_ids uuid[] NOT NULL DEFAULT '{}',
  text_sha256 char(64) NOT NULL,
  UNIQUE(script_revision_id,beat_order)
);
CREATE TABLE audio_beats (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  script_beat_id uuid NOT NULL REFERENCES script_beats(id),
  asset_id uuid NOT NULL REFERENCES media_assets(id),
  voice_config_sha256 char(64) NOT NULL,
  decoded_duration_ms bigint NOT NULL CHECK(decoded_duration_ms>=0),
  audio_qa_status text NOT NULL DEFAULT 'pending',
  input_fingerprint char(64) NOT NULL,
  UNIQUE(script_beat_id,input_fingerprint)
);
CREATE TABLE storyboard_shots (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  storyboard_revision_id uuid NOT NULL REFERENCES production_revisions(id),
  shot_order int NOT NULL, source_panel_id uuid REFERENCES source_panels(id),
  script_beat_id uuid REFERENCES script_beats(id),
  start_frame bigint NOT NULL, end_frame bigint NOT NULL,
  transform jsonb NOT NULL, motion jsonb NOT NULL DEFAULT '{}'::jsonb,
  purpose text, manually_locked boolean NOT NULL DEFAULT false,
  CHECK(end_frame>start_frame), UNIQUE(storyboard_revision_id,shot_order)
);
CREATE TABLE generated_artifacts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  production_id uuid REFERENCES productions(id), asset_id uuid NOT NULL REFERENCES media_assets(id),
  artifact_kind text NOT NULL, input_fingerprint char(64) NOT NULL,
  model_id text, prompt_version text, renderer_version text,
  schema_version text NOT NULL DEFAULT '1.0', manifest jsonb NOT NULL DEFAULT '{}'::jsonb,
  generation_job_id uuid, validity text NOT NULL DEFAULT 'current'
      CHECK(validity IN ('current','stale','unattested','invalid')),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(artifact_kind,input_fingerprint,asset_id)
);
CREATE TABLE artifact_dependencies (
  parent_artifact_id uuid NOT NULL REFERENCES generated_artifacts(id),
  child_artifact_id uuid NOT NULL REFERENCES generated_artifacts(id),
  dependency_kind text NOT NULL DEFAULT 'hard',
  CHECK(parent_artifact_id<>child_artifact_id),
  PRIMARY KEY(parent_artifact_id,child_artifact_id)
);
CREATE TABLE exports (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  production_id uuid NOT NULL REFERENCES productions(id),
  asset_id uuid NOT NULL REFERENCES media_assets(id),
  export_sha256 char(64) NOT NULL UNIQUE,
  manifest_sha256 char(64) NOT NULL,
  input_fingerprint char(64) NOT NULL,
  video_duration_ms bigint NOT NULL CHECK(video_duration_ms>0),
  status text NOT NULL CHECK(status IN ('candidate','verified','invalid','superseded')),
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE qa_reports (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  production_id uuid NOT NULL REFERENCES productions(id), export_id uuid REFERENCES exports(id),
  report_sha256 char(64), check_version text NOT NULL,
  status text NOT NULL CHECK(status IN ('PASS','FAIL','INCOMPLETE','NOT_APPLICABLE')),
  coverage jsonb NOT NULL DEFAULT '{}'::jsonb,
  evaluator_kind text NOT NULL CHECK(evaluator_kind IN ('deterministic','model','asr','human','mixed')),
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE qa_findings (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  qa_report_id uuid NOT NULL REFERENCES qa_reports(id),
  check_id text NOT NULL, severity text NOT NULL CHECK(severity IN ('P0','P1','P2','P3')),
  status text NOT NULL DEFAULT 'open' CHECK(status IN ('open','fixed_pending_retest','verified_fixed','owner_waived','invalidated')),
  evidence_refs uuid[] NOT NULL DEFAULT '{}',
  start_ms bigint, end_ms bigint, description text NOT NULL,
  remediation text, waiver_reason text, waiver_by uuid REFERENCES app_users(id),
  waiver_at timestamptz, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE packaging_revisions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  production_id uuid NOT NULL REFERENCES productions(id), revision int NOT NULL,
  title text NOT NULL DEFAULT '', description text NOT NULL DEFAULT '',
  tags text[] NOT NULL DEFAULT '{}', hashtags text[] NOT NULL DEFAULT '{}',
  thumbnail_asset_id uuid REFERENCES media_assets(id),
  field_policies jsonb NOT NULL DEFAULT '{}'::jsonb,
  truth_card jsonb NOT NULL DEFAULT '{}'::jsonb,
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','needs_review','approved','superseded')),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(production_id,revision)
);
CREATE TABLE packaging_candidates (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  production_id uuid NOT NULL REFERENCES productions(id),
  candidate_type text NOT NULL CHECK(candidate_type IN ('title','thumbnail','description')),
  concept text NOT NULL, source_event_ids uuid[] NOT NULL DEFAULT '{}',
  estimated_score jsonb, image_asset_id uuid REFERENCES media_assets(id),
  selected_by uuid REFERENCES app_users(id), created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE approvals (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  production_id uuid NOT NULL REFERENCES productions(id), export_id uuid NOT NULL REFERENCES exports(id),
  packaging_revision_id uuid NOT NULL REFERENCES packaging_revisions(id),
  rights_manifest_id uuid NOT NULL REFERENCES rights_manifests(id),
  channel_id uuid NOT NULL REFERENCES channels(id),
  qa_report_id uuid NOT NULL REFERENCES qa_reports(id),
  approval_fingerprint char(64) NOT NULL UNIQUE,
  status text NOT NULL DEFAULT 'current' CHECK(status IN ('current','invalidated','revoked')),
  approved_by uuid NOT NULL REFERENCES app_users(id), approved_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE publication_intents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  production_id uuid NOT NULL REFERENCES productions(id),
  approval_id uuid NOT NULL REFERENCES approvals(id),
  channel_id uuid NOT NULL REFERENCES channels(id),
  idempotency_key text NOT NULL UNIQUE,
  privacy text NOT NULL DEFAULT 'private' CHECK(privacy IN ('private','unlisted','public')),
  publish_at timestamptz,
  status text NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','queued','uploading','UPLOAD_UNVERIFIED','published','failed','cancelled')),
  remote_video_id text, created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(channel_id,remote_video_id)
);
CREATE TABLE upload_attempts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  publication_intent_id uuid NOT NULL REFERENCES publication_intents(id),
  attempt_number int NOT NULL, remote_session_ref text,
  status text NOT NULL CHECK(status IN ('starting','in_progress','unverified','succeeded','failed')),
  started_at timestamptz NOT NULL DEFAULT now(), ended_at timestamptz,
  error_code text, UNIQUE(publication_intent_id,attempt_number)
);
CREATE TABLE content_ledger (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  work_id uuid NOT NULL REFERENCES works(id),
  chapter_key text NOT NULL CHECK(length(trim(chapter_key))>0),
  channel_id uuid NOT NULL REFERENCES channels(id),
  content_type text NOT NULL CHECK(content_type IN ('longform_episode','compilation_coverage','short','reel','community')),
  first_production_id uuid NOT NULL REFERENCES productions(id),
  completed_at timestamptz, published_at timestamptz,
  tombstoned_at timestamptz, owner_override_id uuid REFERENCES app_users(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(work_id,chapter_key,channel_id,content_type)
);
-- Owner-approved remake creates a new production variant; it does not erase this ledger.

-- Permanent automated chapter reservation across all longform coverage formats.
-- Never delete a reservation when the file is archived, merged, failed or removed.
-- Retry the *same production* after failure; only an owner-authorized new variant can supersede it.
CREATE TABLE autopilot_claims (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  work_id uuid NOT NULL REFERENCES works(id),
  chapter_key text NOT NULL CHECK(length(trim(chapter_key))>0),
  channel_id uuid NOT NULL REFERENCES channels(id),
  claimed_for_production_id uuid NOT NULL REFERENCES productions(id),
  claim_state text NOT NULL DEFAULT 'reserved'
    CHECK(claim_state IN ('reserved','in_progress','made','published','blocked','cancelled','owner_superseded')),
  claimed_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(work_id,chapter_key,channel_id)
);
-- Publishing a compilation writes one content_ledger row per covered episode.
-- Auto claim uniqueness prevents a simultaneous single-episode claim for the same chapter.

CREATE TABLE research_candidates (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  work_id uuid REFERENCES works(id), proposed_title text NOT NULL,
  status text NOT NULL DEFAULT 'discovered' CHECK(status IN ('discovered','investigating','needs_evidence','blocked','approved','rejected','watching')),
  discovered_at timestamptz NOT NULL DEFAULT now(),
  reviewed_by uuid REFERENCES app_users(id)
);
CREATE TABLE research_observations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  candidate_id uuid REFERENCES research_candidates(id),
  work_id uuid REFERENCES works(id),
  provider text NOT NULL, native_id text, source_url text NOT NULL,
  observation_type text NOT NULL, metric_name text,
  metric_value numeric, metric_unit text, scope jsonb NOT NULL DEFAULT '{}'::jsonb,
  sample_query text, sample_rank int, sampled_count int, expected_count int,
  published_at timestamptz, observed_at timestamptz NOT NULL,
  evidence_sha256 char(64), confidence text NOT NULL DEFAULT 'unverified',
  retention_until timestamptz,
  UNIQUE(provider,native_id,observation_type,observed_at)
);
CREATE TABLE opportunity_assessments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  candidate_id uuid NOT NULL REFERENCES research_candidates(id),
  demand_supply_score numeric(5,2), momentum_score numeric(5,2),
  feasibility_score numeric(5,2), fit_score numeric(5,2),
  total_score numeric(5,2), confidence text NOT NULL,
  tier text NOT NULL CHECK (tier IN ('A','B','C','BLOCKED','UNVERIFIED')),
  rationale jsonb NOT NULL, evidence_ids uuid[] NOT NULL DEFAULT '{}',
  calculated_at timestamptz NOT NULL DEFAULT now(), model_version text NOT NULL
);
CREATE TABLE analytics_observations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  channel_id uuid NOT NULL REFERENCES channels(id),
  publication_intent_id uuid REFERENCES publication_intents(id),
  provider text NOT NULL, metric_name text NOT NULL, value numeric NOT NULL,
  unit text, dims jsonb NOT NULL DEFAULT '{}'::jsonb,
  period_start timestamptz NOT NULL, period_end timestamptz NOT NULL,
  observed_at timestamptz NOT NULL DEFAULT now(),
  CHECK(period_end>=period_start)
);

CREATE TABLE budgets (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  scope_type text NOT NULL, scope_id uuid,
  budget_usd numeric(12,4) NOT NULL CHECK(budget_usd>=0),
  period text NOT NULL CHECK(period IN ('job','day','month')),
  enabled boolean NOT NULL DEFAULT true, updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE usage_reservations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  budget_id uuid NOT NULL REFERENCES budgets(id),
  entity_id uuid NOT NULL, provider text NOT NULL, operation text NOT NULL,
  estimated_usd numeric(12,6) NOT NULL CHECK(estimated_usd>=0),
  actual_usd numeric(12,6) CHECK(actual_usd>=0),
  status text NOT NULL CHECK(status IN ('reserved','charged','released','unverified')),
  created_at timestamptz NOT NULL DEFAULT now(), settled_at timestamptz
);
CREATE TABLE jobs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  job_type text NOT NULL, entity_id uuid NOT NULL,
  state text NOT NULL DEFAULT 'queued' CHECK (state IN ('queued','leased','running','blocked','paused','retryable','failed','completed','cancelled')),
  priority int NOT NULL DEFAULT 0,
  idempotency_key text NOT NULL UNIQUE,
  input_fingerprint char(64),
  lease_owner text, lease_until timestamptz, heartbeat_at timestamptz,
  attempt int NOT NULL DEFAULT 0, max_attempts int NOT NULL DEFAULT 2,
  run_after timestamptz NOT NULL DEFAULT now(), cancel_requested boolean NOT NULL DEFAULT false,
  usage_reservation_id uuid REFERENCES usage_reservations(id),
  result_artifact_id uuid REFERENCES generated_artifacts(id),
  error_code text, error_detail jsonb,
  created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX jobs_claim_idx ON jobs(priority DESC,run_after,created_at)
  WHERE state IN ('queued','retryable');
CREATE TABLE job_attempts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id uuid NOT NULL REFERENCES jobs(id), attempt int NOT NULL,
  worker_id text NOT NULL, started_at timestamptz NOT NULL DEFAULT now(),
  ended_at timestamptz, state text NOT NULL, result jsonb,
  UNIQUE(job_id,attempt)
);
CREATE TABLE outbox_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  event_type text NOT NULL, schema_version int NOT NULL DEFAULT 1,
  entity_id uuid NOT NULL, entity_revision int,
  correlation_id uuid, causation_id uuid,
  payload jsonb NOT NULL, delivered_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX outbox_undelivered ON outbox_events(created_at) WHERE delivered_at IS NULL;
CREATE TABLE event_consumer_receipts (
  event_id uuid NOT NULL REFERENCES outbox_events(id), consumer_name text NOT NULL,
  processed_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(event_id,consumer_name)
);
CREATE TABLE audit_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  actor_id uuid REFERENCES app_users(id), action text NOT NULL,
  entity_type text NOT NULL, entity_id uuid,
  before_hash char(64), after_hash char(64),
  context jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE feature_flags (
  name text PRIMARY KEY, enabled boolean NOT NULL DEFAULT false,
  environment text NOT NULL, changed_by uuid REFERENCES app_users(id),
  changed_at timestamptz NOT NULL DEFAULT now()
);

COMMIT;

-- NOTE: migrations should add validated cross-record triggers/service transactions for:
--   - approvals exact-export/package/QA/rights/channel freshness
--   - releases only when publishing enabled and approved
--   - work/edition/episode ID consistent across related FK records
--   - append-only event/ledger and source revision policy
--   - cost reservation atomicity and actual provider spend reconciliation
--   - auto claims enforced by UNIQUE content_ledger + transaction
-- Privileged service accounts should not bypass these business invariants.
