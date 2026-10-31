export type Rights = {
  basis: string;
  rightsholder: string;
  evidence: string;
  allow_internal: boolean;
  allow_distribution: boolean;
  expires_at: string | null;
};
export type Page = {
  id: string;
  asset_id: string;
  original_asset_id?: string;
  panel_id: string;
  order: number;
  filename: string;
  text: string;
  kind: string;
  width: number;
  height: number;
};
export type Beat = {
  id: string;
  page_id: string;
  spoken_text: string;
  event: string;
  motion?:
    | "static"
    | "zoom_in"
    | "zoom_out"
    | "pan_left"
    | "pan_right"
    | "scroll_down";
  crop: [number, number, number, number];
};
export type Package = {
  title: string;
  description: string;
  tags: string[];
  title_locked: boolean;
  description_locked: boolean;
  thumbnail_asset_id?: string;
};
export type Shot = {
  beat_id: string;
  page_id: string;
  spoken_text: string;
  start_frame: number;
  end_frame: number;
  voice_seconds: number;
  crop: number[];
};
export type Export = {
  sha256: string;
  duration_seconds: number;
  width: number;
  height: number;
  size_bytes: number;
  manifest: {
    fps: number;
    frames: number;
    shots: Shot[];
    voice_engines: string[];
    voice_cache_hits: number;
  };
};
export type Episode = {
  id: string;
  series_id: string;
  series_title: string;
  chapter_key: string;
  title: string;
  revision: number;
  source_sha: string;
  rights: Rights;
  pages: Page[];
  beats: Beat[];
  analysis?: {
    status: string;
    limitations: string[];
    pages: {
      page_id: string;
      proposed_text: string;
      panels: {
        order: number;
        crop: [number, number, number, number];
        confidence: string;
      }[];
      words: { text: string; confidence: number }[];
    }[];
  };
  script_approval: { input_sha: string } | null;
  status: string;
  export: Export | null;
  vertical_export?: Export | null;
  vertical_qa?: {
    status: string;
    checks: string[];
    limitations: string[];
  } | null;
  rights_id: string;
  qa: { status: string; checks: string[]; limitations: string[] } | null;
  review: { decision: string; notes: string } | null;
  packaging: Package;
  notes: string;
  voice: string;
  created_at: string;
};
export type Series = {
  id: string;
  canonical_title: string;
  aliases: string[];
  original_language?: string;
};
export type RenderJob = {
  id: string;
  production_id: string;
  state: string;
  kind: string;
  attempt: number;
  error: string | null;
  input_sha: string;
};
export type Research = {
  id: string;
  proposed_title: string;
  confidence: string;
  views_per_hour: number | null;
  interval_hours: number | null;
  competition: string;
  demand: string;
  flags: string[];
  methodology: string;
  observations: {
    id: string;
    source_url: string;
    metric_value: string;
    observed_at: string;
    native_id: string;
  }[];
};
export type Metric = {
  production_id: string;
  episode_title: string;
  views: number;
  impressions: number;
  clicks: number;
  ctr: number | null;
  average_view_seconds: number;
  observed_at: string;
  timeline: { seconds: number | null; ratio: number }[];
};

export type PackagingProposal = {
  id: string;
  asset_id: string;
  title: string;
  style: string;
  source_page_id: string;
  source_beat_id: string;
  method: string;
  stale: boolean;
};
