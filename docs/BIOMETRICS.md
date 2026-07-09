# What's needed for biometrics

Status: **postponed.** This document explains why biometrics would be useful, why it carries heavy legal weight, how it works technically, and the full checklist to get there, so that when a client asks, scope and price can be quoted instead of improvised.

"Biometrics" here means face recognition: identifying *who* a person is. The current platform detects presence and movement without identifying anyone, which keeps it outside biometric regulation.

## 1. Why

| Use case | Vertical | Worth it? |
|---|---|---|
| Attendance (asistencia): who arrived, when, and when they left | Construction | Yes. This is the real demand, and obras pay for it. |
| Employee time verification | Retail | Maybe. The POS or checador usually covers it already. |
| Repeat-customer analytics ("this shopper came 3 times") | Retail | No. Recognizing customers without consent is legally indefensible and toxic for reputation. |
| Watchlists (known shoplifters) | Retail | No. This is the highest-risk use of the technology and stays outside our scope. |

Conclusion: the only use case worth building is **worker attendance**, sold to construction clients and applied to their own employees under signed consent.

## 2. Legal weight

Under Mexican data-protection law, biometric data is **dato personal sensible**, the strictest tier. Note: a new LFPDPPP replaced the 2010 law in March 2025 and moved INAI's functions to the Secretaría Anticorrupción y Buen Gobierno; a lawyer must confirm current detail before launch. The obligations:

- **Consentimiento expreso y por escrito** from each worker, revocable, collected at onboarding. General signage does not meet this bar.
- **Aviso de privacidad** naming biometric data explicitly, the purpose (control de asistencia), the retention period, and how to exercise **derechos ARCO** (acceso, rectificación, cancelación, oposición).
- **Reinforced security measures**: encryption at rest and in transit, access control, breach-notification readiness. Biometric templates cannot be rotated after a leak, which makes any breach permanent for the affected person.
- **Roles**: the construction company is the *responsable*; this platform acts as *encargado* (processor). The contract must say so and define the duties of each side.
- Sanctions for mishandling sensitive data are the highest in the law.

Checadores de huella y rostro are common in Mexico, so the path is viable; it simply has to be papered correctly, and the client carries obligations too, which must be handed to them as a kit (see section 4).

## 3. How it works (technical)

Face recognition is a separate pipeline from the detection pipeline:

```
enrollment (once):  photo(s) of worker → face embedding (vector) → gallery DB
runtime:            entry camera → detect face → embedding → match vs gallery
                    → attendance event (who, when, confidence) → cloud
```

Key technical realities:

- **A dedicated entry camera is required.** Ceiling security cameras give steep angles and small faces; recognition needs faces near eye level with roughly 100+ pixels between the eyes and decent lighting. In practice: one camera on a pole or wall at the access point. Obras usually have a single access chokepoint, which helps.
- **Models**: open-source stacks (InsightFace, ArcFace-class embeddings) are accurate and run on the planned edge hardware. Only enrollment is needed; there is no training step.
- **Thresholds and errors**: every match carries a confidence score. The false-accept versus false-reject tradeoff must be tuned, and low-confidence cases must surface for manual confirmation by a supervisor.
- **Anti-spoofing**: workers will try photos on phones. Liveness checks (blink or motion analysis, or depth if the camera supports it) are required for the attendance record to be trusted.
- **Storage**: only embeddings (numeric vectors) are stored, encrypted; enrollment photos are deleted after embedding unless consent covers keeping them. Deletion on worker termination must be automatic (ARCO: cancelación).

## 4. Checklist

**Legal kit (once, with a lawyer; this is the long pole):**
- [ ] Consent form template (per worker, signed, revocable)
- [ ] Aviso de privacidad template naming biometrics, purpose, and retention
- [ ] Responsable/encargado data-processing clauses in the client contract
- [ ] ARCO request procedure (who answers, in what timeframe)
- [ ] Breach-notification runbook
- [ ] Legal review of the 2025 LFPDPPP as it applies to encargados

**Technical:**
- [ ] Dedicated entry camera per site (hardware and mounting spec)
- [ ] Enrollment flow (simple app or web: capture, quality check, embed, store)
- [ ] Recognition service on the edge box (embed, match, liveness)
- [ ] Encrypted gallery DB with automatic deletion on termination
- [ ] Attendance event type and reports (llegadas/salidas, weekly summary)
- [ ] Manual-override flow for failed recognitions

**Operational:**
- [ ] Enrollment session at site onboarding (who runs it, how long it takes)
- [ ] Process for new hires and terminations (client notifies us, or self-serve)
- [ ] Support playbook for "worker not recognized" and "worker revoked consent" (revoked consent requires a manual check-in path)

## 5. Lighter alternative to offer first

**Badge or QR check-in plus photo verification**: the worker scans a QR/NFC badge at entry; the camera attaches a snapshot to the check-in event; a supervisor spot-checks that the face matches the badge. This delivers most of the attendance value with zero biometric data (a photo tied to a voluntary check-in has a much lighter legal posture), needs no enrollment, and ships in a fraction of the time. It also produces the labeled face data that would make a later upgrade to full recognition straightforward, with consent collected from day one.

## 6. Recommendation

1. Ship attendance v1 as badge plus photo verification (section 5).
2. Prepare the legal kit in parallel: it is cheap and slow, so it should start early.
3. Build full face recognition only when a client commits to pay for it. Estimated effort at that point: 3 to 4 weeks of engineering (enrollment app, recognition service, liveness, deletion automation) plus the legal kit.
