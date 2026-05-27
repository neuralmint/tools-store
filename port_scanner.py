#!/usr/bin/env python3
"""
port_scanner.py — TCP port scanner with service name lookup and JSON output.

Usage:
    python port_scanner.py <host> --ports <range>
    python port_scanner.py <host> --ports 1-1000 --timeout 2 --json
"""

import argparse
import json
import os
import socket
import sys
import time


SERVICES_FILE = "/etc/services"


def load_services():
    """Load service names from /etc/services into a dict: port->name."""
    svc = {}
    try:
        with open(SERVICES_FILE) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    port_proto = parts[1]
                    if "/" in port_proto:
                        port_str, proto = port_proto.split("/", 1)
                        if proto == "tcp":
                            try:
                                port = int(port_str)
                                if port not in svc:
                                    svc[port] = parts[0]
                            except ValueError:
                                pass
    except OSError:
        pass
    return svc


def scan_port(host, port, timeout):
    """Scan a single TCP port. Returns (port, state, service_name)."""
    service_name = SERVICES.get(port, "")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        result = sock.connect_ex((host, port))
        if result == 0:
            state = "open"
        else:
            state = "closed"
    except socket.gaierror:
        state = "filtered"
    except (socket.timeout, OSError):
        state = "filtered"
    finally:
        sock.close()
    return port, state, service_name


def parse_ports(port_arg):
    """Parse --ports argument (e.g. '1-1000' or '22,80,443' or '1-1000,8080')."""
    ports = []
    for part in port_arg.split(","):
        part = part.strip()
        if "-" in part:
            try:
                start, end = part.split("-", 1)
                ports.extend(range(int(start), int(end) + 1))
            except ValueError:
                print(f"Invalid port range: {part}", file=sys.stderr)
                sys.exit(1)
        else:
            try:
                ports.append(int(part))
            except ValueError:
                print(f"Invalid port: {part}", file=sys.stderr)
                sys.exit(1)
    return ports


def color_state(state):
    """Return color-coded state string."""
    if state == "open":
        return f"\033[92m{state}\033[0m"  # green
    elif state == "closed":
        return f"\033[91m{state}\033[0m"  # red
    else:
        return f"\033[93m{state}\033[0m"  # yellow


def main():
    parser = argparse.ArgumentParser(
        description="TCP Port Scanner — scan ports on a host with service name lookup.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python port_scanner.py scanme.nmap.org --ports 1-1000\n"
            "  python port_scanner.py scanme.nmap.org --ports 22,80,443 --timeout 3\n"
            "  python port_scanner.py scanme.nmap.org --ports 1-1024 --json\n"
        ),
    )
    parser.add_argument("host", help="Target hostname or IP address")
    parser.add_argument(
        "--ports",
        required=True,
        help="Port(s) or range to scan, e.g. 1-1000 or 22,80,443 or 1-1000,8080",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=1.0,
        help="Timeout per port in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )

    args = parser.parse_args()
    ports = parse_ports(args.ports)

    results = []
    open_count = 0
    closed_count = 0
    filtered_count = 0

    total = len(ports)

    if not args.json:
        print(f"Scanning {args.host} ({total} ports, timeout={args.timeout}s)")
        print("-" * 60)

    for i, port in enumerate(ports):
        if not args.json:
            progress = f"\r  [{i+1}/{total}] Scanning port {port}...  "
            print(progress, end="", flush=True)

        _port, state, svc = scan_port(args.host, port, args.timeout)
        entry = {"port": port, "state": state, "service": svc}

        if state == "open":
            open_count += 1
        elif state == "closed":
            closed_count += 1
        else:
            filtered_count += 1

        results.append(entry)

        if not args.json:
            svc_str = f" ({svc})" if svc else ""
            print(f"\r  Port {port:>5}/tcp  {color_state(state):>8}{svc_str}")

    if not args.json:
        print("-" * 60)
        print(
            f"Results: {open_count} open, {closed_count} closed, {filtered_count} filtered"
        )
    else:
        summary = {
            "host": args.host,
            "timeout": args.timeout,
            "total_ports": total,
            "results": results,
            "summary": {
                "open": open_count,
                "closed": closed_count,
                "filtered": filtered_count,
            },
        }
        print(json.dumps(summary, indent=2))

    sys.exit(0 if open_count == 0 else 0)


SERVICES = load_services()

if __name__ == "__main__":
    main()
