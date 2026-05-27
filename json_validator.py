#!/usr/bin/env python3
"""
json_validator.py — Validate and pretty-print JSON files.

Accepts file path(s) or stdin. Color-coded pass/fail output.

Usage:
    python json_validator.py data.json
    python json_validator.py file1.json file2.json --compact --sort-keys
    python json_validator.py --check-only config.json
    cat data.json | python json_validator.py
"""

import argparse
import json
import sys


COLOR_RED = "\033[91m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_CYAN = "\033[96m"
COLOR_BOLD = "\033[1m"
COLOR_RESET = "\033[0m"


def colorize(text, color, bold=False):
    """Apply ANSI color codes."""
    bold_code = COLOR_BOLD if bold else ""
    return f"{bold_code}{color}{text}{COLOR_RESET}"


def process_content(content, source_label, compact, sort_keys, check_only):
    """Validate and optionally pretty-print JSON content."""
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"{colorize('✗ FAIL', COLOR_RED, bold=True)}  {source_label}")
        print(f"  {colorize('Error:', COLOR_RED)} {e}")
        return False, None

    if check_only:
        print(f"{colorize('✓ PASS', COLOR_GREEN, bold=True)}  {source_label}")
        return True, None

    if compact:
        output = json.dumps(data, separators=(",", ":"), sort_keys=sort_keys)
    else:
        output = json.dumps(data, indent=2, sort_keys=sort_keys)

    print(f"{colorize('✓ PASS', COLOR_GREEN, bold=True)}  {source_label}")
    print(output)
    return True, data


def main():
    parser = argparse.ArgumentParser(
        description="Validate and pretty-print JSON files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python json_validator.py data.json\n"
            "  python json_validator.py file1.json file2.json --compact\n"
            "  python json_validator.py config.json --check-only\n"
            "  echo '{\"a\":1}' | python json_validator.py --sort-keys\n"
        ),
    )
    parser.add_argument("files", nargs="*", metavar="FILE", help="JSON file(s) to validate")
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Output minified JSON (no whitespace)",
    )
    parser.add_argument(
        "--sort-keys",
        action="store_true",
        help="Sort object keys alphabetically",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only validate (exit code), no pretty-print output",
    )

    args = parser.parse_args()

    all_passed = True
    results = []

    # Process files
    for filepath in args.files:
        try:
            with open(filepath, "r") as f:
                content = f.read()
        except OSError as e:
            print(f"{colorize('✗ FAIL', COLOR_RED, bold=True)}  {filepath}")
            print(f"  {colorize('Error:', COLOR_RED)} {e}")
            all_passed = False
            results.append(False)
            continue

        passed, _ = process_content(content, filepath, args.compact, args.sort_keys, args.check_only)
        if not passed:
            all_passed = False
        results.append(passed)

        if passed and args.check_only:
            pass  # already printed by process_content

    # Process stdin if no files given or if stdin has data
    if not args.files:
        if not sys.stdin.isatty():
            content = sys.stdin.read()
            passed, _ = process_content(content, "<stdin>", args.compact, args.sort_keys, args.check_only)
            if not passed:
                all_passed = False
            results.append(passed)
        else:
            # No files, no piped input — show help
            parser.print_help()
            print("\nNo input provided. Pipe JSON data or specify file(s).", file=sys.stderr)
            sys.exit(1)

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
