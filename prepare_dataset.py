#!/usr/bin/env python3
"""Utility helpers for curating the evaluation dataset.

The tool streamlines creation and maintenance of `evals/dataset.jsonl`.
It supports adding new samples, updating metadata, and validating that the
transcript/reference files exist before writing entries.

Usage examples:

```bash
# Add a new sample (creates transcript/reference paths if they don't exist)
python evals/prepare_dataset.py add \
  --id my_video \
  --title "Mini album tutorial" \
  --video-url "https://youtu.be/abcd" \
  --transcript evals/transcripts/my_video.txt \
  --reference evals/references/my_video.md \
  --tone Educational

# List entries in the dataset
python evals/prepare_dataset.py list

# Validate all paths referenced by the dataset
python evals/prepare_dataset.py validate
```
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATASET = BASE_DIR / "dataset.jsonl"


def load_rows(dataset_path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not dataset_path.exists():
        return rows
    with dataset_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def write_rows(dataset_path: Path, rows: List[Dict[str, Any]]) -> None:
    dataset_path.parent.mkdir(parents=True, exist_ok=True)
    with dataset_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def add_sample(args: argparse.Namespace) -> None:
    dataset_path: Path = args.dataset
    rows = load_rows(dataset_path)

    if any(row["id"] == args.id for row in rows):
        raise SystemExit(f"Dataset already contains id '{args.id}'. Use a unique identifier.")

    transcript_path = Path(args.transcript)
    reference_path = Path(args.reference)

    if not transcript_path.exists():
        transcript_path.parent.mkdir(parents=True, exist_ok=True)
        transcript_path.touch()
        print(f"Created empty transcript file at {transcript_path}")

    if not reference_path.exists():
        reference_path.parent.mkdir(parents=True, exist_ok=True)
        reference_path.touch()
        print(f"Created empty reference file at {reference_path}")

    row = {
        "id": args.id,
        "video_title": args.title,
        "video_url": args.video_url,
        "transcript_path": str(transcript_path),
        "reference_blog_path": str(reference_path),
        "tone": args.tone,
        "notes": args.notes or "",
    }
    rows.append(row)
    write_rows(dataset_path, rows)
    print(f"Added sample '{args.id}' to {dataset_path}")


def list_samples(args: argparse.Namespace) -> None:
    rows = load_rows(args.dataset)
    if not rows:
        print("Dataset is empty.")
        return

    for row in rows:
        print(f"- {row['id']}: {row['video_title']} ({row.get('tone','professional')})")
        print(f"  transcript -> {row['transcript_path']}")
        print(f"  reference  -> {row['reference_blog_path']}")
        if row.get("notes"):
            print(f"  notes      -> {row['notes']}")


def validate_dataset(args: argparse.Namespace) -> None:
    rows = load_rows(args.dataset)
    missing = []
    for row in rows:
        transcript_path = Path(row["transcript_path"])
        reference_path = Path(row["reference_blog_path"])
        if not transcript_path.exists():
            missing.append(f"Missing transcript for {row['id']}: {transcript_path}")
        if not reference_path.exists():
            missing.append(f"Missing reference for {row['id']}: {reference_path}")
    if missing:
        print("Validation failed:")
        for item in missing:
            print(f"- {item}")
        raise SystemExit(1)
    print("All dataset paths are valid.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage entries in the evaluation dataset")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET, help="Path to the dataset JSONL")

    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add a new sample entry")
    add_parser.add_argument("--id", required=True, help="Unique identifier for the sample")
    add_parser.add_argument("--title", required=True, help="Descriptive title of the video")
    add_parser.add_argument("--video-url", required=True, help="Original video URL")
    add_parser.add_argument("--transcript", required=True, help="Path to the transcript text file")
    add_parser.add_argument("--reference", required=True, help="Path to the reference blog file")
    add_parser.add_argument("--tone", default="professional", help="Tone label for the target output")
    add_parser.add_argument("--notes", help="Optional free-form notes (e.g., tricky cases)")
    add_parser.set_defaults(func=add_sample)

    list_parser = subparsers.add_parser("list", help="List dataset entries")
    list_parser.set_defaults(func=list_samples)

    validate_parser = subparsers.add_parser("validate", help="Validate referenced transcript/reference files")
    validate_parser.set_defaults(func=validate_dataset)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
