from flask import Flask, jsonify, send_from_directory, session
from datasets import load_dataset
import random
import html
import os

from quiz_data import CURATED_QUESTIONS

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-quiz-secret-change-in-production")
_ROOT = os.path.dirname(os.path.abspath(__file__))
_PUBLIC = os.path.join(_ROOT, "public")

# ==========================================
# 1. LOAD HUGGING FACE DATASET (For 'Predicting Output')
# ==========================================
print("Loading Hugging Face dataset into memory... (This might take a minute)")
try:
    raw_dataset = load_dataset("jtatman/python-code-dataset-500k", split="train")
    hf_quiz_pool = raw_dataset.shuffle(seed=42).select(range(10000))
    print("Dataset loaded successfully!")
except Exception as e:
    print(f"Error loading dataset: {e}")
    hf_quiz_pool = []


def _pop_curated_index():
    n = len(CURATED_QUESTIONS)
    deck = session.get("cur_deck") or []
    if not deck:
        last = session.get("last_cur")
        guard = 0
        while True:
            deck = list(range(n))
            random.shuffle(deck)
            guard += 1
            if n <= 1 or last is None or deck[-1] != last or guard > 50:
                break
        session["cur_deck"] = deck
    idx = deck.pop()
    session["cur_deck"] = deck
    session["last_cur"] = idx
    session.modified = True
    return idx


def _pop_hf_index():
    n = len(hf_quiz_pool)
    key = "hf_deck"
    deck = session.get(key) or []
    if not deck:
        last = session.get("last_hf")
        k = min(150, n) if n else 0
        guard = 0
        while True:
            deck = random.sample(range(n), k) if k else []
            guard += 1
            if k <= 1 or last is None or not deck or deck[-1] != last or guard > 50:
                break
        session[key] = deck
    idx = deck.pop()
    session[key] = deck
    session["last_hf"] = idx
    session.modified = True
    return idx


# ==========================================
# 2. ROUTES
# ==========================================
@app.route("/")
def home():
    return send_from_directory(_PUBLIC, "index.html")


@app.route("/quiz-data.json")
def quiz_data_json():
    return send_from_directory(_PUBLIC, "quiz-data.json")


@app.route("/api/question")
def get_question():
    question_type = random.choice(["hf_snippet", "curated"])

    if not hf_quiz_pool:
        question_type = "curated"

    if question_type == "curated":
        q_data = CURATED_QUESTIONS[_pop_curated_index()]
        opts = list(q_data["options"])
        random.shuffle(opts)
        q_data_copy = {**q_data, "options": opts}
        q_data_copy["question"] = (
            f"<span style='color: #4f46e5; font-size: 0.8em; text-transform: uppercase; "
            f"font-weight: 800; letter-spacing: 0.5px;'>{q_data['category']}</span><br>{q_data['question']}"
        )
        return jsonify(q_data_copy)

    row = hf_quiz_pool[_pop_hf_index()]

    code_snippet = row.get("text", "") or row.get("code", "") or row.get("content", "")
    if not code_snippet and len(row) > 0:
        code_snippet = str(list(row.values())[0])

    if len(code_snippet) > 400:
        code_snippet = code_snippet[:400] + "\n\n... [truncated] ..."

    safe_code = html.escape(code_snippet)

    question_data = {
        "question": (
            f"<span style='color: #4f46e5; font-size: 0.8em; text-transform: uppercase; "
            f"font-weight: 800; letter-spacing: 0.5px;'>Predicting Output / Code Analysis</span><br>"
            f"Analyze the following real-world Python snippet. What is likely true about this code?<br>"
            f"<pre><code>{safe_code}</code></pre>"
        ),
        "options": [
            {"text": "It contains valid Python syntax and functions as written.", "correct": True},
            {"text": "It contains a critical IndentationError.", "correct": False},
            {"text": "It lacks required imports to run.", "correct": False},
            {"text": "It will cause an infinite loop.", "correct": False},
        ],
        "explanation": (
            "This snippet is pulled directly from the <code>jtatman/python-code-dataset-500k</code> "
            "Hugging Face dataset, which consists of valid Python code scraped from GitHub repositories."
        ),
    }

    random.shuffle(question_data["options"])
    return jsonify(question_data)


if __name__ == "__main__":
    print("Starting server... Open http://127.0.0.1:5000 in your browser!")
    app.run(debug=True, port=5000)
