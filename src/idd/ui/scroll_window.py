from textual.widgets import ScrollView

class ScrollWindow(ScrollView):
    prev = ""

    async def set_text(self, text_input, should_append = True):
        pre_y = self.y
        if should_append:
            prev = "\n===============================\n"
            prev += "\n".join(e for e in text_input)
            self.prev += prev
        else:
            self.prev = "\n".join(e for e in text_input)

        await self.update(self.prev)
        self.y = pre_y
        self.animate("y", self.window.virtual_size.height, duration=1, easing="linear")
