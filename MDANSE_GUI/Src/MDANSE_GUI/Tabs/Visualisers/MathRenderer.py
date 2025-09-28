from __future__ import annotations

import base64
import io
import re

from matplotlib import pyplot as plt


class MathRenderer:
    # Cache mapping the raw LaTex expression to its rendered image form
    cache = {}

    # Ignore the following expression
    ignores = {r"`\mathbf{q}`": "q"}

    def __init__(self, text: str) -> None:
        self.raw_text = text

    @staticmethod
    def replace_ignored(text: str) -> str:
        return MathRenderer.ignores[text]

    @staticmethod
    def ignore(text: str) -> bool:
        return text in MathRenderer.ignores

    @staticmethod
    def containsMultiLineBlockExpression(text: str) -> bool:
        return text == ".. math::" or text == r"<br />.. math::<br />"

    @staticmethod
    def containsBlockExpression(text: str) -> bool:
        return text.startswith(".. math:")

    @staticmethod
    def containsInlineExpressions(text: str) -> bool:
        pattern = r"(:math:`.*?`)"
        substrings = re.split(pattern, text)
        return len(substrings) > 1

    @staticmethod
    def processBlockExpression(text: str) -> list[tuple[str, bool]]:
        return [(text[len(".. math:: "):], True)]

    @staticmethod
    def processMultiLineBlockExpression(strings: list[str], n: int) -> tuple[list[tuple[str, bool]], int]:
        substrings = strings[n+1:]
        group = []
        for s in substrings:
            if (not s) or (s == r"<br /><br />"):
                break
            group.append(s)

        group = [s.replace(r"<br />", "") for s in group]
        total = "".join(group)
        if total.startswith(r"<br />") and total.endswith(r"<br />"):
            result = total.split(r"<br />")[1]
        else:
            result = total.split(r"<br /><br />")[0]

        return [(result, True)], n + len(group) + 1

    @staticmethod
    def processInlineExpressions(text: str) -> list[tuple[str, bool]]:
        pattern = r"(:math:`.*?`)"
        substrings = re.split(pattern, text)
        scanned = []
        for s in substrings:
            if s.startswith(":math:"):
                expr = s[len(":math:`"):-1]
                scanned.append((expr, True))
            else:
                scanned.append((s, False))

        return scanned

    def scan(self) -> list[tuple[str, bool]]:
        # Use regex matching to find expressions
        pattern = r"(<br />.*?<br />)"
        substrings = re.split(pattern, self.raw_text)

        scanned = []
        for index, s in enumerate(substrings):
            if s:
                if self.containsMultiLineBlockExpression(s):
                    # Html is a multiline block expression
                    group, end = self.processMultiLineBlockExpression(substrings, index)
                    scanned.extend(group)
                    substrings[index:end] = [""] * (end - index)
                elif self.containsBlockExpression(s):
                    # Html substring contains a block expression
                    group = self.processBlockExpression(s)
                    scanned.extend(group)
                elif self.containsInlineExpressions(s):
                    # Html substring contains inline math expressions
                    group = self.processInlineExpressions(s)
                    scanned.extend(group)
                elif ":Example:" in s:
                    # We have reached the end of the section containing math expressions
                    rest = "".join(substrings[index:])
                    scanned.append((rest, False))
                    break
                else:
                    # Html substring contains plain text only
                    scanned.append((s, False))
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
    def from_cache(cls, key) -> str:
        return cls.cache[key]
