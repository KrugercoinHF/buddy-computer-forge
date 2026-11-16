# Buddy Agency multimodal system integration — V1

**Status:** Architecture specification only. No provider, device capture, media
upload, inference route or computer execution is enabled.

## Goal

One governed multimodal ingestion layer for Buddy Computer Programming Agent,
AI Boardroom, Buddy Knowledge Core, BuddyBot and future desktop experiences.
Products consume typed evidence references, not vendor-specific model APIs.

## Architecture

Images / audio / video / text / screen capture
 -> consent and policy gate
 -> immutable content-addressed media vault
 -> deterministic media inspection
 -> modality adapters (OCR / ASR / frame sampling / text extraction)
 -> optional provider-neutral inference adapters
 -> evidence and provenance normalizer
 -> typed annotations and event references
 -> Boardroom / Knowledge Core / BuddyBot context
 -> human review and confirmation
 -> owner-gated task proposal gateway

## Modality boundaries

| Modality | Deterministic inspection | Derived interpretation |
|---|---|---|
| Image | byte hash, MIME, dimensions, color profile | OCR, captions, objects, regions |
| Audio | codec, sample rate, channels, duration, sample hash | ASR, diarization, sound labels |
| Video | container, codec, duration, frame rate, frame timestamps | scene changes, sampled-frame captions, OCR |
| Text | encoding, byte hash, normalized version | classification, extraction, summary |
| Screen/UI | capture timestamp, frame hash, viewport | OCR, UI interpretation, action proposal |

Every adapter result uses a versioned envelope: event_id, schema_version,
modality, source_asset_ref, source_sha256, created_at, processor,
processor_version, config_hash, time_range, payload_ref, confidence (when
meaningful), and derived=true/false.

## Three trust classes

1. Source facts: immutable source bytes and deterministic inspection.
2. Derived annotations: OCR, ASR, captions, embeddings and model inferences.
   Record provider/model, version, config or prompt hash, confidence, source
   reference and time/region.
3. Human ground truth: corrections, labels and approvals attributed to a
   named actor and timestamp.

Derived annotations may enrich search and meeting context. They must not be
silently promoted to ground truth, metrics, deterministic replay inputs,
billing records or bundle hashes. Human acceptance creates a new event
referencing the original annotation.

## Shared services

- Media vault: encrypted content-addressed storage, access policy, retention,
  deletion propagation, malware/type checks and scoped access links.
- Adapter registry: provider-neutral interface, capabilities, version and
  allowed data classes.
- Job orchestration: async jobs, idempotency keys, bounded retries, timeout,
  cancellation and dead-letter state.
- Evidence ledger: immutable source references and annotation lineage.
- Policy gateway: consent, privacy class, retention, provider allowlist,
  region, budget and owner approval.
- Observability: job status, latency, spend, failures and traceability.

## API contract sketch (not implemented)

- POST /v1/media/assets — register/upload after policy checks.
- GET /v1/media/assets/{asset_id} — metadata and access policy.
- POST /v1/media/assets/{asset_id}/jobs — request an allowed adapter task.
- GET /v1/media/jobs/{job_id} — job state and annotation references.
- POST /v1/evidence/{annotation_id}/confirm — human confirmation/correction.
- POST /v1/boardroom/meetings/{meeting_id}/evidence — attach selected evidence.
- POST /v1/tasks/proposals — create a proposal; never execute it.

## Integration sequence

1. Contract and local-fixture phase: JSON Schemas, synthetic fixtures, MIME
   sniffing, hashes and negative tests.
2. Local media phase: sandboxed image/audio/video metadata inspection only.
3. Provider phase: one opt-in provider at a time, secure secrets, consent,
   retention review and hard spend ceilings.
4. Boardroom phase: attach timestamped evidence refs; claims cite evidence or
   explicitly identify assumptions.
5. Knowledge Core phase: index approved annotations with source lineage and
   deletion propagation.
6. Desktop phase: screen interpretation stays read-only. Computer control is
   a separate permission and never implied by multimodal access.

## Security and privacy gates

- Private/local storage by default; encryption at rest and in transit.
- Explicit consent before recording, uploading or sending media to a provider.
- No covert capture, always-on recording or bystander-identification workflow.
- Configurable retention and deletion propagation.
- Provider allowlists, region restrictions, rate limits and hard spend caps.
- Treat OCR, transcripts, images and embedded prompts as untrusted input.
- Never execute tools based solely on model interpretation of media.
- Separate approval for export, external sharing, execution, deployment and spend.
- Audit submit, process, view, confirm, export and delete events.

## Acceptance criteria

Stable asset IDs and hashes; deceptive MIME rejection; source-linked annotations;
versioned provider provenance; deterministic inspection replay; immutable human
confirmation events; revocation/deletion; Boardroom evidence references without
raw-media duplication; no action gateway reachable from media processing; tests
for auth, consent denial, malformed media, duplicate jobs, provider failure,
retention expiry and audit lineage.


## Provider implementation notes — reviewed 2026-11-14

The first optional provider adapter can target OpenAI, while the core contracts
remain vendor-neutral:

- Image understanding: the Responses API accepts text and image inputs; images
  can be supplied by URL, Base64 data URL or Files API file ID. Use the
  documented input_image content type and pin supported detail settings.
- Recorded audio: use the dedicated file-transcription workflow when the output
  needed is a transcript, rather than routing every file through a live agent.
- Live voice: use GPT-Live for a conversational voice experience or the Realtime
  API where direct session, transport and tool control is required. For browser
  sessions, create ephemeral credentials server-side; never expose the API key.
- Video understanding: treat video as a media pipeline. Extract a timestamped
  frame sequence and audio track, process those through image and audio adapters,
  then join annotations by source asset and time range. The Responses overview
  documents text/image inputs; do not assume arbitrary raw video upload is a
  supported Responses input.
- Do not start a new integration on the Assistants API: OpenAI documents its
  sunset on 2026-08-26 and directs new integrations to the Responses API.

These notes are a provider option, not a vendor lock-in decision. Confirm the
selected model's current modality, file-size, region, retention, cost and rate
limits immediately before implementation.

### Official references

- Images and vision: https://developers.openai.com/api/docs/guides/images-vision
- Audio and voice workflow selection: https://developers.openai.com/api/docs/guides/audio
- Realtime API, WebRTC and ephemeral credentials: https://developers.openai.com/api/docs/guides/realtime
- Responses API supported input overview: https://developers.openai.com/api/reference/responses/overview
- Assistants API migration/sunset: https://platform.openai.com/docs/assistants/migration
