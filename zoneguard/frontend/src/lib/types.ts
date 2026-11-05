export type Role = "org_admin" | "site_manager" | "security_reviewer" | "auditor";
export type Severity = "informational" | "review_required" | "high_priority" | "critical_review";
export type Point = [number, number];
export type Window = { days: number[]; start: string; end: string };

export interface Me {
  id: string;
  email: string;
  full_name: string;
  mfa_enabled: boolean;
  memberships: { org_id: string; org_name: string; role: Role }[];
}
export interface Org {
  id: string;
  name: string;
  plan: string;
  timezone: string;
  weapon_detection_mode: string;
  face_covering_mode: string;
  video_retention_days: number;
  detection_retention_days: number;
  event_retention_days: number;
  incident_retention_days: number;
  audit_retention_days: number;
  surveillance_notice_confirmed_at: string | null;
  privacy_contact_email: string;
}
export interface Site { id: string; name: string; address: string; timezone: string; created_at: string }
export interface Camera {
  id: string;
  site_id: string;
  edge_agent_id: string | null;
  name: string;
  location_label: string;
  source_type: "rtsp" | "onvif" | "upload";
  stream_url: string;
  onvif_xaddr: string;
  has_credentials: boolean;
  enabled: boolean;
  status: "unknown" | "online" | "offline" | "degraded";
  last_seen_at: string | null;
  last_error: string;
  health: Record<string, unknown>;
  privacy_masks: Point[][];
  has_snapshot: boolean;
  created_at: string;
}
export interface Zone {
  id: string;
  camera_id: string;
  name: string;
  kind: "area" | "line";
  points: Point[];
  direction: "any" | "a_to_b" | "b_to_a";
  monitoring_schedule: Window[];
  approved_access: Window[];
  enabled: boolean;
}
export interface Rule {
  id: string;
  name: string;
  event_type: string;
  site_id: string | null;
  camera_id: string | null;
  zone_id: string | null;
  schedule: Window[];
  severity: Severity;
  min_confidence: number;
  suppression_seconds: number;
  notify_email: boolean;
  recipient_user_ids: string[];
  enabled: boolean;
}
export interface Video {
  id: string;
  site_id: string;
  camera_id: string;
  original_filename: string;
  size_bytes: number;
  container: string;
  width: number;
  height: number;
  fps: number;
  duration_s: number;
  recorded_at: string;
  created_at: string;
  deleted_at: string | null;
}
export interface Job {
  id: string;
  video_id: string;
  status: "queued" | "running" | "completed" | "failed" | "cancelled";
  progress: number;
  model_name: string;
  model_version: string;
  weapon_mode: string;
  face_covering_mode: string;
  sample_fps: number;
  stats: Record<string, number | string | null>;
  error: string;
  created_at: string;
}
export interface Detection {
  label: string;
  confidence: number;
  bbox: [number, number, number, number];
  category: "person" | "weapon" | "face_covering";
  simulated: boolean;
  track_id?: number;
}
export interface EventRow {
  id: string;
  camera_id: string | null;
  zone_id: string | null;
  source: string;
  event_type: string;
  occurred_at: string;
  offset_s: number | null;
  track_id: number | null;
  confidence: number | null;
  model_name: string;
  model_version: string;
  model_status: string;
  simulated: boolean;
  attributes: Record<string, unknown>;
  rule_outcome: string;
}
export interface Incident {
  id: string;
  reference: string;
  site_id: string;
  camera_id: string | null;
  zone_id: string | null;
  title: string;
  category: string;
  severity: Severity;
  status: "open" | "acknowledged" | "escalated" | "dismissed" | "closed";
  confidence: number | null;
  model_name: string;
  model_version: string;
  simulated: boolean;
  rule_name: string;
  occurred_at: string;
  assigned_to: string | null;
  assigned_to_email: string | null;
  suppressed_count: number;
  resolution_reason: string;
  site_name: string | null;
  camera_name: string | null;
  zone_name: string | null;
  created_at: string;
}
export interface Member { user_id: string; email: string; full_name: string; role: Role; mfa_enabled: boolean }
