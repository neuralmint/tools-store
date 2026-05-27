#!/usr/bin/env python3
"""
link_checker.py — Check URLs for validity using HTTP HEAD requests.

Reads URLs from a file or stdin, checks them with HEAD requests,
follows redirects, and reports status codes, response times, and broken links.

Usage:
    python link_checker.py urls.txt
    cat urls.txt | python link_checker.py
    python link_checker.py urls.txt --concurrent 10
    python link_checker.py urls.txt --json
    python link_checker.py urls.txt --concurrent --json
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed


def read_urls(source_path=None):
    """Read URLs from a file or stdin. Returns a list of (line_number, url)."""
    urls = []
    if source_path:
        if not os.path.exists(source_path):
            sys.exit(f"Error: File not found: {source_path}")
        with open(source_path) as f:
            for i, line in enumerate(f, 1):
                url = line.strip()
                if url and not url.startswith("#"):
                    urls.append((i, url))
    else:
        # Read from stdin
        for i, line in enumerate(sys.stdin, 1):
            url = line.strip()
            if url and not url.startswith("#"):
                urls.append((i, url))

    if not urls:
        sys.exit("Error: No URLs found in input")

    return urls


def check_url(line_num, url, timeout=10, max_redirects=10):
    """Check a single URL with a HEAD request, following redirects."""
    result = {
        "line": line_num,
        "url": url,
        "status_code": None,
        "status_text": "",
        "response_time_ms": None,
        "final_url": None,
        "redirect_chain": [],
        "error": None,
        "broken": False,
    }

    # Ensure URL has scheme
    original_url = url
    if not url.startswith(("http://", "https://", "ftp://")):
        url = "https://" + url
        result["url"] = url
        result["redirect_chain"].append(f"Added scheme: {url}")

    visited = set()
    redirect_count = 0
    start_time = time.time()

    while True:
        if url in visited:
            result["error"] = f"Redirect loop detected at: {url}"
            result["broken"] = True
            return result

        if redirect_count > max_redirects:
            result["error"] = f"Too many redirects (> {max_redirects})"
            result["broken"] = True
            return result

        visited.add(url)

        try:
            req = urllib.request.Request(url, method="HEAD")
            req.add_header("User-Agent", "link_checker/1.0 (URL validator)")

            with urllib.request.urlopen(req, timeout=timeout) as resp:
                elapsed_ms = round((time.time() - start_time) * 1000, 1)
                result["response_time_ms"] = elapsed_ms
                result["status_code"] = resp.status
                result["final_url"] = resp.url
                result["status_text"] = get_status_text(resp.status)

                # Check for redirect
                if 300 <= resp.status < 400:
                    redirect_target = resp.headers.get("Location")
                    if redirect_target:
                        result["redirect_chain"].append(f"{resp.status} -> {redirect_target}")
                        url = urllib.parse.urljoin(url, redirect_target)
                        redirect_count += 1
                        continue

                # Non-redirect response
                if resp.status >= 400:
                    result["broken"] = True
                return result

        except urllib.error.HTTPError as e:
            elapsed_ms = round((time.time() - start_time) * 1000, 1)
            result["response_time_ms"] = elapsed_ms
            result["status_code"] = e.code
            result["status_text"] = get_status_text(e.code)
            result["final_url"] = url

            # Follow redirect on HTTPError (sometimes 301/302 comes as an error)
            if 300 <= e.code < 400:
                redirect_target = e.headers.get("Location") if e.headers else None
                if redirect_target:
                    result["redirect_chain"].append(f"{e.code} -> {redirect_target}")
                    url = urllib.parse.urljoin(url, redirect_target)
                    redirect_count += 1
                    continue

            result["broken"] = True
            return result

        except urllib.error.URLError as e:
            elapsed_ms = round((time.time() - start_time) * 1000, 1)
            reason = str(e.reason) if e.reason else "Unknown error"
            result["response_time_ms"] = elapsed_ms
            result["error"] = f"URLError: {reason}"
            result["broken"] = True
            return result

        except OSError as e:
            elapsed_ms = round((time.time() - start_time) * 1000, 1)
            result["response_time_ms"] = elapsed_ms
            result["error"] = f"OSError: {e}"
            result["broken"] = True
            return result


def get_status_text(code):
    """Return a human-readable status text for HTTP status codes."""
    status_map = {
        200: "OK",
        201: "Created",
        204: "No Content",
        301: "Moved Permanently",
        302: "Found",
        303: "See Other",
        304: "Not Modified",
        307: "Temporary Redirect",
        308: "Permanent Redirect",
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        408: "Request Timeout",
        410: "Gone",
        429: "Too Many Requests",
        500: "Internal Server Error",
        502: "Bad Gateway",
        503: "Service Unavailable",
        504: "Gateway Timeout",
    }
    return status_map.get(code, f"HTTP {code}")


def format_result(result, json_output, show_all=False):
    """Format a single URL check result."""
    if json_output:
        return result

    status = result["status_code"] or "ERR"
    status_str = f"{status}" if result["status_code"] else "ERROR"

    time_str = f"{result['response_time_ms']:.0f}ms" if result["response_time_ms"] is not None else "---"

    if result["broken"]:
        icon = "❌"
    elif result["status_code"] and result["status_code"] < 400:
        icon = "✅"
    else:
        icon = "⚠️"

    line = f"{icon} [{status_str:>4}] [{time_str:>7}] Line {result['line']:>3}: {result['url']}"

    if result["final_url"] and result["final_url"] != result["url"]:
        line += f"\n      Redirected to: {result['final_url']}"

    if result["error"]:
        line += f"\n      Error: {result['error']}"

    return line


def main():
    parser = argparse.ArgumentParser(
        description="Check URLs for validity using HTTP HEAD requests.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  link_checker.py urls.txt\n"
            "  cat urls.txt | link_checker.py\n"
            "  link_checker.py urls.txt --concurrent 10\n"
            "  link_checker.py urls.txt --json\n"
            "  link_checker.py urls.txt --broken-only\n"
        ),
    )
    parser.add_argument("file", nargs="?", default=None, help="File containing URLs (one per line). Reads from stdin if omitted.")
    parser.add_argument("--concurrent", type=int, default=1, help="Number of parallel checks (default: 1)")
    parser.add_argument("--json", action="store_true", dest="json_flag", help="Output as JSON")
    parser.add_argument("--broken-only", action="store_true", help="Show only broken/invalid links")
    parser.add_argument("--timeout", type=int, default=10, help="Request timeout in seconds (default: 10)")
    args = parser.parse_args()

    # Check for stdin input (pipe mode)
    has_stdin_data = not sys.stdin.isatty()
    source = args.file

    if not source and not has_stdin_data:
        parser.print_help()
        print("\nError: Provide a URL file or pipe URLs via stdin")
        sys.exit(1)

    urls = read_urls(source)

    workers = max(1, args.concurrent)
    results = []

    print(f"Checking {len(urls)} URL(s) with {workers} worker(s)...\n", file=sys.stderr)

    if workers == 1:
        # Sequential
        for line_num, url in urls:
            result = check_url(line_num, url, timeout=args.timeout)
            results.append(result)
            if args.json_flag:
                continue
            line = format_result(result, False, args.broken_only)
            if not args.broken_only or result["broken"]:
                print(line)
    else:
        # Concurrent
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(check_url, line_num, url, timeout=args.timeout): (line_num, url)
                for line_num, url in urls
            }
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                if args.json_flag:
                    continue
                line = format_result(result, False, args.broken_only)
                if not args.broken_only or result["broken"]:
                    print(line)

    # Sort results by line number for consistent output
    results.sort(key=lambda r: r["line"])

    # Summarize
    total = len(results)
    broken = sum(1 for r in results if r["broken"])
    ok = total - broken
    avg_time = None
    times = [r["response_time_ms"] for r in results if r["response_time_ms"] is not None]
    if times:
        avg_time = round(sum(times) / len(times), 1)

    if args.json_flag:
        summary = {
            "total": total,
            "ok": ok,
            "broken": broken,
            "average_response_time_ms": avg_time,
            "results": results,
        }
        print(json.dumps(summary, indent=2))
        return

    # Print summary
    print(f"\n{'=' * 50}", file=sys.stderr)
    print(f"  Total URLs:  {total}", file=sys.stderr)
    print(f"  OK:          {ok}", file=sys.stderr)
    print(f"  Broken:      {broken}", file=sys.stderr)
    if avg_time is not None:
        print(f"  Avg time:    {avg_time}ms", file=sys.stderr)

    if broken > 0:
        print(f"\nBroken Links:", file=sys.stderr)
        for r in results:
            if r["broken"]:
                error_msg = r["error"] or f"HTTP {r['status_code']}"
                print(f"  Line {r['line']}: {r['url']}  ({error_msg})", file=sys.stderr)


if __name__ == "__main__":
    main()
