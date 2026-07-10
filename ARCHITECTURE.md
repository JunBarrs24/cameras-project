# Architecture: proyecto-rafa

Video-analytics platform sold as a service. One shared engine: each market (retail, construction, future verticals) is a **configuration profile**. The engine code stays single for every client.

## 1. Deployment model: hybrid edge + cloud

**Decision:** video is processed at the client site on a small box we own and lend (comodato); our central server receives only *events* and runs the product around them.

```
CLIENT SITE (tienda / obra)                    OUR CLOUD
┌─────────────────────────────────┐            ┌──────────────────────────────┐
│  existing cameras / NVR (RTSP)  │            │  API (event ingestion)       │
│        │ LAN, no upload cost    │   events   │  Postgres (events, sites)    │
│  ┌─────▼──────────────────┐     │  JSON +    │  Object storage (snapshots)  │
│  │ EDGE BOX (ours)        │─────┼──snapshot──▶  Rule-driven alerts          │
│  │ ingest→detect→track    │     │  ~KBs      │  (WhatsApp / Telegram)       │
│  │ →zones→rules→buffer    │     │            │  Dashboard + reports         │
│  └────────────────────────┘     │  profiles  │  Fleet mgmt (config, OTA,    │
│  offline-tolerant: buffers      │◀──models───│   health, model distribution)│
│  events locally, syncs later    │            │                              │
└─────────────────────────────────┘            └──────────────────────────────┘
```

### Why not central processing (dumb client streams video to us)

- Bandwidth: 2 to 6 Mbps upstream **per camera**; a 12-camera store needs 30 to 70 Mbps of sustained upload. Typical MX business internet cannot hold it, and a construction site on 4G has no chance.
- Our GPU cost scales linearly with every camera signed.
- An internet outage means total blindness (the edge keeps working offline).
- Privacy: raw video of customers and employees leaving the premises is the worst posture under the LFPDPPP. Events plus snapshots is far easier to defend.

### Why not full edge (everything at the site)

- No multi-site view, hard to update, we would maintain scattered servers, and the offer stops looking like a service subscription.

### Edge hardware

- v0 (development): this MacBook, running the edge stack against one camera.
- v1 (pilots): x86 mini-PC (Intel N100 class, $150 to $250) handles roughly 4 to 8 streams of yolo11n via OpenVINO. Jetson Orin Nano ($250 to $400) when a site needs more streams or heavier models.
- Lent in comodato, preconfigured, plugged into the NVR's switch. Included in the subscription; cost recovered in 1 to 2 months.
- **Pilot rule:** pilots run opportunistically on capable hardware the client already has (fast, zero friction). Paid production always runs on our box, because client-owned PCs get turned off, run other software, and give us no remote access.

## 2. Processing pipeline (identical for every vertical)

```
RTSP streams → ingest → detect → track → zone engine → rule engine → event queue
               (reconnect,  (pluggable  (ByteTrack,  (polygons:    (config-     (local SQLite
                frame        weights per  stable IDs)  entry/exit/   driven)      buffer →
                sampling)    profile)                  dwell)                     uploader)
```

- **ingest**: per-camera capture with automatic reconnection and frame sampling (5 to 10 fps is enough for analytics).
- **detect**: model runner. The profile decides which weights and which classes. Stock yolo11 for retail; fine-tuned PPE weights for construction.
- **track**: ByteTrack (built into ultralytics) gives each person a stable ID, enabling dwell, paths, and unique counting.
- **zone engine**: named polygons per camera ("pasillo-4", "trastienda", "zona-excavacion"). Emits enter/exit/dwell facts. Polygon geometry is site and camera specific (each lens frames a different scene), so it lives in `sites/<site>/zones.yaml`, separate from the vertical profile. The profile references zones by name; the site config gives each name its polygon. Vertices are stored in normalized `[0, 1]` coordinates so a zone survives a stream resolution change (D-010).
- **rule engine**: evaluates profile rules over tracks, zones, and schedule (e.g. "person in `trastienda` between 22:00 and 07:00 raises an alert"). Emits events.
- **event queue**: every event is written to local SQLite first, then uploaded; it survives internet outages and syncs on reconnect.

## 3. Vertical profiles (the only thing that differs per market)

A profile declares: model weights, classes of interest, zones schema, rules, alert routing, report templates. Example shape:

```yaml
# profiles/retail.yaml
model:
  weights: yolo11n.pt          # stock weights, no training needed for retail v1
  classes: [person]
rules:
  - id: after-hours-intrusion
    when: {zone: trastienda, schedule: "22:00-07:00"}
    emit: {type: intrusion, severity: high, alert: whatsapp}
  - id: dwell
    when: {zone: "pasillo-*", dwell_gt_s: 30}
    emit: {type: dwell, severity: info}
reports: [traffic-by-hour, zone-heatmap, dwell-ranking]
```

```yaml
# profiles/construction.yaml
model:
  weights: ppe-v1.pt           # fine-tuned: casco, no-casco, chaleco, arnés
  classes: [person, casco, no-casco, chaleco]
rules:
  - id: no-helmet-in-active-zone
    when: {zone: "zona-activa*", class: no-casco}
    emit: {type: ppe-violation, severity: high, alert: whatsapp, snapshot: true}
reports: [ppe-compliance-daily, attendance-summary]
```

**Discipline rule:** when a client asks for something new, first ask "is this expressible as profile config?" If yes, it goes in the profile. If it needs code, it goes into the shared engine so every vertical benefits. The engine must never fork per client.

## 4. Event schema (the contract between edge and cloud)

Defined once in `shared/` (pydantic), used by both sides:

```
Event { id, site_id, camera_id, ts, type, severity, track_id,
        zone, class, dwell_s?, snapshot_ref?, profile_rule_id }
```

Events are small, immutable facts. Everything the cloud does (alerts, dashboards, reports) is derived from them.

## 5. Data retention

Raw 24/7 video stays on the client's NVR (which already overwrites itself, typically every 15 to 30 days) and is never transferred to us. What we hold, with defaults configurable per contract:

| Data | Default retention |
|---|---|
| Anonymized aggregates (counts, heatmaps) | Indefinite |
| Event metadata (JSON) | 12 months |
| Event snapshots | 30 days, automatic deletion |
| Incident-flagged evidence | Until the client closes the case, 90-day cap |
| Client footage for model training | Only with an explicit contract clause |

Rationale: storage cost is negligible (snapshots are small JPEGs); the driver is exposure. Everything held can be breached or subpoenaed, so short defaults protect both sides, and "snapshots auto-delete in 30 days" is a selling point under the LFPDPPP proportionality principle.

## 6. Repository layout (monorepo)

```
proyecto-rafa/
├── edge/            # runs on the box at the client site
│   ├── ingest/      ├── detect/      ├── track/
│   ├── zones/       ├── rules/       ├── events/
│   └── agent/       # health heartbeat, config sync, updates
├── cloud/           # runs on our server
│   ├── api/         # FastAPI: event ingestion + dashboard API
│   ├── alerts/      # WhatsApp/Telegram dispatch
│   ├── dashboard/   # web UI
│   └── fleet/       # device registry, profile/model distribution
├── shared/          # event schemas, common utils (single source of truth)
├── profiles/        # retail.yaml, construction.yaml, ...
└── models/          # weights registry (stock + fine-tuned)
```

## 7. Roadmap

Each phase has a detailed plan (inputs, steps, files, validation, value) in `docs/plans/`.

- **Phase 0, pipeline on this Mac (now).** Evolve the current script into the edge stack: profile loading, tracking, one zone, rules, events into SQLite. Secrets out of git. Prove the pipeline end to end with one camera. Plan: [docs/plans/PHASE_0.md](docs/plans/PHASE_0.md)
- **Phase 1, first pilot (tienda).** Cloud API + Postgres + minimal dashboard, alerts, retail profile running in a real store. Plan: [docs/plans/PHASE_1.md](docs/plans/PHASE_1.md)
- **Phase 2, productize the edge.** Real mini-PC image, fleet registry, remote config and updates, health monitoring, multi-camera. Plan: [docs/plans/PHASE_2.md](docs/plans/PHASE_2.md)
- **Phase 3, construction profile.** Fine-tune the PPE model (public datasets plus client footage), construction rules and reports, targeting obras that already have power and cameras. Plan: [docs/plans/PHASE_3.md](docs/plans/PHASE_3.md)

## 8. Related documents

- [docs/BIOMETRICS.md](docs/BIOMETRICS.md): why, how, and what is needed to add biometric attendance (postponed until a client pays for it).
