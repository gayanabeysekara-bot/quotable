# Detector Evaluation Framework

Measure the detectors on **your own staged, consented footage** before relying on them.
No accuracy figures are published with ZoneGuard AI. The only numbers produced so far are
latency/resource measurements, because no ground-truth annotations exist yet.

## Metrics

| Metric | Where it comes from |
|---|---|
| Precision, recall, F1, false positives, false negatives (per box, IoU ≥ 0.5) | `python -m evaluation.run --annotations …` |
| Zone-entry event precision/recall (time tolerance) | same, when `zone_entries` are annotated |
| Detection latency p50/p95, throughput, CPU %, peak RSS | `evaluation.run` (always) and analysis job stats in the dashboard |
| False alerts per camera per day | Dashboard → Evaluation, from incidents dismissed as `false_positive` |
| Alert delivery latency | Dashboard → Evaluation (notification created → sent) |
| Camera reconnect success | Dashboard → Evaluation (edge heartbeat counters) |

## Running

```bash
# from zoneguard/ with the backend virtualenv active
python -m evaluation.run --video staged/after_hours_entry_01.mp4 \
       --annotations evaluation/annotations/after_hours_entry_01.json \
       --model yolox_tiny --sample-fps 5 --label "Site A staged set v1 (consented)"
# reports land in evaluation/reports/*.json and *.md
```

To show a run in the dashboard, POST the JSON report's metrics to
`/api/orgs/{org_id}/evaluations` (name, model_name, model_version, dataset_label, metrics).

## Annotation format

```json
{
  "dataset_label": "Site A staged set v1 (consented, 2026-11)",
  "scenario": "after_hours_entry",
  "frames": [
    {"t": 0.0, "boxes": []},
    {"t": 0.2, "boxes": [[0.41, 0.22, 0.52, 0.81]]}
  ],
  "zones": [{"id": "finance", "name": "Finance Office", "points": [[0.5,0.4],[1,0.4],[1,1],[0.5,1]]}],
  "zone_entries": [3.4],
  "event_tolerance_s": 2.0
}
```

* `t` = seconds from video start; boxes are normalised `[x1, y1, x2, y2]`, one per visible person.
* Annotate at the same sampling rate you evaluate at (e.g. every 0.2 s for 5 fps).
* Use any labelling tool that exports boxes (e.g. CVAT, which is MIT-licensed) and convert.

## Staged footage plan (record with written participant consent)

| # | Scenario | What to capture | What it tests |
|---|---|---|---|
| 1 | Normal office entry | Staff entering a zone during approved hours | No incident (approved access); detection recall |
| 2 | After-hours entry | Same entry outside hours (set `recorded_at`) | Incident + email |
| 3 | Walking past a restricted zone | People passing close to but not into the zone | Zone false positives (feet-anchor accuracy) |
| 4 | Partial occlusion | People behind desks/doors/other people | Recall under occlusion; track fragmentation |
| 5 | Poor lighting | Dim office, backlit doorway, IR night mode | Recall/precision at night |
| 6 | Harmless lookalikes | Phones, umbrellas, tools, toy objects, kitchen utensils | Weapon-module false positives |
| 7 | Visible staged prohibited objects | Prop/training knives & replica firearms, safely staged and pre-announced | Weapon-module recall (only meaningful with a trained model) |
| 8 | Face coverings | Medical masks, scarves, helmets, balaclava (props, consenting actors) | Face-covering module; confirm no severity escalation |
| 9 | Diversity & accessibility | Different clothing, body types, wheelchairs, prams, children (only with guardian consent where lawful) | Disparate error rates |
| 10 | Camera faults | Lens covered, camera unplugged, network dropped | Obstruction & offline alerts, reconnect |

Rules: never use real school CCTV without explicit written approval; store staged footage under the same
retention controls; don't put annotated datasets in this repository.

## Recorded results so far

| Date | Footage | Model | Ground truth | Result |
|---|---|---|---|---|
| 2026-11-05 | OpenCV `vtest.avi` (768×576, 79.5 s, pedestrians; dev-only clip) | yolox_tiny @ 5 fps, conf 0.35, 4 vCPU sandbox | **None** | p50 22.3 ms / p95 27.9 ms per frame, 41 frames/s, peak RSS 161 MB. Precision/recall **not measured**. |
