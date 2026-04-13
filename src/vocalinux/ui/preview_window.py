"""GTK preview window for pending transcript review."""

from __future__ import annotations

import logging
from typing import Callable

import gi

gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, Gtk

from ..transcript_output import OUTPUT_MODE_PREVIEW, TranscriptOutputController

logger = logging.getLogger(__name__)


class PreviewWindow(Gtk.Window):
    """Simple review window for pending transcript commit/discard actions."""

    def __init__(
        self,
        controller: TranscriptOutputController,
        cancel_callback: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(title="Pending Transcript Review")
        self.controller = controller
        self.cancel_callback = cancel_callback
        self.output_mode = controller.output_mode
        self.pending_text = controller.get_pending_text()
        self.live_preview_text = ""
        self.session_active = False

        self.set_default_size(520, 360)
        self.set_border_width(16)
        self.set_type_hint(Gdk.WindowTypeHint.UTILITY)
        self.set_keep_above(True)
        self.set_accept_focus(False)
        self.set_focus_on_map(False)
        self.connect("delete-event", self._on_delete_event)
        self.connect("key-press-event", self._on_key_press_event)

        outer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.add(outer_box)

        self.status_label = Gtk.Label(xalign=0)
        self.status_label.set_line_wrap(True)
        outer_box.pack_start(self.status_label, False, False, 0)

        self.live_preview_label = Gtk.Label(xalign=0)
        self.live_preview_label.set_line_wrap(True)
        outer_box.pack_start(self.live_preview_label, False, False, 0)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_hexpand(True)
        scrolled_window.set_vexpand(True)
        outer_box.pack_start(scrolled_window, True, True, 0)

        self.transcript_view = Gtk.TextView()
        self.transcript_view.set_editable(False)
        self.transcript_view.set_cursor_visible(False)
        self.transcript_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        scrolled_window.add(self.transcript_view)

        button_box = Gtk.ButtonBox(orientation=Gtk.Orientation.HORIZONTAL)
        button_box.set_layout(Gtk.ButtonBoxStyle.END)
        button_box.set_spacing(8)
        outer_box.pack_start(button_box, False, False, 0)

        self.copy_button = Gtk.Button(label="Copy")
        self.copy_button.connect("clicked", self._on_copy_clicked)
        button_box.add(self.copy_button)

        self.discard_button = Gtk.Button(label="Discard")
        self.discard_button.connect("clicked", self._on_discard_clicked)
        button_box.add(self.discard_button)

        self.commit_button = Gtk.Button(label="Commit")
        self.commit_button.connect("clicked", self._on_commit_clicked)
        button_box.add(self.commit_button)

        self.close_button = Gtk.Button(label="Close")
        self.close_button.connect("clicked", self._on_close_clicked)
        button_box.add(self.close_button)

        self._refresh_ui()

    def set_output_mode(self, output_mode: str) -> bool:
        """Update the output mode shown in the preview window."""
        self.output_mode = output_mode
        self._refresh_ui()
        return False

    def update_pending_text(self, pending_text: str) -> bool:
        """Update the pending transcript shown in the window."""
        self.pending_text = pending_text.strip()
        self._refresh_ui()
        return False

    def update_live_preview(self, preview_text: str) -> bool:
        """Update the in-session live preview text."""
        self.live_preview_text = preview_text.strip()
        self._refresh_ui()
        return False

    def set_session_active(self, session_active: bool) -> bool:
        """Update the HTT session state shown in the window."""
        self.session_active = session_active
        self._refresh_ui()
        return False

    def present_for_review(self, steal_focus: bool = False) -> None:
        """Show and focus the review window."""
        logger.info(
            "Presenting preview window. Pending transcript available=%s, steal_focus=%s.",
            bool(self.pending_text),
            steal_focus,
        )
        self.move(0, 0)
        self.set_accept_focus(steal_focus)
        self.set_focus_on_map(steal_focus)
        self.show_all()
        if steal_focus:
            self.present()

    def _refresh_ui(self) -> None:
        pending_available = bool(self.pending_text)
        preview_available = bool(self.live_preview_text)

        if self.session_active:
            status_text = "HTT active. Release to inject the live preview, or press Esc to cancel."
        elif pending_available:
            status_text = (
                "Pending transcript is ready. Review it, then Commit or Discard when you're ready."
            )
        elif self.output_mode == OUTPUT_MODE_PREVIEW:
            status_text = (
                "Preview mode is enabled. Pending transcript will appear here after speech is "
                "finalized."
            )
        else:
            status_text = (
                "Immediate mode is enabled. New speech is typed directly, but any older pending "
                "transcript can still be reviewed here."
            )
        self.status_label.set_text(status_text)

        if preview_available:
            self.live_preview_label.set_text(f"Live preview: {self.live_preview_text}")
            self.live_preview_label.show()
        else:
            self.live_preview_label.hide()

        transcript_text = self.pending_text or (
            "" if self.session_active else "No pending transcript."
        )
        self.transcript_view.get_buffer().set_text(transcript_text)

        self.commit_button.set_sensitive(pending_available and not self.session_active)
        self.discard_button.set_sensitive(pending_available and not self.session_active)
        self.copy_button.set_sensitive(pending_available and not self.session_active)
        self.close_button.set_sensitive(not self.session_active)

    def _on_commit_clicked(self, widget) -> None:
        logger.info("Commit clicked in preview window.")
        if self.controller.commit_pending_text():
            self.hide()

    def _on_discard_clicked(self, widget) -> None:
        logger.info("Discard clicked in preview window.")
        if self.controller.discard_pending_text():
            self.hide()

    def _on_copy_clicked(self, widget) -> None:
        if not self.pending_text:
            logger.info("Copy requested in preview window with no pending text.")
            return

        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(self.pending_text, -1)
        clipboard.store()
        logger.info("Copied pending transcript to clipboard.")

    def _on_close_clicked(self, widget) -> None:
        logger.info("Closing preview window without changing pending transcript.")
        self.hide()

    def _on_delete_event(self, widget, event) -> bool:
        logger.info("Preview window closed via window manager; pending transcript preserved.")
        self.hide()
        return True

    def _on_key_press_event(self, widget, event) -> bool:
        if event.keyval == Gdk.KEY_Escape and self.session_active and self.cancel_callback is not None:
            logger.info("Escape pressed in preview window during active HTT session.")
            self.cancel_callback()
            return True
        return False
