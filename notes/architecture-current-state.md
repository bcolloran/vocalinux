# Architecture: Current State

This document describes the current runtime pipeline in Vocalinux after the MVP
preview work landed.

## Runtime Overview

The app now has two transcript output paths:

- `immediate_injection`
  - finalized dictated text is injected as soon as it is produced
- `preview_deferred_injection`
  - finalized dictated text is buffered for explicit `Commit` / `Discard`

There is also a special **hold-to-transcribe live preview path**:

- when HTT starts, the preview window opens immediately
- incremental preview text becomes the source of truth for HTT release
- on release, the current live preview text is injected immediately
- on `Esc`, the HTT session is cancelled and trailing finalized callbacks are suppressed until idle

## Pipeline Walkthrough

## 1) `_record_audio` (capture thread)

`SpeechRecognitionManager.start_recognition()` starts `_record_audio` on
`audio_thread`.

What `_record_audio` does:

- opens the PyAudio input stream
- reads chunks into `self.audio_buffer` under lock
- normalizes channels / sample rate as needed
- applies silence logic
  - in `toggle` mode, finalized chunks are enqueued on silence timeout
  - in `push_to_talk` mode, enqueue is deferred until release / stop
- emits audio-level callbacks for UI metering

## 2) `_perform_recognition` (recognition thread)

`start_recognition()` also starts `_perform_recognition` on
`recognition_thread`.

What `_perform_recognition` does:

- drains `_segment_queue`
- for each segment:
  - sets state to `PROCESSING`
  - calls `_process_audio_buffer(segment)`
  - returns to `LISTENING` if recording continues
- handles stop via queue sentinel and queue-drain logic

## 3) `_process_audio_buffer` (transcribe + parse)

For each immutable audio segment:

- transcribes through the selected engine
  - `vosk`
  - `whisper`
  - `whisper_cpp`
- runs the command processor when voice commands are enabled
- emits:
  - `text_callbacks(processed_text)` for dictated text
  - `action_callbacks(action)` for commands

Incremental preview text is emitted separately through preview callbacks during
active recognition.

## 4) `main.py` callback bridge

`main.py` now wires recognition into a transcript output controller instead of
injecting dictated text directly from the callback wrapper.

Current callback wiring:

- `register_text_callback(output_controller.handle_finalized_text)`
- `register_preview_callback(tray_indicator._on_preview_text_changed)`
- `register_action_callback(action_handler.handle_action)`
- `register_state_callback(on_state_change)`

`on_state_change(...)` fans recognition state into:

- `output_controller.handle_state_change(...)`
- tray / preview UI updates

## 5) `TranscriptOutputController`

`TranscriptOutputController` is now the central output-policy layer.

It owns:

- output mode normalization
- pending transcript accumulation through `PendingTranscriptStore`
- immediate injection spacing behavior
- HTT live preview commit / cancel suppression

Behavior by mode:

- `immediate_injection`
  - finalized text injects immediately through `TextInjector`
- `preview_deferred_injection`
  - finalized text is appended to pending transcript
  - explicit commit injects the full pending transcript once
  - discard clears without injection

Special HTT behavior:

- `begin_push_to_talk_preview_session()`
  - marks the live preview session active
- `commit_live_preview_text()`
  - injects the current live preview immediately
  - suppresses later finalized callbacks until idle
- `cancel_live_preview_session()`
  - clears live preview state
  - suppresses later finalized callbacks until idle

## 6) Tray + Preview Window

`TrayIndicator` is now the main HTT preview orchestrator.

What it does:

- opens the preview window when HTT starts
- forwards incremental preview text to both:
  - tray live preview label
  - preview window live preview area
- commits live preview text on HTT release
- cancels HTT session on global `Esc`
- shows pending transcript in the preview window for explicit commit / discard

The preview surface is currently a standalone GTK utility window, not a
tray-attached popover.

## Current Data-Flow Diagram

```mermaid
flowchart LR
  Mic[Microphone] --> A[_record_audio\n(audio_thread)]
  A -->|silence / release / stop| Q[_segment_queue]
  Q --> R[_perform_recognition\n(recognition_thread)]
  R --> P[_process_audio_buffer]
  P -->|finalized text| TC[text_callbacks]
  P -->|preview text| PC[preview_callbacks]
  P -->|actions| AC[action_callbacks]

  subgraph GTK[GTK Main Thread]
    TOC[TranscriptOutputController]
    PTS[PendingTranscriptStore]
    TRAY[TrayIndicator]
    PW[PreviewWindow]
    AH[ActionHandler]
    TI[TextInjector.inject_text]
  end

  TC --> TOC
  TOC -->|preview mode| PTS
  PTS --> PW
  TOC -->|immediate mode / HTT live commit| TI
  PC --> TRAY
  TRAY --> PW
  AC --> AH --> TI
```

## Threading Model

- GTK main thread
  - tray UI
  - preview window UI
  - settings dialog
  - most output-policy state changes
- audio capture thread
  - microphone reads
  - buffering
  - silence segmentation
- recognition thread
  - queue draining
  - transcription
  - finalized / preview callback emission

### Shared structures

- `self.audio_buffer`
  - protected by `self._buffer_lock`
- model / recognizer state
  - protected by `self._model_lock`
- `_segment_queue`
  - thread-safe handoff between capture and recognition
- `PendingTranscriptStore`
  - internal lock for append / clear / read / listener snapshots

## State Notes

Recognition states remain:

- `IDLE`
- `LISTENING`
- `PROCESSING`
- `ERROR`

Important additions:

- HTT preview session state is tracked outside the recognition state enum
- finalized-text suppression now persists until `IDLE` after HTT commit/cancel
  so late recognition callbacks cannot double-inject text

## Practical Behavior Summary

- toggle mode + immediate output:
  - behaves like classic Vocalinux
- toggle mode + preview output:
  - finalized text buffers until manual `Commit` / `Discard`
- HTT:
  - always uses the live preview release flow when preview window/controller are available
  - release injects live preview text
  - `Esc` cancels

## Known Architectural Follow-Ups

- preview window ownership still lives partly in `TrayIndicator`; this could be
  separated into a dedicated controller later
- xdotool injection is still simulated typing, not a true paste-style commit
- output behavior is now richer, but recognition/session state is still managed
  by a small mix of explicit state plus helper flags rather than a formal state
  machine
