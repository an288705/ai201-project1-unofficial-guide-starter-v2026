#!/usr/bin/env python3
"""
The Unofficial Guide — the same pipeline, over HTTP.

    python serve.py                          run it locally on port 5000
    gunicorn serve:app                       run it the way a host runs it

Nothing new happens in this file. It is a wrapper: a request comes in, it
hands the question to `app.py::ask_pipeline` — the exact function the command
line uses — and hands the answer back as JSON. Retrieval, the relevance gate
and the grounded prompt all still live where they lived. If you change how
your system answers, you change it in those files and this one follows.

Two routes:

    POST /ask       {"question": "..."} in, the answer and its sources out
    GET  /health    is the service up, and is there an index to search

Why this exists: `app.py` runs once and exits, which is fine on your laptop
and impossible to deploy. A hosted service has to stay up and wait for
requests. This is the smallest thing that does that.

⚠️ There is deliberately no logging, no timing and no metrics in this file.
Unit 9 has you build the structured log yourself — the request line, the
timing field everyone skips, the whole instrument-before-you-deploy exercise.
Shipping a logger here would hand you the answer to that. Add yours in unit 9;
this file stays the bare shell until then.
"""

import os
import shutil
import subprocess
import asyncio
import re
import unicodedata

from flask import Flask, jsonify, request

import config

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
pi_executable = os.path.join(PROJECT_DIR, "node_modules", ".bin", "pi")
app = Flask(__name__)

MAX_QUESTION_LENGTH = 500

# Command substitution, command chaining, pipes and redirects. Ordinary
# questions never need these; apostrophes, quotes and "?" stay allowed.
SHELL_INJECTION = re.compile(r"\$\(|\$\{|`|;|&&|\|\||\||[<>]")


def sanitize_question(raw):
    """Clean a user question before it reaches the pi subprocess.

    Returns the cleaned string, or raises ValueError with a message that is
    safe to show the caller. The question is passed as an argv entry (never
    through a shell), so shell metacharacters are not the danger; the real
    ones are a question that pi parses as a command-line flag, control
    characters, and unbounded length.
    """
    if not isinstance(raw, str):
        raise ValueError("question must be a string")

    text = unicodedata.normalize("NFKC", raw)
    # Drop control/format characters (null bytes, escapes, zero-width, bidi
    # overrides); keep ordinary whitespace, then collapse it to single spaces.
    text = "".join(
        " " if ch.isspace() else ch
        for ch in text
        if ch.isspace() or unicodedata.category(ch) not in ("Cc", "Cf", "Cs")
    )
    text = re.sub(r"\s+", " ", text).strip()
    # A leading "-" would be read by pi as an option, not as the prompt.
    text = text.lstrip("-").strip()

    if not text:
        raise ValueError("question is empty after cleaning")
    if SHELL_INJECTION.search(text):
        raise ValueError("question contains characters that look like a shell command")
    if len(text) > MAX_QUESTION_LENGTH:
        raise ValueError(f"question is too long (max {MAX_QUESTION_LENGTH} characters)")
    return text


@app.get("/health")
def health():
    """Is the service up, and is there an index to search?

    Two different questions, and the second one is the one that bites. A
    freshly deployed service answers this route happily while every /ask
    returns "no index" — hosts give you no disk that survives a restart, so
    the index has to be built as part of getting the service up. Checking
    here means you find that out in one request instead of five.
    """
    from store import index_exists

    ready = index_exists(config.CORPUS)
    return jsonify(
        {
            "status": "ok",
            "corpus": config.CORPUS,
            "index_ready": ready,
            "detail": (
                "ready"
                if ready
                else "no index for this corpus — run `python app.py index`"
            ),
        }
    )


@app.post("/ask")
async def ask():
    """One question in, one grounded answer out.

    A refused question is a 200, not an error. The gate refusing is your
    system working — it is an answer, and the JSON says so with
    `"refused": true` so whatever calls this can tell the two apart.
    """
    from app import ask_pipeline

    payload = request.get_json(silent=True) or {}
    try:
        question = sanitize_question(payload.get("question") or "")
    except ValueError as exc:
        return (
            jsonify(
                {
                    "error": f"{exc}. Send JSON with a question in it, like "
                    '{"question": "is the housing lottery random?"}'
                }
            ),
            400,
        )

    try:
        #outcome = ask_pipeline(question, corpus=config.CORPUS)
        outcome = {
            "refused":"",
            "sources":"",
            "best_distance":"",
            "threshold":""
        }
        process = await asyncio.create_subprocess_exec(
                pi_executable, "-p", question,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            return jsonify({"error": stderr.decode().strip()}), 500
        answer = stdout.decode().strip()
    except Exception as exc:  # noqa: BLE001 — a reader gets this, not a traceback
        return jsonify({"error": f"{type(exc).__name__}: {exc}"}), 500

    return jsonify(
        {
            "question": question,
            "answer": answer,
            "refused": outcome["refused"],
            "sources": outcome["sources"],
            "best_distance": round(outcome["best_distance"], 4),
            "threshold": outcome["threshold"],
            "corpus": config.CORPUS,
        }
    )

@app.get("/debug/check-pi")
def check_pi():
    # pi is a local npm install (node_modules/.bin), not on PATH, so run it
    # through npx from the project directory.
    npx = shutil.which("npx")
    if not npx:
        return jsonify({"status": "not_found", "message": "'npx' is not on the server's PATH."}), 500
    try:
        result = subprocess.run(
            [npx, "pi", "--version"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return jsonify({"status": "error", "message": "'npx pi --version' timed out."}), 500
    if result.returncode == 0:
        return jsonify({"status": "found", "command": "npx pi --version", "version": result.stdout.strip()})
    return jsonify({"status": "error", "message": result.stderr.strip()}), 500


def main():
    # Hosts tell you which port to listen on through PORT, and they expect you
    # on 0.0.0.0. Binding 127.0.0.1 instead works perfectly on your laptop and
    # then answers nothing at all once deployed, because the host's router
    # can't reach a socket that only accepts connections from inside the
    # container. It is the single most common way a first deploy "succeeds"
    # and is unreachable.
    port = int(os.getenv("PORT", "5001"))

    # Debug mode reloads on save, which is handy, and prints a console that
    # runs arbitrary code, which is not something to leave switched on where
    # strangers can reach it. Off unless you ask for it.
    debug = os.getenv("AI201_DEBUG", "0") == "1"

    print(f"Serving The Unofficial Guide on http://localhost:{port}")
    print(f"Corpus: {config.CORPUS}    (Ctrl-C to stop)\n")
    print("Try it from another terminal:\n")
    print(f"  curl http://localhost:{port}/health")
    print(
        f"  curl -X POST http://localhost:{port}/ask \\\n"
        f"    -H 'Content-Type: application/json' \\\n"
        f"    -d '{{\"question\": \"is the housing lottery random?\"}}'\n"
    )

    app.run(host="0.0.0.0", port=port, debug=debug)


if __name__ == "__main__":
    main()
