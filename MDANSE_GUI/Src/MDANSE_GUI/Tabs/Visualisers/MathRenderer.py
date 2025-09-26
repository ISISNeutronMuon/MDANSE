from __future__ import annotations

import base64
import io
import re

from matplotlib import pyplot as plt


class MathRenderer:
    # Cache mapping the raw LaTex expression to its rendered image form
    cache = {}

    # Ignore the following expression
    ignores = {"`\mathbf{q}`": "q"}

    def __init__(self, text: str) -> None:
        self.raw_text = text

    @staticmethod
    def replace_ignored(text: str) -> str:
        return MathRenderer.ignores[text]

    @staticmethod
    def ignore(text: str) -> bool:
        return text in MathRenderer.ignores

    def scan(self) -> dict[str, bool]:
        # Use regex matching to find expressions
        pattern = r"(:math:`.*?`)"
        substrings = re.split(pattern, self.raw_text)

        scanned = {}
        for s in substrings:
            if not s:
                # This is not a string - skip
                continue

            # Get the raw expression content to check if it is ignored
            raw_expr = s[len(":math:") :]
            if self.ignore(raw_expr):
                # We ignore rendering this
                s = MathRenderer.replace_ignored(raw_expr)
                substrings[-1] = s + substrings[-1]
                continue

            if s.startswith(":math:`") and s.endswith("`"):
                # This is a raw LaTex expression string - instantiate object to identify it as such
                expr = s[len(":math:`") : -1]
                scanned.update({expr: True})
            else:
                # Normal text string
                scanned.update({s: False})

        return scanned

    @staticmethod
    def mask(text: str) -> str:
        return f"${text}$"

    @staticmethod
    def render(expression: str) -> None:
        # Create a figure containing the rendered LaTex expression
        fig, ax = plt.subplots(figsize=(0.01, 0.01))
        ax.axis("off")
        fig.text(0, 0, MathRenderer.mask(expression), fontsize=6)

        # Save the image as bytes
        buffer = io.BytesIO()
        plt.savefig(buffer, format="png", bbox_inches="tight", pad_inches=0.1, dpi=150)
        plt.close(fig)
        buffer.seek(0)
        image = base64.b64encode(buffer.read()).decode("utf-8")

        # Cache rendered expression
        MathRenderer.set_cache(expression, image)

    @classmethod
    def set_cache(cls, key, value) -> None:
        cls.cache.update({key: value})

    @classmethod
    def cached(cls, key) -> bool:
        result = key in cls.cache
        return result

    @classmethod
    def from_cache(cls, key):
        return cls.cache[key]
