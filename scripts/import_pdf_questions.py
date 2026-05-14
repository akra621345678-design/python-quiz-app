"""
Extract MCQs from PDFs in ../quiz pdf/ and write quiz_pdf_questions.py.
Run from repo root: python scripts/import_pdf_questions.py

Supports:
  - Newline options: N. question... / opt1 / opt2 / opt3 / opt4 / Correct Answer: / Reasoning:
  - Inline A-D: N. question... A. ... B. ... C. ... D. ... Correct Answer: ... Reasoning: ...
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:
    print("Install pypdf: pip install pypdf", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "quiz pdf"
OUT = ROOT / "quiz_pdf_questions.py"

# Split document into one block per leading "123. " question (multiline-safe)
BLOCK_START = re.compile(r"(?m)(?=^\s*\d+\.\s+)")

# Trailing PDF junk: lines that are only A./B./C./D. markers
_TRAIL_JUNK = re.compile(r"(?m)(?:^\s*[ABCDabcd][.\)]?\s*)+$")

# Full-text inline MCQ stream (python quiz.pdf): requires uppercase A.–D. labels
INLINE_MCQ = re.compile(
    r"(?P<num>\d+)\.\s+(?P<q>.+?)\s+A\.\s+(?P<a>.+?)\s+B\.\s+(?P<b>.+?)\s+C\.\s+(?P<c>.+?)\s+D\.\s+(?P<d>.+?)"
    r"\s+Correct\s+Answer:\s*(?P<ans>.+?)\s+Reasoning:\s*(?P<reason>.*?)(?=\s+\d+\.\s+.+?\s+A\.\s+|\Z)",
    re.DOTALL,
)


def normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def strip_wrapping_quotes(s: str) -> str:
    s = s.strip()
    if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
        return s[1:-1].strip()
    return s


def norm_key(s: str) -> str:
    return normalize_ws(strip_wrapping_quotes(html.unescape(s))).lower()


def extract_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    parts: list[str] = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            parts.append(t)
    return "\n".join(parts)


def split_numbered_blocks(raw: str) -> list[str]:
    raw = raw.replace("\r", "\n")
    raw = re.sub(r"(\S)(Correct\s+Answer:)", r"\1 \2", raw, flags=re.I)
    chunks = BLOCK_START.split(raw)
    blocks: list[str] = []
    for ch in chunks:
        ch = ch.strip()
        if not ch:
            continue
        if re.match(r"^\s*\d+\.\s+", ch, re.M):
            blocks.append(ch)
    return blocks


def trim_block_trailer(block: str) -> str:
    block = block.rstrip()
    block = _TRAIL_JUNK.sub("", block)
    return block.rstrip()


def parse_newline_block(block: str) -> dict | None:
    """Four option lines immediately before 'Correct Answer:'; question is all lines above them."""
    block = trim_block_trailer(block)
    lines = [ln.rstrip() for ln in block.split("\n")]
    ca_idx = None
    for i, ln in enumerate(lines):
        if re.match(r"^\s*Correct\s+Answer:\s*", ln, re.I):
            ca_idx = i
            break
    if ca_idx is None or ca_idx < 4:
        return None

    ans_m = re.match(r"^\s*Correct\s+Answer:\s*(.+)\s*$", lines[ca_idx], re.I)
    if not ans_m:
        return None
    ans = ans_m.group(1).strip()

    opts = [
        lines[ca_idx - 4].strip(),
        lines[ca_idx - 3].strip(),
        lines[ca_idx - 2].strip(),
        lines[ca_idx - 1].strip(),
    ]
    if any(not o for o in opts):
        return None
    if any(re.match(r"^\d+\.\s", o) for o in opts):
        return None
    if all(len(o) <= 3 and re.match(r"^[ABCDabcd][.\)]?\s*$", o) for o in opts):
        return None

    reason_lines: list[str] = []
    started = False
    for j in range(ca_idx + 1, len(lines)):
        ln = lines[j]
        if not started and re.match(r"^\s*Reasoning:\s*", ln, re.I):
            started = True
            reason_lines.append(re.sub(r"^\s*Reasoning:\s*", "", ln, flags=re.I))
        elif started:
            if re.match(r"^\s*\d+\.\s+", ln):
                break
            if re.match(r"^\s*[ABCDabcd][.\)]?\s*$", ln) and j > ca_idx + 3:
                break
            reason_lines.append(ln)
    reason = "\n".join(reason_lines).strip()
    if not reason:
        return None

    q_lines = lines[: ca_idx - 4]
    if not q_lines:
        return None
    first = re.sub(r"^\s*\d+\.\s*", "", q_lines[0])
    qtext = "\n".join([first] + q_lines[1:]).strip()
    if not qtext or len(qtext) > 4000:
        return None

    return {"question": qtext, "options": opts, "answer": ans, "reason": reason}


def parse_labeled_block(block: str) -> dict | None:
    """Single-line style: ... A. ... B. ... C. ... D. ... Correct Answer: ... Reasoning: ..."""
    block = trim_block_trailer(block)
    b = re.sub(r"\s+", " ", block.strip())
    m = re.match(
        r"^\d+\.\s*(.+?)\s+A\.\s*(.+?)\s+B\.\s*(.+?)\s+C\.\s*(.+?)\s+D\.\s*(.+?)\s+"
        r"(?i:Correct\s+Answer:)\s*(.+?)\s+(?i:Reasoning:)\s*(.+)$",
        b,
    )
    if not m:
        return None
    qtext, a, bb, c, d, ans, reason = m.groups()
    qtext = qtext.strip()
    opts = [a.strip(), bb.strip(), c.strip(), d.strip()]
    if any(len(o) < 1 for o in opts):
        return None
    return {"question": qtext, "options": opts, "answer": ans.strip(), "reason": reason.strip()}


def row_from_parsed(parsed: dict, source: str) -> dict | None:
    qtext = parsed["question"]
    opts = parsed["options"]
    ans = normalize_ws(parsed["answer"])
    reason = parsed["reason"]

    ans_key = norm_key(ans)
    correct_idx = None
    for i, o in enumerate(opts):
        o_n = norm_key(o)
        if o_n == ans_key:
            correct_idx = i
            break
    if correct_idx is None:
        for i, o in enumerate(opts):
            ok, ak = norm_key(o), ans_key
            if ak and (ak in ok or ok in ak):
                correct_idx = i
                break
    if correct_idx is None:
        return None

    safe_q = html.escape(qtext).replace("\n", "<br>")
    safe_exp = html.escape(normalize_ws(reason)) if reason else ""
    opt_objs = [{"text": html.escape(normalize_ws(o)), "correct": (i == correct_idx)} for i, o in enumerate(opts)]

    return {
        "category": f"Imported ({source})",
        "question": safe_q,
        "options": opt_objs,
        "explanation": safe_exp,
    }


def _looks_labeled_inline(block: str) -> bool:
    """True if this block uses uppercase A./B./C./D. labels (single-line quiz style)."""
    m = re.search(r"Correct\s+Answer:", block, re.I)
    if not m:
        return False
    head = block[: m.start()]
    return bool(re.search(r"\bA\.\s+\S", head))


def valid_inline_match(m: re.Match) -> bool:
    """Reject inline regex hits where 'A.' came from PDF junk, not real options."""
    q = m.group("q")
    if re.search(r"(?m)^\d+\.\s+", q):
        return False
    for g in ("a", "b", "c", "d"):
        t = m.group(g).strip()
        if "Correct Answer" in t or len(t) > 800 or len(t) < 1:
            return False
        compact = re.sub(r"\s+", "", t)
        if re.fullmatch(r"(?:[A-D]\.)+", compact, re.I):
            return False
    return True


def _parsed_from_inline_match(m: re.Match) -> dict:
    return {
        "question": normalize_ws(m.group("q")),
        "options": [normalize_ws(m.group(x)) for x in ("a", "b", "c", "d")],
        "answer": normalize_ws(m.group("ans")),
        "reason": normalize_ws(m.group("reason")),
    }


INLINE_MIN_VALID = 50


def parse_questions(raw: str, source: str) -> list[dict]:
    raw = raw.replace("\r", "\n")
    raw = re.sub(r"(\S)(Correct\s+Answer:)", r"\1 \2", raw, flags=re.I)

    out: list[dict] = []
    seen_q: set[str] = set()

    inline_hits = [m for m in INLINE_MCQ.finditer(raw) if valid_inline_match(m)]
    if len(inline_hits) >= INLINE_MIN_VALID:
        for m in inline_hits:
            parsed = _parsed_from_inline_match(m)
            row = row_from_parsed(parsed, source)
            if row is None:
                continue
            q_key = norm_key(re.sub(r"<br\s*/?>", " ", row["question"]))
            if q_key in seen_q:
                continue
            seen_q.add(q_key)
            out.append(row)
        return out

    for block in split_numbered_blocks(raw):
        if _looks_labeled_inline(block):
            parsed = parse_labeled_block(block)
            if parsed is None:
                parsed = parse_newline_block(block)
        else:
            parsed = parse_newline_block(block)
            if parsed is None:
                parsed = parse_labeled_block(block)
        if parsed is None:
            continue

        row = row_from_parsed(parsed, source)
        if row is None:
            continue

        q_key = norm_key(re.sub(r"<br\s*/?>", " ", row["question"]))
        if q_key in seen_q:
            continue
        seen_q.add(q_key)
        out.append(row)

    return out


def main():
    if not PDF_DIR.is_dir():
        print(f"Missing folder: {PDF_DIR}", file=sys.stderr)
        sys.exit(1)

    pdf_files = sorted(PDF_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDFs in {PDF_DIR}", file=sys.stderr)
        sys.exit(1)

    all_rows: list[dict] = []
    seen_global: set[str] = set()

    for pdf in pdf_files:
        label = pdf.name
        try:
            text = extract_pdf_text(pdf)
        except Exception as e:
            print(f"Skip {label}: {e}", file=sys.stderr)
            continue
        rows = parse_questions(text, label)
        for r in rows:
            k = norm_key(re.sub(r"<br\s*/?>", " ", r["question"]))
            if k in seen_global:
                continue
            seen_global.add(k)
            all_rows.append(r)
        print(f"{label}: parsed {len(rows)} (unique so far: {len(all_rows)})")

    header = (
        "# Auto-generated by scripts/import_pdf_questions.py — do not edit by hand.\n"
        "# Re-run: python scripts/import_pdf_questions.py\n\n"
        "PDF_QUESTIONS = "
    )
    body = repr(all_rows)
    OUT.write_text(header + body + "\n", encoding="utf-8")
    print(f"Wrote {len(all_rows)} questions to {OUT}")


if __name__ == "__main__":
    main()
