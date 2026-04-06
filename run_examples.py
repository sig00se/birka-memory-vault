#!/usr/bin/env python3
"""
Quick smoke test: run all examples in sequence.
Requires an empty SQLite DB or DATABASE_URL set.
"""
import asyncio
import os
import sys

EXAMPLES = [
    "examples.basic_indexing",
    "examples.mission_tracking",
]

async def run_all():
    for mod_name in EXAMPLES:
        print(f"\n=== Running {mod_name} ===")
        try:
            mod = __import__(mod_name, fromlist=["main"])
            await mod.main()
            print(f"✓ {mod_name} succeeded")
        except Exception as e:
            print(f"✗ {mod_name} failed:", e)
            raise

if __name__ == "__main__":
    # Ensure a clean DB for tests
    if os.path.exists("birka_memory.db"):
        os.remove("birka_memory.db")
    asyncio.run(run_all())