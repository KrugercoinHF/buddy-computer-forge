# Buddy Agency contract index

These are contract families, not yet complete production JSON Schemas. Each
consumer must pin a versioned schema before exchanging data.

- replay.frame: deterministic timestamped state, frame index, agents, metrics,
  committee/wing and source window.
- bundle: sealed run record with run metadata, trace, frames, scorecard,
  human confirmation state, hash algorithm and self-hash.
- gt.event: human-confirmed action with source, subject, action, target,
  duration, frame reference and confidence.
- cost.event: auditable provider/resource cost with timestamp, run, agent,
  kind, resource, amount and source reference.
- chat.path: shareable pointer to sealed context with access tier and expiry.
- scene.json: deterministic render recipe with duration, fps, frame refs,
  chapters and score inputs.
- manifest: provenance and reproduction recipe including seed, trace hash,
  frames hash and hash algorithm.

Integrity rules:
- Canonical JSON recursively sorts object keys and preserves array order.
- SHA-256 proves byte-level integrity, not truth or correctness.
- Trace hash covers canonical trace.events; frame hash covers frames.items.
- Bundle hash covers all bundle fields except hash.
- A non-null previous hash is only a pointer; callers must verify it against a
  trusted prior bundle to establish chain continuity.
- Model output is not ground truth without a separate human-confirmation event.
