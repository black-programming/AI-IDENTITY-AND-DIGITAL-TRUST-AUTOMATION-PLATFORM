#!/usr/bin/env python3
"""CLI utility for executing release smoke tests against any deployment URL."""

import argparse
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from tests.ci.test_staging_smoke import run_staging_smoke_tests


def main():
    parser = argparse.ArgumentParser(description="Platform Deployment Smoke Test Runner")
    parser.add_argument("--environment", default="staging", choices=["development", "staging", "production"])
    parser.add_argument("--target-url", default="http://127.0.0.1:8000", help="Root URL of deployment target")
    args = parser.parse_args()

    print(f"[*] Initiating Smoke Test Suite against: {args.target_url} (Env: {args.environment.upper()})")
    success = run_staging_smoke_tests(base_url=args.target_url)
    if success:
        print("[+] All deployment smoke gates passed successfully.")
        return 0
    else:
        print("[!] Smoke tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
