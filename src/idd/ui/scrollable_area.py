from __future__ import annotations
import os
import time
from textual.widgets import RichLog
from textual import events
from textual.reactive import reactive


class TextScrollView(RichLog):
    COMPONENT_CLASSES = {
        "box",         # Class for the main text container
        "rich-text--line",   # Class for each line of text
    }
    DEFAULT_CSS = """
    TextScrollView {
        height: 100%;
        scrollbar-size: 1 1;
        border: solid green;
    }
    """

    # Terminal-specific selection tips
    SELECTION_TIPS = {
        "Terminal.app": "Option(⌥)+Click to select text",
        "iTerm2": "Cmd(⌘)+Shift+C: Copy mode | Option(⌥)+Click: Selection",
        "Warp": "Shift+Click to select text",
        "default": "Use terminal's selection mechanism to copy text" #default mac terminal
    }
    
    # Track if we've shown the tip for this panel
    tip_shown = reactive(False)

    def __init__(self, title: str = "", component_id: str = None) -> None:
        super().__init__(name=title, auto_scroll=True, markup=True)
        self.border_title = title
        if component_id:
            self.id = component_id
        self._hover_start = 0

    def append(self, lines: list[str]):
        self.write("\n".join(lines))

    def text(self, lines: list[str]):
        self.clear()
        self.append(lines)
        
    def _get_terminal_type(self):
        """Try to detect terminal type from environment variables."""
        term_program = os.environ.get("TERM_PROGRAM", "")
        if "iTerm" in term_program:
            return "iTerm2"
        elif "Apple_Terminal" in term_program:
            return "Terminal.app"
        elif "WarpTerminal" in term_program:
            return "Warp"
        return "default"
    
    def on_mouse_down(self, event: events.MouseDown) -> None:
        """Track when the user clicks on the panel."""
        self._clicked = True
        self._hover_start = time.time()  # Start timing from the click
    
    def on_mouse_move(self, event: events.MouseMove) -> None:
        """Show selection tip after clicking and hovering."""
        # Only show tip if we've been clicked and haven't shown a tip yet
        if hasattr(self, '_clicked') and self._clicked and not self.tip_shown:
            current_time = time.time()
            hover_duration = current_time - self._hover_start
            
            # Show tip after 0.1 seconds of hovering after a click
            if hover_duration > 0.1:
                terminal = self._get_terminal_type()
                tip = self.SELECTION_TIPS.get(terminal, self.SELECTION_TIPS["default"])
                self.notify(tip, severity="information", timeout=5)
                self.tip_shown = True 
    
    def on_mouse_up(self, event: events.MouseUp) -> None:
        """Reset click state when mouse button is released."""
        if hasattr(self, '_clicked'):
            self._clicked = False
    
    def on_leave(self, event: events.Leave) -> None:
        """Reset hover timer and click state when mouse leaves the widget."""
        self._hover_start = 0
        if hasattr(self, '_clicked'):
            self._clicked = False
    
