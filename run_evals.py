#!/usr/bin/env python3
"""Evaluation harness for the YouTube-to-blog prototype.

The script consumes a JSONL dataset that links transcripts, reference blogs,
optional pre-generated outputs, and metadata such as tone. It can either call
`utils.summarizer.generate_blog` (live mode) or load cached outputs (mock mode)
and reports lexical and structural metrics for each sample plus aggregate stats.
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Dict, List

try:
    from rouge_score import rouge_scorer  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    rouge_scorer = None  # type: ignore

try:
    from bert_score import score as bert_score  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    bert_score = None  # type: ignore

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DEFAULT = BASE_DIR / "evals" / "dataset.jsonl"
DEFAULT_OUTPUT_DIR = BASE_DIR / "evals" / "results"
DEFAULT_GENERATED_DIR = BASE_DIR / "evals" / "mock_outputs"

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "be",
    "but",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "with",
    "you",
    "your",
    "this",
    "we",
}

CTA_KEYWORDS = {
    "subscribe",
    "share",
    "tag",
    "join",
    "follow",
    "call to action",
    "let us know",
    "tell us",
    "comment",
}


def read_jsonl(path: Path) -> List[Dict[str, str]]:
    """Load a JSONL dataset into memory."""
    rows: List[Dict[str, str]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Expected file missing: {path}")
    return path.read_text(encoding="utf-8").strip()


def tokenize(text: str) -> List[str]:
    clean = "".join(ch.lower() if ch.isalnum() else " " for ch in text)
    return [tok for tok in clean.split() if tok and tok not in STOPWORDS]


def keyword_recall(reference: str, generated: str) -> float:
    ref_tokens = set(tok for tok in tokenize(reference) if len(tok) > 4)
    if not ref_tokens:
        return 0.0
    gen_tokens = set(tokenize(generated))
    overlap = ref_tokens & gen_tokens
    return round(len(overlap) / len(ref_tokens), 4)


def simple_overlap(reference: str, generated: str) -> float:
    ref_tokens = set(tokenize(reference))
    if not ref_tokens:
        return 0.0
    gen_tokens = set(tokenize(generated))
    overlap = ref_tokens & gen_tokens
    return round(len(overlap) / len(ref_tokens.union(gen_tokens)), 4)


def detect_cta(text: str) -> bool:
    lower = text.lower()
    return any(keyword in lower for keyword in CTA_KEYWORDS)


def heading_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.strip().startswith("#"))


def rouge_scores(reference: str, generated: str) -> Dict[str, float]:
    if rouge_scorer is None:
        # Fall back to overlap proxy if the true scorer is unavailable.
        overlap = simple_overlap(reference, generated)
        return {"rouge1_f": overlap, "rougeL_f": overlap}

    scorer = rouge_scorer.RougeScorer(["rouge1", "rougeL"], use_stemmer=True)
    scores = scorer.score(reference, generated)
    return {"rouge1_f": round(scores["rouge1"].fmeasure, 4), "rougeL_f": round(scores["rougeL"].fmeasure, 4)}


def collect_metrics(
    reference: str,
    generated: str,
    skip_bert: bool = False,
    bert_model: str | None = None,
) -> Dict[str, float]:
    metrics: Dict[str, float] = {}
    metrics.update(rouge_scores(reference, generated))
    metrics["keyword_recall"] = keyword_recall(reference, generated)
    metrics["call_to_action"] = float(detect_cta(generated))
    metrics["heading_count"] = float(heading_count(generated))
    metrics["word_count_generated"] = float(len(tokenize(generated)))
    metrics["word_count_reference"] = float(len(tokenize(reference)))
    if not skip_bert and bert_score is not None:
        try:
            bert_kwargs: Dict[str, object] = {"lang": "en", "rescale_with_baseline": True}
            if bert_model:
                bert_kwargs["model_type"] = bert_model
            precision, recall, f1 = bert_score([generated], [reference], **bert_kwargs)
            metrics["bert_precision"] = round(float(precision.mean().item()), 4)
            metrics["bert_recall"] = round(float(recall.mean().item()), 4)
            metrics["bert_f1"] = round(float(f1.mean().item()), 4)
        except Exception as exc:  # pragma: no cover - optional metric
            metrics["bert_f1_error"] = 1.0
            print(f"Warning: BERTScore failed ({exc}). Recorded bert_f1_error = 1.0")
    return metrics


def ensure_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def resolve_generated_text(sample: Dict[str, str], mode: str, generated_dir: Path) -> str:
    if mode == "live":
        from utils.summarizer import generate_blog

        tone = sample.get("tone", "professional").lower()
        response = generate_blog(sample["transcript"], tone=tone)
        if isinstance(response, dict):
            if response.get("status") != "success":
                raise RuntimeError(f"Model call failed for {sample['id']}: {response.get('message')}")
            return response["blog_post"]
        # Backward compatibility with older summarizer returning a string.
        if isinstance(response, str):
            return response
        raise TypeError("Unexpected response type from generate_blog")

    # Mock / cached mode expects files named <id>.md or <id>.txt.
    for ext in (".md", ".txt"):
        candidate = generated_dir / f"{sample['id']}{ext}"
        if candidate.exists():
            return read_text(candidate)
    raise FileNotFoundError(f"No cached output found for sample {sample['id']} in {generated_dir}")


def evaluate(
    dataset_path: Path,
    mode: str,
    generated_dir: Path,
    *,
    skip_bert: bool = False,
    bert_model: str | None = None,
) -> Dict[str, Dict[str, float]]:
    dataset = read_jsonl(dataset_path)
    results: Dict[str, Dict[str, float]] = {}

    for row in dataset:
        sample_id = row["id"]
        transcript_path = BASE_DIR / row["transcript_path"]
        reference_path = BASE_DIR / row["reference_blog_path"]

        sample = {
            "id": sample_id,
            "transcript": read_text(transcript_path),
            "reference": read_text(reference_path),
            "tone": row.get("tone", "professional"),
        }

        generated = resolve_generated_text(sample, mode=mode, generated_dir=generated_dir)
        metrics = collect_metrics(
            sample["reference"],
            generated,
            skip_bert=skip_bert,
            bert_model=bert_model,
        )
        results[sample_id] = metrics

    return results


def aggregate(results: Dict[str, Dict[str, float]]) -> Dict[str, float]:
    if not results:
        return {}

    all_keys = sorted({metric for sample in results.values() for metric in sample.keys()})
    summary: Dict[str, float] = {}
    for metric in all_keys:
        values = [sample[metric] for sample in results.values() if metric in sample]
        summary[f"avg_{metric}"] = float(mean(values)) if values else 0.0
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run evaluation benchmark for the YouTube-to-blog pipeline.")
    parser.add_argument("--dataset", type=Path, default=DATASET_DEFAULT, help="Path to the evaluation dataset (JSONL)")
    parser.add_argument("--mode", choices=["mock", "live"], default="mock", help="Use cached outputs (mock) or call the live model")
    parser.add_argument("--generated-dir", type=Path, default=DEFAULT_GENERATED_DIR, help="Directory containing cached/generated outputs")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Where to store the evaluation report")
    parser.add_argument("--skip-bert-score", action="store_true", help="Disable BERTScore metric collection (useful in offline environments)")
    parser.add_argument("--bert-model", default="roberta-large", help="Model identifier used by BERTScore (ignored when --skip-bert-score is set)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_output_dir(args.output_dir)

    results = evaluate(
        args.dataset,
        mode=args.mode,
        generated_dir=args.generated_dir,
        skip_bert=args.skip_bert_score,
        bert_model=None if args.skip_bert_score else args.bert_model,
    )
    summary = aggregate(results)

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    report_path = args.output_dir / f"report_{timestamp}.json"
    payload = {
        "dataset": str(args.dataset),
        "mode": args.mode,
        "generated_dir": str(args.generated_dir),
        "timestamp_utc": timestamp,
        "samples": results,
        "summary": summary,
    }
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Saved evaluation report to {report_path}")


if __name__ == "__main__":
    main()
