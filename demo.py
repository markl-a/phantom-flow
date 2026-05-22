#!/usr/bin/env python3
"""
demo.py — top-level "I cloned this repo, show me it works in 30 seconds" demo.

Designed to run with **zero setup**: no API keys, no Docker, no Postgres.
Falls back to a deterministic mock LLM by default. If you have
ANTHROPIC_API_KEY (or OPENAI_API_KEY) in your env, it'll use the real
provider for the final question-answering step so you can see actual
LLM output too.

Demonstrates the core "applied AI automation" loop end-to-end:

    1. Fetch a web page (real HTTP)
    2. Chunk it into RAG-friendly passages
    3. Embed (mocked — bag-of-words hash; deterministic)
    4. Retrieve top-k matches for a question
    5. Ask an LLM (mocked unless API key present)
    6. Print colorized result

Runs in ~10s with mock provider, ~25s with a real LLM call.

Usage:
    python demo.py                    # default URL, mock LLM
    python demo.py --use-llm          # real LLM if key in env
    python demo.py --url <X>          # different URL
    python demo.py --question "..."   # different question

Why this lives at the repo root: cloning Automation_with_Agent and not
finding any "press play" script is a dead-on-arrival recruiter
experience. Same reason phantom-mesh ships `phantom doctor` — first
impressions need a 30-second proof-of-life.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
import textwrap
import time
import urllib.request
from typing import List, Tuple

# ── ANSI colors (best-effort; degrade to plain on non-TTY) ───────────────────
def _c(code: str, text: str) -> str:
    if not sys.stdout.isatty():
        return text
    return f"\033[{code}m{text}\033[0m"

def cyan(s):    return _c("36", s)
def green(s):   return _c("32", s)
def yellow(s):  return _c("33", s)
def gray(s):    return _c("90", s)
def magenta(s): return _c("35", s)
def bold(s):    return _c("1",  s)


# ── Step 1: fetch URL ────────────────────────────────────────────────────────

def fetch_url(url: str, timeout: int = 10) -> str:
    """Plain HTTP GET, strip HTML to plaintext. No external deps."""
    print(f"{cyan('→')} fetching {gray(url)}")
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Automation_with_Agent/0.5 demo"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read().decode("utf-8", errors="ignore")
    # Aggressive but cheap HTML strip — sufficient for demo.
    body = re.sub(r"<script[^>]*>.*?</script>", " ", body, flags=re.DOTALL | re.IGNORECASE)
    body = re.sub(r"<style[^>]*>.*?</style>",   " ", body, flags=re.DOTALL | re.IGNORECASE)
    body = re.sub(r"<[^>]+>",                   " ", body)
    body = re.sub(r"\s+", " ", body).strip()
    print(f"  {green('✓')} {len(body):,} chars after HTML strip")
    return body


# ── Step 2: chunk ────────────────────────────────────────────────────────────

def chunk(text: str, chunk_chars: int = 600, overlap: int = 100) -> List[str]:
    """Sliding-window chunker. Cheap; not as good as semantic chunking
    but fine for a 30-second demo."""
    chunks: List[str] = []
    i = 0
    while i < len(text):
        chunks.append(text[i:i + chunk_chars])
        i += chunk_chars - overlap
    print(f"  {green('✓')} {len(chunks)} chunks of ~{chunk_chars} chars each")
    return chunks


# ── Step 3: mock embeddings (deterministic bag-of-words hash) ────────────────

def embed_mock(text: str, dim: int = 64) -> List[float]:
    """Deterministic 'embedding' for the demo. Each token contributes to
    one bucket via SHA-256 mod dim. Crude but enough to rank matches."""
    vec = [0.0] * dim
    for tok in re.findall(r"[A-Za-z0-9_']+", text.lower()):
        h = int(hashlib.sha256(tok.encode()).hexdigest(), 16)
        vec[h % dim] += 1.0
    # L2 normalise so cosine ≈ dot product.
    norm = sum(v * v for v in vec) ** 0.5 or 1.0
    return [v / norm for v in vec]


def cosine(a: List[float], b: List[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


# ── Step 4: retrieve top-k ───────────────────────────────────────────────────

def retrieve(question: str, chunks: List[str], k: int = 3) -> List[Tuple[float, str]]:
    qv = embed_mock(question)
    scored = [(cosine(qv, embed_mock(c)), c) for c in chunks]
    scored.sort(key=lambda x: -x[0])
    return scored[:k]


# ── Step 5: LLM call (real or mock) ──────────────────────────────────────────

def answer_mock(question: str, passages: List[str]) -> str:
    """Deterministic stub answer. The point of this demo isn't the LLM
    response quality — it's showing the orchestration shape works."""
    bullet = "\n  - ".join(p[:120].replace("\n", " ") + "…" for p in passages)
    return textwrap.dedent(
        f"""\
        [mock LLM] Based on the {len(passages)} retrieved passage(s), here's a
        synthesis answer to: "{question}"

        Key context found:
          - {bullet}

        Answer: This is a mock response for the demo. Set ANTHROPIC_API_KEY
        (or pass --use-llm with an OPENAI_API_KEY) to see the real LLM's
        synthesis. The orchestration plumbing — URL fetch → chunk → embed
        → retrieve → call — is verified working end-to-end above."""
    )


def answer_anthropic(question: str, passages: List[str]) -> str:
    """Real Anthropic call. Imported lazily so the demo runs without
    the SDK installed (it ships in requirements.txt but not in stdlib)."""
    import anthropic  # type: ignore

    client = anthropic.Anthropic()
    context = "\n\n---\n\n".join(passages)
    prompt = (
        f"Use the context below to answer the question. If the answer "
        f"isn't in the context, say so honestly.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}"
    )
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    return f"[Anthropic Haiku 4.5] {msg.content[0].text}"


def answer_openai(question: str, passages: List[str]) -> str:
    """Real OpenAI call. Same lazy-import pattern."""
    from openai import OpenAI  # type: ignore

    client = OpenAI()
    context = "\n\n---\n\n".join(passages)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=512,
        messages=[
            {"role": "system",
             "content": "Answer using only the provided context. If unknown, say so."},
            {"role": "user",
             "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ],
    )
    return f"[OpenAI gpt-4o-mini] {resp.choices[0].message.content}"


def call_llm(question: str, passages: List[str], *, force_real: bool) -> str:
    if force_real or os.environ.get("ANTHROPIC_API_KEY"):
        try:
            print(f"  {cyan('→')} calling {magenta('Anthropic')} (real LLM) …")
            return answer_anthropic(question, passages)
        except Exception as e:
            print(f"  {yellow('⚠')} Anthropic call failed ({e}); falling back to mock")
    if force_real or os.environ.get("OPENAI_API_KEY"):
        try:
            print(f"  {cyan('→')} calling {magenta('OpenAI')} (real LLM) …")
            return answer_openai(question, passages)
        except Exception as e:
            print(f"  {yellow('⚠')} OpenAI call failed ({e}); falling back to mock")
    print(f"  {gray('→ no API key in env; using deterministic mock LLM')}")
    return answer_mock(question, passages)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(
        description="Automation_with_Agent — 30-second proof-of-life demo",
    )
    p.add_argument(
        "--url",
        default="https://en.wikipedia.org/wiki/Retrieval-augmented_generation",
        help="Web page to fetch + RAG over (default: Wikipedia RAG article)",
    )
    p.add_argument(
        "--question",
        default="What problem does retrieval-augmented generation solve?",
        help="Question to ask of the fetched page",
    )
    p.add_argument(
        "--use-llm",
        action="store_true",
        help="Force a real LLM call even if key is missing (will error clearly)",
    )
    args = p.parse_args()

    print()
    print(bold(magenta("━━━ Automation_with_Agent demo ━━━")))
    print(gray("URL fetch → chunk → embed → retrieve → LLM"))
    print()

    t0 = time.time()
    print(bold("[1/5] Fetch"))
    text = fetch_url(args.url)
    print()

    print(bold("[2/5] Chunk"))
    chunks = chunk(text)
    print()

    print(bold("[3/5] Embed (mock — deterministic bag-of-words)"))
    print(f"  {green('✓')} {len(chunks)} embeddings × 64 dims")
    print()

    print(bold("[4/5] Retrieve top-3 for question"))
    print(f"  question: {cyan(args.question)}")
    matches = retrieve(args.question, chunks, k=3)
    for score, passage in matches:
        preview = passage[:100].replace("\n", " ")
        print(f"  {green('✓')} {gray(f'sim={score:.3f}')} {preview}…")
    print()

    print(bold("[5/5] Generate answer"))
    answer = call_llm(args.question, [p for _, p in matches], force_real=args.use_llm)
    print()
    print(yellow("┌─ Answer ─────────────────────────────────────────"))
    for line in answer.split("\n"):
        print(yellow("│ ") + line)
    print(yellow("└──────────────────────────────────────────────────"))
    print()
    print(f"{green('✓')} demo complete in {time.time() - t0:.1f}s")
    print()
    print(gray("Next: `python -m examples.level1_basics.01_simple_chat` for more,"))
    print(gray("      or `pip install -e .` to develop the framework locally."))


if __name__ == "__main__":
    main()
