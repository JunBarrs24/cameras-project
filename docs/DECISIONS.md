# Biases, tradeoffs, and decisions

Source of truth for the project's design decisions, the tradeoffs accepted, and the biases behind them.

**Protection rules:**

- Entries are immutable. They are never edited or deleted, only superseded by a new entry that references the old one.
- Agents never add or modify entries on their own. A new decision is proposed inside a change-log entry and appended here only after explicit validation by Juan or the developer.
- Every change-log entry references the decision IDs it applies.

Status values: `validated` (approved by Juan or the developer) or `proposed` (awaiting validation).

---

## D-001: Hybrid edge + cloud deployment

Status: validated (2026-07-09, conversation with Juan)

Decision: video is processed on an edge box at the client site; the cloud receives only events (JSON plus snapshot) and runs the product (DB, dashboard, alerts, fleet).
Tradeoff: hardware logistics per site (a box to prepare, lend, and support) in exchange for viable bandwidth (KBs instead of 30 to 70 Mbps upload), server costs that do not scale per camera, offline tolerance, and a defensible privacy posture (raw video never leaves the premises).
Bias: preference for architectures where the physics (upload arithmetic) decides, ahead of what is comfortable to develop.

## D-002: Retail first, construction second

Status: validated (2026-07-09)

Decision: the first vertical to launch is retail; construction follows on the same engine.
Tradeoff: construction likely has stronger compliance-driven demand, but stores already have cameras, power, and internet, so deployment is software-only. Construction without infrastructure becomes a hardware and logistics business, a bad first business for a small team.
Bias: reachable customer beats attractive market.

## D-003: One engine, vertical profiles

Status: validated (2026-07-09)

Decision: a single pipeline for every client; each vertical is a configuration profile (weights, classes, rules, reports). The engine never forks per client.
Tradeoff: some client requests take longer (they must be expressed as config or built into the shared engine) in exchange for one codebase, and each new vertical costing near-zero marginal engineering.
Bias: resistance to per-client special cases, the known death of shared platforms.

## D-004: Data retention defaults

Status: validated (2026-07-09)

Decision: raw video stays on the client NVR and is never transferred. Defaults: anonymized aggregates indefinite; event metadata 12 months; snapshots 30 days with automatic deletion; incident-flagged evidence until case close with a 90-day cap; training use of client footage only by explicit contract clause. Configurable per contract.
Tradeoff: shorter evidence windows for clients in exchange for reduced breach/subpoena exposure and an easy story under the LFPDPPP proportionality principle.
Bias: hold as little as possible; whatever is held can be leaked.

## D-005: Pilots on client hardware, production on our box

Status: validated (2026-07-09)

Decision: pilots run opportunistically on capable hardware the client already has; paid production always runs on hardware we own and lend (comodato).
Tradeoff: pilot support is worse (machines get turned off, no remote access) in exchange for zero-friction, zero-cost pilots that prove value fast.
Bias: speed to first demonstrated value over operational purity, but only while money is not changing hands.

## D-006: Biometrics postponed, badge plus photo first

Status: validated (2026-07-09)

Decision: no face recognition until a client commits to pay for it. Attendance v1 is badge/QR check-in with a camera snapshot attached. Full analysis in [BIOMETRICS.md](BIOMETRICS.md).
Tradeoff: a less automatic attendance product in exchange for zero sensitive-data obligations (dato personal sensible under the LFPDPPP) and a much faster ship.
Bias: legal surface is a cost like any other; take it only when someone pays for it.

## D-007: Toolchain uv + ruff + pytest + ty

Status: proposed (2026-07-09, awaiting validation)

Decision: uv for environments, ruff for format and lint, pytest for tests, ty as the typechecker.
Tradeoff: ty is young compared to mypy, but it is fast and keeps a single-vendor stack (uv, ruff, ty). Fallback: if ty blocks work with false positives, switch to mypy via a new decision entry.
Bias: fewer moving parts in the toolchain, accepting some immaturity risk.

## D-008: Alerts via Telegram first, WhatsApp when a client requires it

Status: proposed (2026-07-09, awaiting validation)

Decision: Phase 1 alerting ships on Telegram (free bot API, roughly an hour of work). WhatsApp Business API (Meta Cloud API or Twilio) is added when a paying client requires it, since WhatsApp is what MX store owners and supervisors actually use.
Tradeoff: pilot users must install/open Telegram, in exchange for shipping alerts weeks earlier and at zero cost.
Bias: prove the alert loop first; pay for the preferred channel when revenue justifies it.

## D-010: Zone polygons in normalized coordinates

Status: validated (2026-07-09, conversation with the developer)

Decision: zone polygon vertices are stored in normalized [0.0, 1.0] coordinates, as fractions of frame width and height, in `sites/<site>/zones.yaml`. The drawing tool (`scripts/draw_zones.py`) captures pixel clicks and converts them on save, so the installer never handles normalization.
Tradeoff: the yaml is less readable at a glance (0.66 instead of 640) in exchange for zones that survive a stream resolution change. A client NVR reconfigured from 720p to 1080p would otherwise silently shift every zone.
Bias: a silently broken zone is the worst failure mode for a security product, so prefer configuration that fails safe over configuration that reads nicely.

Note: D-009 is reserved for the edge/cloud authentication proposal in change-log 0004, still awaiting validation, so it is not yet recorded here.
