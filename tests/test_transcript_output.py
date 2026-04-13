"""Tests for transcript output mode control and pending transcript state."""

import unittest
from unittest.mock import MagicMock

from vocalinux.common_types import RecognitionState
from vocalinux.transcript_output import (
    OUTPUT_MODE_IMMEDIATE,
    OUTPUT_MODE_PREVIEW,
    PendingTranscriptStore,
    TranscriptOutputController,
    normalize_output_mode,
)
from vocalinux.ui.action_handler import ActionHandler


class TestOutputModeNormalization(unittest.TestCase):
    def test_normalize_legacy_output_modes(self):
        self.assertEqual(normalize_output_mode("immediate"), OUTPUT_MODE_IMMEDIATE)
        self.assertEqual(normalize_output_mode("deferred_until_release"), OUTPUT_MODE_PREVIEW)

    def test_unknown_output_mode_falls_back_to_immediate(self):
        self.assertEqual(normalize_output_mode("unknown-mode"), OUTPUT_MODE_IMMEDIATE)


class TestPendingTranscriptStore(unittest.TestCase):
    def test_append_and_clear(self):
        store = PendingTranscriptStore()
        listener = MagicMock()
        store.register_listener(listener)

        store.append_segment("hello")
        store.append_segment(" world ")

        self.assertEqual(store.get_text(), "hello world")
        listener.assert_called_with("hello world")

        store.clear(reason="test")
        self.assertEqual(store.get_text(), "")


class TestTranscriptOutputController(unittest.TestCase):
    def _make_controller(self, output_mode: str) -> tuple[TranscriptOutputController, MagicMock]:
        text_injector = MagicMock()
        text_injector.inject_text.return_value = True
        action_handler = ActionHandler(text_injector)
        controller = TranscriptOutputController(output_mode, text_injector, action_handler)
        return controller, text_injector

    def test_preview_mode_buffers_until_commit(self):
        controller, text_injector = self._make_controller(OUTPUT_MODE_PREVIEW)

        controller.handle_finalized_text("hello")
        controller.handle_finalized_text("world")

        text_injector.inject_text.assert_not_called()
        self.assertEqual(controller.get_pending_text(), "hello world")

        self.assertTrue(controller.commit_pending_text())
        text_injector.inject_text.assert_called_once_with("hello world")
        self.assertFalse(controller.has_pending_text())

    def test_preview_mode_preserves_pending_text_on_idle(self):
        controller, text_injector = self._make_controller(OUTPUT_MODE_PREVIEW)

        controller.handle_state_change(RecognitionState.LISTENING)
        controller.handle_finalized_text("partial")
        controller.handle_state_change(RecognitionState.IDLE)

        text_injector.inject_text.assert_not_called()
        self.assertEqual(controller.get_pending_text(), "partial")

    def test_immediate_mode_injects_with_spacing(self):
        controller, text_injector = self._make_controller(OUTPUT_MODE_IMMEDIATE)

        controller.handle_finalized_text("hello")
        controller.handle_finalized_text("world")

        self.assertEqual(
            [call.args[0] for call in text_injector.inject_text.call_args_list],
            ["hello", " world"],
        )

    def test_live_preview_commit_suppresses_next_finalized_callback(self):
        controller, text_injector = self._make_controller(OUTPUT_MODE_PREVIEW)

        controller.begin_push_to_talk_preview_session()
        controller.update_live_preview_text("live preview text")
        self.assertTrue(controller.commit_live_preview_text())
        controller.handle_finalized_text("finalized text")

        text_injector.inject_text.assert_called_once_with("live preview text")
        self.assertFalse(controller.has_pending_text())

    def test_live_preview_cancel_suppresses_next_finalized_callback(self):
        controller, text_injector = self._make_controller(OUTPUT_MODE_PREVIEW)

        controller.begin_push_to_talk_preview_session()
        controller.update_live_preview_text("live preview text")
        controller.cancel_live_preview_session()
        controller.handle_finalized_text("finalized text")

        text_injector.inject_text.assert_not_called()
        self.assertFalse(controller.has_pending_text())

    def test_active_htt_preview_ignores_finalized_text_even_in_immediate_mode(self):
        controller, text_injector = self._make_controller(OUTPUT_MODE_IMMEDIATE)

        controller.begin_push_to_talk_preview_session()
        controller.handle_finalized_text("finalized text")

        text_injector.inject_text.assert_not_called()
        self.assertFalse(controller.has_pending_text())


if __name__ == "__main__":
    unittest.main()
