"""Post-processing: clean up raw OCR/ASR output into readable text."""
import re


def clean_text(raw_text: str) -> str:
    if not raw_text or not raw_text.strip():
        return ""

    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")

    # Collapse repeated horizontal whitespace and trim each line.
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Normalize punctuation spacing: no space before, one space after.
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"([,.;:!?])(?=[^\s\n])", r"\1 ", text)

    # Capitalize the first letter of each sentence / line.
    text = re.sub(
        r"(^|[.!?]\s+|\n)([a-z])",
        lambda match: match.group(1) + match.group(2).upper(),
        text,
    )

    return text.strip()
