"""
TrainingPipeline – end-to-end auto-training pipeline.

Workflow
--------
1. For each target repository, instantiate a ``TrainerAgent`` and collect
   training artefacts (issues, PR discussions, code snippets).
2. Merge all JSONL files in ``training/data/`` into a single dataset.
3. Validate each line is well-formed OpenAI fine-tuning JSON.
4. (Optional) Submit the dataset to the OpenAI Fine-Tunes API when the
   ``OPENAI_API_KEY`` is present and the dataset meets the minimum threshold.
5. Write a run report to ``training/reports/``.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from agents.trainer_agent import TrainerAgent

logger = logging.getLogger(__name__)

DATA_DIR = Path("training/data")
REPORT_DIR = Path("training/reports")


class TrainingPipeline:
    """Orchestrates auto-training data collection and optional fine-tuning."""

    def __init__(
        self,
        repos: list[str],
        data_dir: Path = DATA_DIR,
        fine_tune_threshold: int = 100,
        submit_fine_tune: bool = False,
    ) -> None:
        self.repos = repos
        self.data_dir = data_dir
        self.fine_tune_threshold = fine_tune_threshold
        self.submit_fine_tune = submit_fine_tune

        self.data_dir.mkdir(parents=True, exist_ok=True)
        REPORT_DIR.mkdir(parents=True, exist_ok=True)

    def run(self) -> dict[str, Any]:
        """Execute the full training pipeline and return a summary."""
        logger.info("[TrainingPipeline] Starting pipeline for %d repos …", len(self.repos))

        agent = TrainerAgent()
        collection_results: list[dict[str, Any]] = []

        for repo in self.repos:
            result = agent.run({"repo": repo, "output_dir": str(self.data_dir)})
            collection_results.append(result)
            if result.get("status") == "ok":
                logger.info(
                    "[TrainingPipeline] %s – %d examples collected",
                    repo,
                    result.get("examples_written", 0),
                )

        # Merge & validate
        merged_file, total_examples = self._merge_and_validate()

        # Optionally submit fine-tune job
        fine_tune_job: dict[str, Any] = {}
        if self.submit_fine_tune and total_examples >= self.fine_tune_threshold:
            fine_tune_job = self._submit_fine_tune(merged_file)
        elif self.submit_fine_tune:
            logger.info(
                "[TrainingPipeline] Skipping fine-tune: only %d examples (threshold=%d)",
                total_examples,
                self.fine_tune_threshold,
            )

        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "repos_processed": len(self.repos),
            "collection_results": collection_results,
            "merged_file": str(merged_file) if merged_file else None,
            "total_examples": total_examples,
            "fine_tune_job": fine_tune_job,
        }

        self._write_report(summary)
        return summary

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _merge_and_validate(self) -> tuple[Path | None, int]:
        """Merge all JSONL files in ``data_dir`` into one validated file."""
        jsonl_files = list(self.data_dir.glob("*.jsonl"))
        if not jsonl_files:
            logger.warning("[TrainingPipeline] No JSONL files found in %s", self.data_dir)
            return None, 0

        valid_lines: list[str] = []
        for f in jsonl_files:
            for line in f.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if "messages" in obj:
                        valid_lines.append(line)
                except json.JSONDecodeError:
                    pass

        if not valid_lines:
            return None, 0

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        merged = self.data_dir / f"merged_{timestamp}.jsonl"
        merged.write_text("\n".join(valid_lines), encoding="utf-8")
        logger.info(
            "[TrainingPipeline] Merged %d valid examples → %s", len(valid_lines), merged
        )
        return merged, len(valid_lines)

    def _submit_fine_tune(self, dataset_file: Path) -> dict[str, Any]:
        """Upload dataset and create a fine-tuning job via the OpenAI API."""
        try:
            from openai import OpenAI

            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            with dataset_file.open("rb") as fh:
                upload = client.files.create(file=fh, purpose="fine-tune")
            job = client.fine_tuning.jobs.create(
                training_file=upload.id,
                model=os.getenv("TRAINING_MODEL", "gpt-4o-mini"),
            )
            logger.info(
                "[TrainingPipeline] Fine-tune job created: %s (status=%s)",
                job.id,
                job.status,
            )
            return {"job_id": job.id, "status": job.status, "model": job.model}
        except Exception as exc:  # noqa: BLE001
            logger.error("[TrainingPipeline] Fine-tune submission failed: %s", exc)
            return {"error": str(exc)}

    def _write_report(self, summary: dict[str, Any]) -> None:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        report_file = REPORT_DIR / f"training_report_{timestamp}.json"
        report_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        logger.info("[TrainingPipeline] Report written to %s", report_file)
