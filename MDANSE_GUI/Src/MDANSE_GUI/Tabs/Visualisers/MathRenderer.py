from __future__ import annotations

import base64
import io
import re

from matplotlib import pyplot as plt


class MathRenderer:
    # Cache mapping the raw LaTex expression to its rendered image form
    cache = {}

    # Ignore the following expression
    ignores = {r"\mathbf{q}": "q"}

    # Inline expression marker
    INLINE = r":math:"

    # Multiline block expression marker
    MULTILINE_BLOCK = r".. math::"

    # Line breaks used
    BREAK = r"<br\s*/?>"
    DOUBLE_BREAK = f"{BREAK}\s*{BREAK}"

    def __init__(self, text: str, dark: bool = False) -> None:
        self.raw_text = text
        self.dark = dark

    @staticmethod
    def replace_ignored(text: str) -> str:
        return MathRenderer.ignores[text]

    @staticmethod
    def ignore(text: str) -> bool:
        return text in MathRenderer.ignores

    @staticmethod
    def contains_multiline_block_expression(text: str) -> bool:
        return (
            re.search(f"<br />{MathRenderer.MULTILINE_BLOCK}<br />", text) is not None
        )

    @staticmethod
    def contains_block_expression(text: str) -> bool:
        return text.startswith(".. math:")

    @staticmethod
    def contains_inline_expressions(text: str) -> bool:
        return re.search(f"({MathRenderer.INLINE}`.*?`)", text) is not None

    def process_block_expression(self, substrings: list[str], index: int) -> None:
        expr = substrings[index].strip(f"{MathRenderer.MULTILINE_BLOCK}").strip("`")
        if not expr:
            match = re.search(r"<br\s*/?>(.*?)<br\s*/?>", substrings[index + 1])
            expr = match.group(1).strip()
        substrings[index] = self.render(expr, self.dark)
        substrings[index + 1] = ""

    def process_multiline_block_expression(
        self, strings: list[str], index: int
    ) -> None:
        substrings = strings[index + 1 :]
        group = []
        for s in substrings:
            if (not s) or re.fullmatch(self.DOUBLE_BREAK, s):
                break
            group.append(s)

        total = re.sub(self.BREAK, "", "".join(group))
        if total.startswith(r"<br />") and total.endswith(r"<br />"):
            result = total.split(r"<br />")[1]
        else:
            result = total.split(r"<br /><br />")[0]

        strings[index] = self.render(result, self.dark)
        expr_end = index + len(group) + 1
        discard = strings[index + 1 : expr_end]
        strings[index + 1 : expr_end] = [""] * len(discard)

    def process_inline_expressions(self, substrings: list[str], index: int) -> None:
        pattern = f"({MathRenderer.INLINE}`.*?`)"
        text = substrings[index]
        scanned = []
        matches = tuple(re.finditer(pattern, text))
        for i, match in enumerate(matches):
            last_span = matches[i - 1].span()
            expr_start, expr_end = match.span()
            plain_text = text[(0 if i < 1 else last_span[1]) : expr_start]
            scanned.append(self.process_plain_text(plain_text))
            span, expression = (
                match[0],
                match[1].strip(f"{MathRenderer.INLINE}").strip("`"),
            )
            rendered = self.render(expression, self.dark)
            scanned.append(rendered)
        substrings[index] = "".join(scanned)

    def process_plain_text(self, text: str) -> str:
        text = text.replace("\n", "<br>")
        return f'<span style="margin:0; padding:0;">{text}</span>'

    def scan(self) -> list[tuple[str, bool]]:
        # Use regex matching to find expressions
        pattern = r"(<br />.*?<br />)"
        substrings = re.split(pattern, self.raw_text)

        for index, s in enumerate(substrings):
            if s:
                if self.contains_multiline_block_expression(s):
                    # Html is a multiline block expression
                    self.process_multiline_block_expression(substrings, index)
                elif self.contains_block_expression(s):
                    # Html substring contains a block expression
                    self.process_block_expression(substrings, index)
                elif self.contains_inline_expressions(s):
                    # Html substring contains inline math expressions
                    self.process_inline_expressions(substrings, index)
                elif ":Example:" in s:
                    # Break - we don't process any info below this line
                    break
                else:
                    # This is plain text
                    substrings[index] = self.process_plain_text(s)

        return "".join(substrings)

    @staticmethod
    def mask(text: str) -> str:
        return f"${text}$"

    @staticmethod
    def render(expression: str, dark: bool = False) -> str:
        # Create a figure containing the rendered LaTex expression
        fig, ax = plt.subplots(figsize=(0.01, 0.01))
        ax.axis("off")
        fig.text(
            0,
            0,
            MathRenderer.mask(expression),
            fontsize=7,
            color="white" if dark else "black",
        )

        # Save the image as bytes
        buffer = io.BytesIO()
        plt.savefig(
            buffer,
            format="png",
            bbox_inches="tight",
            pad_inches=0.1,
            dpi=150,
            transparent=dark,
        )
        plt.close(fig)
        buffer.seek(0)
        image = base64.b64encode(buffer.read()).decode("utf-8")

        # Cache rendered expression
        MathRenderer.set_cache(expression, image)

        return (
            MathRenderer.embed_html(image)
            if len(expression) < 10
            else MathRenderer.embed_html_large(image)
        )

    @staticmethod
    def embed_html(image: str) -> str:
        return f'<span style="vertical-align:middle;"><img src="data:image/png;base64,{image}" style="height:1em; display:inline;"></span>'

    @staticmethod
    def embed_html_large(image: str) -> str:
        return f'<div style="text-align:left; margin:2px 0; padding:0;"><img src="data:image/png;base64,{image}" style="vertical-align:middle;"></div>'

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
