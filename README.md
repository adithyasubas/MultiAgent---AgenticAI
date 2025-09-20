# Evaluation Harness

This folder contains assets to benchmark the YouTube-to-blog pipeline before production rollout.

## Structure
- `dataset.jsonl` – evaluation manifest, one JSON object per sample.
- `transcripts/` – curated transcripts that act as model inputs.
- `references/` – gold-standard blog posts for comparison.
- `mock_outputs/` – cached model outputs to enable offline testing.
- `run_evals.py` – CLI script that executes the evaluation suite and writes a report under `results/`.
- `prepare_dataset.py` – helper utility for adding/listing/validating dataset entries.

## Running The Suite
```bash
# Activate the project virtualenv first
source venv/bin/activate

# Use cached outputs (default) to validate the harness and metrics
python evals/run_evals.py --mode mock

# Call the live OpenAI-backed pipeline (requires network + API key)
python evals/run_evals.py --mode live --generated-dir evals/generated

# Skip BERTScore in offline mode or choose a specific model
python evals/run_evals.py --mode mock --skip-bert-score
python evals/run_evals.py --mode mock --bert-model microsoft/deberta-xlarge-mnli

# Add a new evaluation sample (creates files if missing)
python evals/prepare_dataset.py add --id sample_id --title "Descriptive Title" \
  --video-url "https://youtu.be/..." --transcript evals/transcripts/sample_id.txt \
  --reference evals/references/sample_id.md --tone Professional

# Confirm that every referenced transcript/reference file exists
python evals/prepare_dataset.py validate
```

The script computes:
- ROUGE-1 and ROUGE-L (via `rouge-score` when available, otherwise a token overlap proxy)
- BERTScore precision/recall/F1 (`bert-score`, optional; skipped if unavailable)
- Keyword recall against important content in the reference blog
- Structural checks (heading count, presence of a call to action, word counts)

Each run produces a timestamped JSON report with per-sample metrics and dataset averages. A GitHub Actions workflow (`.github/workflows/evals.yml`) is provided to execute the mock suite on every push/PR and optionally run the live evaluation when an `OPENAI_API_KEY` secret is configured.

> Tip: export `MPLCONFIGDIR=$PWD/.cache/matplotlib` and `XDG_CACHE_HOME=$PWD/.cache/xdg` before running the suite on systems with locked-down home directories to avoid Matplotlib/fontconfig cache warnings.
