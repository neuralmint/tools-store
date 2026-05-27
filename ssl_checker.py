#!/usr/bin/env python3
"""
ssl_checker.py — Check SSL/TLS certificates for domains.

Usage:
    python ssl_checker.py example.com
    python ssl_checker.py example.com --port 8443 --json
    python ssl_checker.py example.com --alert-days 14
"""

import argparse
import json
import ssl
import socket
import sys
from datetime import datetime, timezone


def check_cert(host, port, timeout):
    """Connect to host:port and retrieve the SSL certificate."""
    context = ssl.create_default_context()
    context.check_hostname = False
    # CERT_REQUIRED is the default; needed to actually retrieve the cert via getpeercert()

    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
                return cert
    except socket.gaierror as e:
        print(f"DNS resolution failed for {host}: {e}", file=sys.stderr)
        sys.exit(1)
    except socket.timeout:
        print(f"Connection timed out connecting to {host}:{port}", file=sys.stderr)
        sys.exit(1)
    except ConnectionRefusedError:
        print(f"Connection refused: {host}:{port}", file=sys.stderr)
        sys.exit(1)
    except ssl.SSLError as e:
        print(f"SSL error for {host}:{port} — {e}", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"OS error connecting to {host}:{port} — {e}", file=sys.stderr)
        sys.exit(1)


def parse_cert_date(date_str):
    """Parse an SSL cert date string (e.g. 'May 27 12:00:00 2026 GMT') to a datetime."""
    return datetime.strptime(date_str, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)


def color_text(text, color_code):
    """Wrap text in ANSI color codes."""
    return f"\033[{color_code}m{text}\033[0m"


def main():
    parser = argparse.ArgumentParser(
        description="SSL/TLS Certificate Checker — inspect and validate SSL certificates.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python ssl_checker.py example.com\n"
            "  python ssl_checker.py example.com --port 8443\n"
            "  python ssl_checker.py example.com --json\n"
            "  python ssl_checker.py example.com --alert-days 7\n"
        ),
    )
    parser.add_argument("host", help="Domain name to check")
    parser.add_argument("--port", type=int, default=443, help="Port to connect to (default: 443)")
    parser.add_argument(
        "--timeout", type=float, default=5.0, help="Connection timeout in seconds (default: 5.0)"
    )
    parser.add_argument(
        "--alert-days",
        type=int,
        default=30,
        help="Days threshold for expiry alerts (default: 30)",
    )
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    cert = check_cert(args.host, args.port, args.timeout)

    # Extract fields — cert tuples are ((key, value),) format
    def extract_rdn(rdn_seq):
        """Extract key=value pairs from OpenSSL RDN sequence."""
        result = {}
        for item in rdn_seq:
            # Each item is ((key, value),) or a tuple of (key, value) pairs
            if isinstance(item, tuple) and len(item) > 0:
                inner = item[0]
                if isinstance(inner, tuple) and len(inner) >= 2:
                    result[inner[0]] = inner[1]
        return result

    issuer = extract_rdn(cert.get("issuer", []))
    subject = extract_rdn(cert.get("subject", []))
    not_before = cert.get("notBefore", "")
    not_after = cert.get("notAfter", "")
    san_entries = cert.get("subjectAltName", [])
    sans = [san[1] for san in san_entries]
    serial = cert.get("serialNumber", "")
    version = cert.get("version", "")
    fingerprint = cert.get("fingerprint", {}).get("sha256", "")

    # Parse dates
    try:
        valid_from = parse_cert_date(not_before) if not_before else None
        valid_to = parse_cert_date(not_after) if not_after else None
    except (ValueError, TypeError):
        print("Could not parse certificate dates.", file=sys.stderr)
        valid_from = None
        valid_to = None

    days_remaining = None
    if valid_to:
        now = datetime.now(timezone.utc)
        delta = valid_to - now
        days_remaining = delta.days

    is_expiring = days_remaining is not None and days_remaining <= args.alert_days
    expired = days_remaining is not None and days_remaining < 0

    # Format issuer/subject as readable strings
    issuer_parts = [f"{k}={v}" for k, v in issuer.items()]
    subject_parts = [f"{k}={v}" for k, v in subject.items()]

    if args.json:
        output = {
            "host": args.host,
            "port": args.port,
            "issuer": issuer_parts,
            "subject": subject_parts,
            "valid_from": not_before,
            "valid_to": not_after,
            "days_remaining": days_remaining,
            "serial_number": serial,
            "version": version,
            "sans": sans,
            "expired": expired,
            "is_expiring": is_expiring,
            "alert_threshold_days": args.alert_days,
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"\n{' SSL Certificate Report ':=^60}")
        print(f"  Host:              {args.host}:{args.port}")
        print(f"  Issuer:            {', '.join(issuer_parts)}")
        print(f"  Subject:           {', '.join(subject_parts)}")
        print(f"  Valid From:        {not_before}")
        print(f"  Valid Until:       {not_after}")
        if days_remaining is not None:
            if expired:
                print(f"  Days Remaining:    {color_text('EXPIRED (' + str(abs(days_remaining)) + ' days ago)', '91')}")
            elif is_expiring:
                print(f"  Days Remaining:    {color_text(f'{days_remaining} days ⚠ EXPIRING SOON', '93')}")
            else:
                print(f"  Days Remaining:    {color_text(f'{days_remaining} days', '92')}")
        print(f"  Serial Number:     {serial}")
        if sans:
            print(f"  Subject Alt Names: {len(sans)} entries")
            for san in sans[:10]:
                print(f"    - {san}")
            if len(sans) > 10:
                print(f"    ... and {len(sans) - 10} more")
        print("=" * 60)

        if expired:
            print(color_text(f"  ❌ CERTIFICATE EXPIRED {abs(days_remaining)} days ago!", '91'))
        elif is_expiring:
            print(color_text(f"  ⚠ Certificate expires in {days_remaining} days (threshold: {args.alert_days} days)", '93'))
        else:
            print(color_text("  ✅ Certificate is valid and not expiring soon.", '92'))
        print()

    sys.exit(1 if expired or is_expiring else 0)


if __name__ == "__main__":
    main()
