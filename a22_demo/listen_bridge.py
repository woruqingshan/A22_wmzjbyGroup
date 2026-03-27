#!/usr/bin/env python3
import argparse
import json
import time
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Follow edge-backend bridge traces and print backend <-> remote messages."
    )
    parser.add_argument(
        "--log-dir",
        default="/home/siyuen/docker_ws/A22/logs/edge-backend",
        help="Directory containing edge-backend bridge trace files.",
    )
    parser.add_argument(
        "--pattern",
        default="edge-backend-bridge-*.jsonl",
        help="Glob pattern used to find bridge trace files.",
    )
    parser.add_argument(
        "--from-start",
        action="store_true",
        help="Read the latest trace file from the beginning instead of following only new records.",
    )
    return parser.parse_args()


def find_latest_trace(log_dir: Path, pattern: str) -> Path | None:
    candidates = sorted(log_dir.glob(pattern), key=lambda path: path.stat().st_mtime)
    if not candidates:
        return None
    return candidates[-1]


def render_record(record: dict) -> None:
    payload = record.get("payload", {})
    request_id = payload.get("request_id", "-")
    status_code = payload.get("status_code", "-")

    print(f"[{record.get('ts', '-')}] {record.get('event_type', '-')}")
    print(f"  request_id : {request_id}")
    print(f"  status_code: {status_code}")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print("-" * 80)


def follow_trace(log_dir: Path, pattern: str, from_start: bool) -> None:
    current_trace = None
    current_file = None

    while True:
        latest_trace = find_latest_trace(log_dir, pattern)
        if latest_trace is None:
            time.sleep(0.5)
            continue

        if current_trace != latest_trace:
            if current_file:
                current_file.close()
            current_trace = latest_trace
            current_file = current_trace.open("r", encoding="utf-8")
            if not from_start:
                current_file.seek(0, 2)
            print(f"Following trace file: {current_trace}")

        line = current_file.readline()
        if not line:
            time.sleep(0.3)
            continue

        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            print(f"Skipping malformed line: {line.rstrip()}")
            continue

        render_record(record)


def main() -> None:
    args = parse_args()
    log_dir = Path(args.log_dir).expanduser()
    log_dir.mkdir(parents=True, exist_ok=True)
    follow_trace(log_dir=log_dir, pattern=args.pattern, from_start=args.from_start)


if __name__ == "__main__":
    main()
