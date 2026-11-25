"""
End-to-end check of the humanization pipeline against the real model.

Reports, for each sample: input/output length retention, the five preservation
scores, the composite score, repair iterations and wall-clock latency.
"""

import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from app.services.humanize_service import HumanizeService  # noqa: E402

SAMPLES = [
    (
        "academic",
        "It is important to note that the implementation of the utilization of modern "
        "methodology facilitates the optimization of comprehensive subsequent results. "
        "Furthermore, this approach leverages significant improvements in overall "
        "performance across the organization.",
        [],
    ),
    (
        "professional",
        "Acme Corporation reported revenue of 42 million dollars in 2026, a figure "
        "that exceeded analyst expectations. The company attributed the result to "
        "its expanded operations in Southeast Asia and to the adoption of automated "
        "inventory systems.",
        ["Acme Corporation", "42 million dollars", "2026"],
    ),
    (
        "casual",
        "The deployment took longer than expected, mostly because the team had to "
        "rewrite the authentication layer. By the time everything shipped, most of "
        "the original schedule was gone.",
        [],
    ),
]


async def main():
    service = HumanizeService()

    for tone, text, locked in SAMPLES:
        started = time.perf_counter()
        result = await service.humanize(text, tone=tone, locked_keywords=locked, tool="humanize")
        elapsed = time.perf_counter() - started

        in_words = len(text.split())
        out_words = len(result.text.split())
        p = result.preservation or {}

        print("=" * 78)
        print(f"TONE: {tone}   ({in_words} words in)")
        print("=" * 78)
        print("INPUT :", text)
        print()
        print("OUTPUT:", result.text)
        print()
        print(f"  length retention : {out_words}/{in_words} "
              f"= {out_words / max(1, in_words):.0%}")
        print(f"  composite score  : {p.get('composite_score')}")
        print(f"  sub-scores       : {p.get('scores')}")
        print(f"  missing entities : {p.get('missing_entities')}")
        print(f"  missing keywords : {p.get('missing_keywords')}")
        print(f"  iterations       : {result.iterations}  converged={result.converged}")
        print(f"  wall clock       : {elapsed:.2f}s")
        if result.warning:
            print(f"  warning          : {result.warning}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
