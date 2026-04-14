# Implementation Breakdown (Updated After MVP)

This note tracks the original MVP task list against what has now shipped.

## Status Summary

- Task 0: complete
- Task 1: complete
- Task 2: complete for MVP
- Task 3: complete for MVP
- Task 4: partially complete

The preview-first MVP is now functional enough to treat as the current shipped
baseline, with follow-up work focused on polish, robustness, and ergonomics.

## Task 0 — Baseline Mapping And Feature Flag

### Delivered

- transcript behavior now has explicit modes:
  - `immediate_injection`
  - `preview_deferred_injection`
- config/settings wiring exists for transcript output mode
- legacy values are normalized on load

### Notes

- HTT behavior is now slightly more opinionated than the original plan:
  when the preview window/controller are present, HTT uses the live-preview
  release flow even if the saved output mode is immediate

### Status

- complete

---

## Task 1 — Pending Transcript Store + Events

### Delivered

- `PendingTranscriptStore` now owns buffered transcript accumulation
- `TranscriptOutputController` mediates finalized text handling
- pending-text listeners update UI when buffered text changes
- spacing behavior is normalized through the controller

### Status

- complete

---

## Task 2 — Preview UI Surface And Actions

### Delivered

- standalone GTK preview window exists
- actions implemented:
  - `Commit`
  - `Discard`
  - `Copy`
- tray can open/focus the preview window
- preview settings now include:
  - horizontal placement
  - vertical placement

### MVP deviation from original plan

- the preview UI shipped as a standalone utility window instead of a
  tray-attached popover
- this turned out to be the simpler and more reliable MVP path

### Status

- complete for MVP

---

## Task 3 — Commit Pipeline + State Integration

### Delivered

- pending transcript commit injects once and clears on success
- discard clears pending transcript without injection
- preview mode does not auto-inject on stop
- HTT release now commits live preview text directly
- HTT `Esc` cancellation closes the preview path and suppresses trailing
  finalized callbacks until `IDLE`
- duplicate injection path caused by synthetic post-typing `Escape` has been removed

### Notes

- command actions still run immediately through the existing action path
- dictated text and command actions now have meaningfully different output paths,
  which is acceptable for MVP but should stay documented

### Status

- complete for MVP

---

## Task 4 — Hardening, Regressions, And Docs

### Delivered

- additional lifecycle logging around:
  - pending transcript changes
  - HTT preview session start/commit/cancel
  - preview window presentation
  - sound playback requests
  - xdotool typing settings
- tests now cover:
  - output-mode normalization
  - pending transcript behavior
  - HTT suppression behavior
  - preview/settings config
  - text injector delay behavior

### Still Outstanding

- broader manual verification across desktop/session combinations
- more explicit documentation of HTT-vs-toggle behavior in end-user docs
- better install-time persistence UX around reuse of prior install choices
- deeper negative-path testing for injector failure / focus drift in real desktops

### Status

- partially complete

---

## Current Acceptance Snapshot

### Working

- immediate mode still injects directly
- preview mode buffers finalized text for explicit review
- preview window can commit/discard/copy pending transcript
- HTT opens preview immediately
- HTT release injects live preview text
- HTT `Esc` cancels the session
- preview placement is configurable
- xdotool typing delay is configurable

### Known Limitations

- injection is still simulated typing for xdotool targets
- preview window is not yet tray-attached
- HTT live preview text is still dependent on recognition cadence and may lag on
  very quick releases
- install-config reuse needed extra hardening for older installs / missing
  metadata files

## Recommended Next Work

1. Harden installer reuse flow and document where installer metadata lives.
2. Add manual QA coverage for HTT on X11, XWayland, and Wayland/IBus paths.
3. Consider a faster non-typing injection path where platform/tooling allows it.
4. Decide whether HTT should remain preview-window-driven regardless of saved
   transcript output mode, or become explicitly configurable.
5. Improve preview UX with optional tray anchoring, sizing, and maybe inline edit support.
