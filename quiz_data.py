"""Curated quiz items shared by Flask (local) and the static Netlify build."""

import html as html_module
import re

from quiz_pdf_questions import PDF_QUESTIONS


def _question_dedup_key(question_html: str) -> str:
    t = html_module.unescape(question_html)
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip().lower()


def _merge_pdf_questions(core: list, pdf_rows: list) -> list:
    seen = {_question_dedup_key(q["question"]) for q in core}
    out = list(core)
    for q in pdf_rows:
        k = _question_dedup_key(q["question"])
        if k in seen:
            continue
        seen.add(k)
        out.append(q)
    return out


_CORE_CURATED = [
    {
        "category": "Library Syntax (Pandas)",
        "question": "Which method is used to get a summary of the numerical columns in a Pandas DataFrame?",
        "options": [
            {"text": "df.summary()", "correct": False},
            {"text": "df.describe()", "correct": True},
            {"text": "df.info()", "correct": False},
            {"text": "df.stats()", "correct": False},
        ],
        "explanation": "<code>df.describe()</code> computes a summary of statistics pertaining to the DataFrame columns. <code>df.info()</code> is used for data types and memory usage.",
    },
    {
        "category": "Library Syntax (Requests)",
        "question": "How do you pass URL query parameters to a GET request using the <code>requests</code> library?",
        "options": [
            {"text": "requests.get(url, params={'key': 'value'})", "correct": True},
            {"text": "requests.get(url, data={'key': 'value'})", "correct": False},
            {"text": "requests.get(url, query={'key': 'value'})", "correct": False},
            {"text": "requests.get(url, json={'key': 'value'})", "correct": False},
        ],
        "explanation": "For HTTP GET requests, query string parameters are passed via the <code>params</code> keyword argument. <code>data</code> and <code>json</code> are for POST/PUT requests.",
    },
    {
        "category": "Bug Squashing",
        "question": "What is the error in the following code?<br><pre><code>def append_to(num, target=[]):\n    target.append(num)\n    return target</code></pre>",
        "options": [
            {"text": "SyntaxError: invalid syntax in function definition.", "correct": False},
            {
                "text": "Logic Error: It uses a mutable default argument, which will share the same list across multiple calls.",
                "correct": True,
            },
            {"text": "TypeError: append() takes no arguments.", "correct": False},
            {"text": "NameError: target is not defined.", "correct": False},
        ],
        "explanation": "In Python, default arguments are evaluated only <strong>once</strong> at function definition. Using a mutable default like an empty list <code>[]</code> means every subsequent call to the function without that argument will use and modify the exact same list.",
    },
    {
        "category": "Performance & Best Practices",
        "question": "Which of the following is the most 'Pythonic' and efficient way to combine a list of strings into a single string?",
        "options": [
            {"text": "Using a for loop to concatenate with the + operator.", "correct": False},
            {"text": "Using the .join() method: <code>''.join(my_list)</code>", "correct": True},
            {"text": "Using the map() function.", "correct": False},
            {"text": "Using string formatting: <code>f'{my_list}'</code>", "correct": False},
        ],
        "explanation": "Strings are immutable in Python. Using the <code>+</code> operator in a loop creates a new string object in memory every single time, which is very slow. <code>''.join()</code> calculates the required memory once and builds the string efficiently.",
    },
    {
        "category": "OOP Concepts",
        "question": "What does the <code>@staticmethod</code> decorator do in a Python class?",
        "options": [
            {"text": "It defines a method that takes the class (cls) as its first implicit argument.", "correct": False},
            {"text": "It prevents the method from being overridden by subclasses.", "correct": False},
            {"text": "It defines a method that does not receive an implicit first argument (neither self nor cls).", "correct": True},
            {"text": "It automatically caches the results of the method.", "correct": False},
        ],
        "explanation": "A <code>@staticmethod</code> behaves like a plain function that happens to live inside a class's namespace. It doesn't modify object state (no <code>self</code>) or class state (no <code>cls</code>).",
    },
    {
        "category": "Standard Library (Collections)",
        "question": "If you need a dictionary that remembers the order in which items were inserted, which object should you use (especially in Python versions older than 3.7)?",
        "options": [
            {"text": "collections.defaultdict", "correct": False},
            {"text": "collections.OrderedDict", "correct": True},
            {"text": "collections.Counter", "correct": False},
            {"text": "dict", "correct": False},
        ],
        "explanation": "<code>OrderedDict</code> was specifically designed to remember insertion order. While standard <code>dict</code> objects maintain insertion order as an implementation detail starting in Python 3.7, <code>OrderedDict</code> still offers unique features like equality testing that considers order.",
    },
    {
        "category": "Core Concepts",
        "question": "What does the <code>yield</code> keyword do in Python?",
        "options": [
            {"text": "It completely stops the execution of a function.", "correct": False},
            {"text": "It pauses function execution and sends a value back, turning the function into a generator.", "correct": True},
            {"text": "It imports a specific module.", "correct": False},
            {"text": "It forces a multi-threading lock to release.", "correct": False},
        ],
        "explanation": "<code>yield</code> is used to create a generator. Unlike <code>return</code>, which exits a function entirely, <code>yield</code> pauses the function saving all its states, and later continues from there on successive calls.",
    },
    {
        "category": "Data Structures",
        "question": "What is the average time complexity for searching for a specific item in a Python <code>set</code>?",
        "options": [
            {"text": "O(N)", "correct": False},
            {"text": "O(log N)", "correct": False},
            {"text": "O(1)", "correct": True},
            {"text": "O(N^2)", "correct": False},
        ],
        "explanation": "Python sets are implemented as hash tables. Because of this, checking if an item exists in a set (<code>if x in my_set</code>) takes constant time, O(1), making it much faster than searching a list O(N).",
    },
    {
        "category": "Input/Output",
        "question": "What is the output of the following <code>print()</code> statement?<br><pre><code>print('Apples', 'Bananas', 'Cherries', sep='|', end='!')</code></pre>",
        "options": [
            {"text": "Apples Bananas Cherries|!", "correct": False},
            {"text": "Apples|Bananas|Cherries!", "correct": True},
            {"text": "Apples|Bananas|Cherries\n!", "correct": False},
            {"text": "SyntaxError: invalid keyword argument", "correct": False},
        ],
        "explanation": "The <code>sep</code> parameter dictates what string is placed <i>between</i> the items being printed (a pipe <code>|</code> in this case). The <code>end</code> parameter dictates what is printed at the very end of the statement instead of the default newline character (an exclamation mark <code>!</code> here).",
    },
    {
        "category": "Input/Output",
        "question": "When you use the built-in <code>input()</code> function to get a number from a user, what data type does it return by default?",
        "options": [
            {"text": "An integer (int)", "correct": False},
            {"text": "A float if it has decimals, otherwise an int", "correct": False},
            {"text": "A string (str)", "correct": True},
            {"text": "NoneType", "correct": False},
        ],
        "explanation": "The <code>input()</code> function <strong>always</strong> returns a string, regardless of what the user types. If you need to do math with the input, you must explicitly cast it, like this: <code>int(input('Enter a number: '))</code>.",
    },
    {
        "category": "Input/Output",
        "question": "Which is the safest and most 'Pythonic' way to open and read a text file?",
        "options": [
            {"text": "<pre><code>file = open('data.txt', 'r')\ndata = file.read()\nfile.close()</code></pre>", "correct": False},
            {"text": "<pre><code>with open('data.txt', 'r') as file:\n    data = file.read()</code></pre>", "correct": True},
            {"text": "<pre><code>data = read('data.txt')</code></pre>", "correct": False},
            {"text": "<pre><code>file = open('data.txt')\ndata = file.read()</code></pre>", "correct": False},
        ],
        "explanation": "Using a <strong>context manager</strong> (the <code>with</code> statement) is best practice. It guarantees that the file will be properly closed after the indented block finishes executing, even if an error occurs while reading the file.",
    },
    {
        "category": "Data Types",
        "question": "Which of the following data types is <strong>mutable</strong> (can be changed in-place)?",
        "options": [
            {"text": "Tuple", "correct": False},
            {"text": "String", "correct": False},
            {"text": "Dictionary", "correct": True},
            {"text": "Integer", "correct": False},
        ],
        "explanation": "Dictionaries and Lists are mutable, meaning you can add, remove, or change elements after they are created. Strings, Tuples, and numeric types (Integers, Floats) are immutable; any 'change' actually creates a brand new object in memory.",
    },
    {
        "category": "Data Types",
        "question": "What is the result of checking the type of a standard Python dictionary?<br><pre><code>type({'name': 'Alice', 'age': 30})</code></pre>",
        "options": [
            {"text": "&lt;class 'dict'&gt;", "correct": True},
            {"text": "&lt;class 'dictionary'&gt;", "correct": False},
            {"text": "&lt;class 'json'&gt;", "correct": False},
            {"text": "&lt;class 'set'&gt;", "correct": False},
        ],
        "explanation": "In Python, the dictionary data type is formally known and identified by the class <code>dict</code>. While it looks like JSON, JSON is a text format, not a built-in Python data structure.",
    },
    {
        "category": "Data Types",
        "question": "What happens when you execute this code involving floating-point numbers?<br><pre><code>print(0.1 + 0.2 == 0.3)</code></pre>",
        "options": [
            {"text": "True", "correct": False},
            {"text": "False", "correct": True},
            {"text": "SyntaxError", "correct": False},
            {"text": "None", "correct": False},
        ],
        "explanation": "Because of how computers store floating-point numbers in binary representation, <code>0.1 + 0.2</code> actually results in <code>0.30000000000000004</code>. Therefore, the equality check returns <code>False</code>. You should use the <code>math.isclose()</code> function when comparing floats.",
    },
]

CURATED_QUESTIONS = _merge_pdf_questions(_CORE_CURATED, PDF_QUESTIONS)
