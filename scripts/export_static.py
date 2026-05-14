"""Write public/quiz-data.json for Netlify static hosting (stdlib only)."""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from quiz_data import CURATED_QUESTIONS  # noqa: E402

OUT_DIR = os.path.join(ROOT, "public")
OUT_PATH = os.path.join(OUT_DIR, "quiz-data.json")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    payload = {"curated": CURATED_QUESTIONS, "hf_snippets": []}
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
