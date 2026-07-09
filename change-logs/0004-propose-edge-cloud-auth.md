# 0004: Propose edge/cloud authentication (D-009)

Date: 2026-07-09
Author: agent session (Juan directing)

This entry proposes a new decision. It does not modify `docs/DECISIONS.md`. The
text below enters that file as D-009 only after explicit validation from Juan or
the developer.

## What changed

No code. This is a design proposal, recorded so the edge/cloud contract has a
stated auth model before Phase 1 builds the ingestion API.

## Context and problem

The edge box (D-001) runs at the client site, buffers events locally, and
uploads them to one shared cloud ingestion API. The box is physically reachable
at the client premises, so any secret it holds can be extracted. The API is
internet-facing. Threats to defend:

- Forged or spam events from random internet actors, and denial of service.
- A lost or stolen box whose credentials leak.
- A client trying to write events for, or read data of, another site.
- Replay of captured requests.

The asset is event integrity (a forged intrusion event raises a false alert; a
suppressed real one is worse) and isolation between clients. The box only makes
outbound calls (it sits behind the client NAT), so the exposed surface is the
API.

## Proposed decision (D-009)

Phase the mechanism to the risk, consistent with D-005 and D-008 (ship a simple
safe version, harden when revenue justifies it).

**Phase 1 (first pilot):**

1. TLS on every call. The API terminates HTTPS and refuses plaintext.
2. Per-device bearer API key: each box is provisioned with a unique
   high-entropy key (256-bit random, never shared between boxes), sent as a
   bearer token over TLS. The server stores only a hash, mapped to
   `device -> site_id -> allowed camera_ids -> status(active|revoked)`.
3. Server-side authorization: the site and cameras come from the authenticated
   device, and the API rejects any event whose `site_id`/`camera_id` fall
   outside that device's scope. A valid box for one store cannot write for
   another.
4. Idempotent upsert on the client-generated `event.id` (UUID), so
   offline-buffered retries do not duplicate and replaying an old event is a
   no-op.
5. Per-device rate limiting to blunt spam and denial of service.
6. Revocation and rotation through the fleet channel: a lost box or a churned
   client is cut off by flipping its status; keys rotate by pushing a new one.

**Phase 2 (productized fleet), when scale justifies the operational weight:**

- Exchange the long-lived key for short-lived tokens (the box presents its key
  to a token endpoint and receives a roughly 15-minute JWT the API verifies
  statelessly), shrinking the exposure window of a leaked key. Consider mTLS
  with our own CA if the fleet grows enough to warrant cert infrastructure.
- Optionally sign each event or batch with a per-device ed25519 key at
  creation. The server stores only the public key, so a full server-database
  leak still cannot forge events, and the fact is verifiable end to end. The
  signature travels in the upload envelope, not inside the `Event`.
- Hardware-backed key storage (TPM on the mini-PC) so a stolen box does not
  yield an extractable key.

## Tradeoff and residual risk

The Phase 1 bearer key is a static secret on a physically reachable box. A
stolen pilot box can forge events for its own site or go silent until revoked.
It cannot read other clients or pivot into the cloud. This residual risk is
accepted while the box is lent to a known site, and closed in Phase 2 by
short-lived tokens, event signing, and hardware-backed keys. The gain is an
auth model that ships in about a day and keeps clients isolated from day one.

## Bias

Match the strength of the mechanism to the money at stake and the size of the
fleet. Buy operational weight (a CA, cert rotation, token infrastructure) when
scale pays for it.

## Effect on existing schema

None. Change-log 0003 already records that attribution is server-side and that
any signature lives in the upload envelope, so `Event` needs no `device_id` and
no signature field.

## Status

Proposed, awaiting validation from Juan or the developer. On validation, append
as D-009 in `docs/DECISIONS.md` with status `validated`.
