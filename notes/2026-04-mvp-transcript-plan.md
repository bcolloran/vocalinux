# MVP Transcript Plan (April 2026)

## Conversation Summary & Product Decisions

This planning pass is focused on documenting and de-risking an MVP that introduces a **preview-first transcription flow** in Vocalinux, while preserving the existing speech engine and injection plumbing.

### Decisions captured in this plan

1. **Keep the recognition core intact for MVP**
   - Reuse the existing capture/segmentation/transcription loop in `SpeechRecognitionManager`.
   - Do not swap recognition engines or rewrite threading as part of MVP.

2. **Introduce deferred injection via a preview step**
   - Recognized text should be buffered and shown to the user first.
   - Injection should happen only after explicit confirmation (or equivalent deferred-commit trigger).

3. **Retain existing voice-command/action behavior unless explicitly gated**
   - Current command parsing remains available.
   - Any command side-effects that conflict with preview mode should be scoped as follow-up design work.

4. **Ship incrementally behind a mode/flag**
   - Existing immediate-injection behavior remains the default fallback unless preview mode is enabled.

## MVP Scope

### In-scope

- Add a productized **preview + deferred injection** flow for dictated text.
- Keep compatibility with current engines (`vosk`, `whisper`, `whisper_cpp`).
- Preserve current hotkey interaction model (`toggle` and `push_to_talk`) while ensuring pending preview text is not injected automatically.
- Add minimal UI/state hooks needed to:
  - show pending transcript,
  - confirm injection,
  - cancel/clear pending transcript.
- Add tests for queueing behavior, state transitions, and commit/cancel outcomes.

### Explicit non-goals (for MVP)

- Full transcript editor (rich text, cursor-level editing, history timelines).
- Multi-utterance semantic post-processing/rewrite pipeline.
- Cross-device sync/cloud transcript storage.
- Re-architecting GTK tray or replacing input-injection backends.
- Large engine-level algorithm changes (new VAD stack, streaming partial decoder redesign).

## Risks

1. **Threading/race complexity**
   - Audio and recognition run in background threads; introducing a pending-text buffer risks new ordering issues during stop/drain.

2. **UI-thread safety**
   - Recognition callbacks currently invoke injection directly; preview updates may need explicit handoff to GTK main thread.

3. **Command-vs-dictation ambiguity**
   - In preview mode, command actions may need to execute immediately while text waits for commit.

4. **Stop behavior edge cases**
   - Existing queue drain + sentinel stop signaling can produce subtle lifecycle issues; deferred commit adds another stage to reason about.

5. **Injection environment variance**
   - X11/Wayland/IBus differences may affect commit reliability and user expectations.

## Open Questions

1. What is the exact UX for preview confirmation?
   - Tray menu action, shortcut, popup, or settings-selectable mode?

2. Should voice commands execute during preview mode?
   - Always, never, or configurable subset?

3. How should multi-segment spacing behave before commit?
   - Preserve current implicit spacing or show exact raw segments?

4. What should happen to pending text when state returns to `IDLE`?
   - Auto-clear, persist until user action, or configurable policy?

5. Do we support partial/streaming preview in MVP or finalized segments only?

## Success Criteria for MVP

- Users can dictate without immediate text injection.
- Users can explicitly commit or discard pending transcript.
- Existing immediate injection flow remains available and stable.
- No regressions in start/stop recognition controls.
