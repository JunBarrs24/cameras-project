# Phase 3: construction profile

Goal: bring the second vertical onto the same engine (D-003): a fine-tuned PPE model, construction rules and reports, and attendance v1 without biometrics (D-006), targeting obras that already have power and cameras (D-002).

This plan is written three phases ahead and will be refined when a construction prospect is concrete. Requirements, outcomes, and validation criteria are the commitment.

## Value delivered

The second market unlocks with near-zero platform work, proving the profile architecture. The sellable pitch: "detecta trabajadores sin casco o chaleco en zonas activas y avisa al supervisor por mensaje con foto", plus a daily compliance report and attendance summary.

## Input

- Phases 0 to 2 complete: platform stable, fleet manageable remotely.
- A construction prospect with power and cameras (or willingness to accept our box on their wired site).
- The M3 Max development machine (fine-tuning runs locally via MPS) or a rented cloud GPU for larger runs.

## Required

- Public PPE datasets to bootstrap (Roboflow Universe hosts several, 5k to 15k labeled images with helmet/vest classes).
- A labeling tool (Label Studio or Roboflow) and a labeling budget of client-site images: a few thousand frames captured from the prospect's cameras, since on-site footage is what makes accuracy real.
- Evaluation footage held out from training, from the actual site.

## Steps

### Step 1: dataset assembly

- Collect and normalize public PPE datasets into one training set with the target classes: `person`, `casco`, `no-casco`, `chaleco` (arnés postponed until a client needs work-at-height rules; it is rarer in public data and harder to see on ceiling-angle cameras: declared limitation).
- Capture and label frames from the prospect's cameras; keep a held-out evaluation set from days not used in training.

Files: `models/datasets/` layout and prep scripts (C), labeling guidelines doc (C)
Validation: class balance report; evaluation set verifiably disjoint from training days.

### Step 2: fine-tuning

- Fine-tune `yolo11s` (small, not nano: PPE items are small objects and the accuracy gap matters) starting from pretrained weights. Local runs on the M3 Max via `device="mps"`; a rented GPU (RunPod or Lambda class) if iteration gets slow. Track runs and metrics in the repo.

Files: `models/train/` scripts and configs (C), `models/ppe-v1.pt` artifact (registered, storage decided then)
Validation: mAP@50 per class on the held-out set; the casco/no-casco pair is the one that matters, target proposed at that time with real data (a number invented today would be decoration).

### Step 3: operational evaluation

- Metrics that decide sellability, measured on full days of held-out site footage: violations detected vs missed (recall) and false alerts per day (precision translated to supervisor annoyance). Tune confidence thresholds and rule cooldowns until false alerts per day are low enough that a supervisor keeps the channel unmuted.

Files: `models/eval/` scripts (C), `docs/BENCHMARKS.md` (M)
Validation: a written eval report; the go/no-go threshold decision proposed to DECISIONS.md.

### Step 4: construction profile, rules, reports

- `profiles/construction.yaml`: PPE weights, classes, rules (`no-casco` in `zona-activa*` raises a high-severity alert with snapshot; perimeter entry rules for danger zones).
- Reports: `ppe-compliance-daily` (violations by zone and hour, with snapshots) and `attendance-summary`.
- Platform changes, if any, go into the shared engine (D-003 discipline): this step is expected to be mostly configuration; every line of engine code it forces is a signal to examine.

Files: `profiles/construction.yaml` (C), report templates (C)
Validation: the profile runs on the unchanged engine; rule tests with synthetic tracks.

### Step 5: attendance v1 (no biometrics)

- Badge or QR check-in at the access point with a camera snapshot attached to each check-in event, per D-006 and docs/BIOMETRICS.md section 5. A supervisor spot-checks that faces match badges.

Files: check-in flow (C), attendance report (M)
Validation: a day of check-ins reconciles against the supervisor's manual list.

### Step 6: field pilot on an obra

- Deploy on the prospect's site (their cameras if RTSP-accessible, otherwise our box on their wired network), run 2 to 4 weeks with weekly supervisor reviews, tuning zones and thresholds.

## Phase validation (exit criteria)

1. PPE model meets the eval thresholds set in step 3 on held-out footage from the real site.
2. False alerts per day low enough that the supervisor has not muted the channel by week 2 (asked directly).
3. Daily compliance report generated automatically and used in at least one site safety meeting.
4. Attendance v1 reconciles with manual records within an agreed error margin.
5. Zero forks of the engine: everything vertical-specific lives in the profile and report templates.

## Out of scope

Face-recognition attendance (docs/BIOMETRICS.md gates it on a paying client plus the legal kit), arnés and work-at-height rules, sites without power or connectivity (D-002 keeps them out of scope deliberately).
