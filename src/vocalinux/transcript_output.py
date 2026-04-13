"""Transcript output modes and pending transcript control."""

from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING, Callable

from .common_types import RecognitionState, TextInjectorProtocol

if TYPE_CHECKING:
    from .ui.action_handler import ActionHandler

logger = logging.getLogger(__name__)

OUTPUT_MODE_IMMEDIATE = "immediate_injection"
OUTPUT_MODE_PREVIEW = "preview_deferred_injection"
OUTPUT_MODE_DEFAULT = OUTPUT_MODE_IMMEDIATE

LEGACY_OUTPUT_MODE_MAP = {
    "immediate": OUTPUT_MODE_IMMEDIATE,
    "deferred_until_release": OUTPUT_MODE_PREVIEW,
}

VALID_OUTPUT_MODES = {OUTPUT_MODE_IMMEDIATE, OUTPUT_MODE_PREVIEW}


def normalize_output_mode(output_mode: str | None) -> str:
    """Normalize current and legacy output-mode values."""
    if output_mode in VALID_OUTPUT_MODES:
        return str(output_mode)

    if output_mode in LEGACY_OUTPUT_MODE_MAP:
        normalized = LEGACY_OUTPUT_MODE_MAP[str(output_mode)]
        logger.info(
            "Migrating legacy output mode '%s' to '%s'.",
            output_mode,
            normalized,
        )
        return normalized

    if output_mode is not None:
        logger.warning(
            "Unknown output mode '%s'. Falling back to '%s'.",
            output_mode,
            OUTPUT_MODE_DEFAULT,
        )
    return OUTPUT_MODE_DEFAULT


class PendingTranscriptStore:
    """Thread-safe pending transcript accumulator."""

    def __init__(self) -> None:
        self._segments: list[str] = []
        self._listeners: list[Callable[[str], None]] = []
        self._lock = threading.Lock()

    def append_segment(self, text: str) -> str:
        """Append a finalized segment and return the full pending transcript."""
        segment = text.strip()
        if not segment:
            return self.get_text()

        with self._lock:
            self._segments.append(segment)
            pending_text = " ".join(self._segments)

        logger.info(
            "Pending transcript updated: %s segment(s), %s character(s).",
            len(self._segments),
            len(pending_text),
        )
        self._notify_listeners(pending_text)
        return pending_text

    def get_text(self) -> str:
        """Return the full pending transcript."""
        with self._lock:
            return " ".join(self._segments)

    def has_text(self) -> bool:
        """Return whether any pending transcript is available."""
        with self._lock:
            return bool(self._segments)

    def clear(self, reason: str = "manual_clear") -> None:
        """Clear all pending transcript state."""
        with self._lock:
            had_text = bool(self._segments)
            self._segments.clear()

        if had_text:
            logger.info("Pending transcript cleared (%s).", reason)
        else:
            logger.debug("Pending transcript clear requested with no pending text (%s).", reason)
        self._notify_listeners("")

    def register_listener(self, callback: Callable[[str], None]) -> None:
        """Register a listener for pending transcript changes."""
        with self._lock:
            self._listeners.append(callback)

    def unregister_listener(self, callback: Callable[[str], None]) -> None:
        """Unregister a listener for pending transcript changes."""
        with self._lock:
            try:
                self._listeners.remove(callback)
            except ValueError:
                logger.debug("Pending transcript listener not found: %s", callback)

    def _notify_listeners(self, pending_text: str) -> None:
        with self._lock:
            listeners = list(self._listeners)

        for callback in listeners:
            try:
                callback(pending_text)
            except Exception as exc:
                logger.warning("Pending transcript listener failed: %s", exc)


class TranscriptOutputController:
    """Coordinate immediate injection and preview-first transcript review."""

    def __init__(
        self,
        output_mode: str,
        text_injector: TextInjectorProtocol,
        action_handler: "ActionHandler",
        pending_store: PendingTranscriptStore | None = None,
    ) -> None:
        self.text_injector = text_injector
        self.action_handler = action_handler
        self.pending_store = pending_store or PendingTranscriptStore()
        self.output_mode = normalize_output_mode(output_mode)
        self._mode_listeners: list[Callable[[str], None]] = []

    def is_preview_mode(self) -> bool:
        """Return whether the controller is in preview-first mode."""
        return self.output_mode == OUTPUT_MODE_PREVIEW

    def set_output_mode(self, output_mode: str) -> None:
        """Update the current output mode."""
        normalized_mode = normalize_output_mode(output_mode)
        if normalized_mode == self.output_mode:
            return

        previous_mode = self.output_mode
        self.output_mode = normalized_mode
        logger.info("Transcript output mode changed from %s to %s.", previous_mode, normalized_mode)
        if (
            previous_mode == OUTPUT_MODE_PREVIEW
            and normalized_mode == OUTPUT_MODE_IMMEDIATE
            and self.pending_store.has_text()
        ):
            logger.info(
                "Immediate mode enabled while pending transcript exists; pending text remains "
                "available for explicit commit or discard."
            )
        self._notify_mode_listeners(normalized_mode)

    def register_mode_listener(self, callback: Callable[[str], None]) -> None:
        """Register a listener for output mode changes."""
        self._mode_listeners.append(callback)

    def register_pending_text_listener(self, callback: Callable[[str], None]) -> None:
        """Register a listener for pending transcript changes."""
        self.pending_store.register_listener(callback)

    def unregister_pending_text_listener(self, callback: Callable[[str], None]) -> None:
        """Unregister a listener for pending transcript changes."""
        self.pending_store.unregister_listener(callback)

    def get_pending_text(self) -> str:
        """Return the current pending transcript."""
        return self.pending_store.get_text()

    def has_pending_text(self) -> bool:
        """Return whether pending transcript is available."""
        return self.pending_store.has_text()

    def handle_finalized_text(self, text: str) -> None:
        """Handle a finalized recognition segment."""
        text_to_handle = text.strip()
        if not text_to_handle:
            logger.debug("Ignoring empty finalized text segment.")
            return

        if self.is_preview_mode():
            pending_text = self.pending_store.append_segment(text_to_handle)
            logger.info(
                "Buffered finalized segment in preview mode: %s character(s) pending.",
                len(pending_text),
            )
            return

        if self.action_handler.last_injected_text and self.action_handler.last_injected_text.strip():
            text_to_handle = f" {text_to_handle}"
            logger.debug("Added separator space before immediate segment injection.")

        success = self.text_injector.inject_text(text_to_handle)
        logger.info(
            "Immediate transcript injection %s for %s character(s).",
            "succeeded" if success else "failed",
            len(text_to_handle),
        )
        if success:
            self.action_handler.set_last_injected_text(text_to_handle)

    def handle_state_change(self, state: RecognitionState) -> None:
        """Update output state in response to recognition state changes."""
        if state == RecognitionState.LISTENING:
            self.action_handler.set_last_injected_text("")
            logger.info(
                "Recognition session started in %s mode. Pending transcript currently %s.",
                self.output_mode,
                "present" if self.pending_store.has_text() else "empty",
            )
            return

        if state == RecognitionState.IDLE:
            if self.is_preview_mode() and self.pending_store.has_text():
                logger.info(
                    "Recognition stopped with pending transcript ready for review (%s character(s)).",
                    len(self.pending_store.get_text()),
                )
            else:
                logger.info("Recognition entered idle state with no pending transcript action.")
            return

        if state == RecognitionState.ERROR:
            logger.warning(
                "Recognition entered error state. Pending transcript preserved=%s.",
                self.pending_store.has_text(),
            )

    def commit_pending_text(self) -> bool:
        """Inject the pending transcript and clear it on success."""
        pending_text = self.pending_store.get_text()
        if not pending_text:
            logger.info("Commit requested with no pending transcript.")
            return False

        logger.info("Committing pending transcript (%s character(s)).", len(pending_text))
        success = self.text_injector.inject_text(pending_text)
        logger.info("Pending transcript commit %s.", "succeeded" if success else "failed")
        if success:
            self.action_handler.set_last_injected_text(pending_text)
            self.pending_store.clear(reason="commit")
        return success

    def discard_pending_text(self) -> bool:
        """Discard any pending transcript."""
        if not self.pending_store.has_text():
            logger.info("Discard requested with no pending transcript.")
            return False

        logger.info("Discarding pending transcript.")
        self.pending_store.clear(reason="discard")
        return True

    def _notify_mode_listeners(self, output_mode: str) -> None:
        for callback in list(self._mode_listeners):
            try:
                callback(output_mode)
            except Exception as exc:
                logger.warning("Output mode listener failed: %s", exc)
