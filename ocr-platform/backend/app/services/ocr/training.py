"""Tesseract ground-truth dataset builder and training pipeline hooks."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from app.core.logging import get_logger

log = get_logger(__name__)


@dataclass
class GroundTruthPair:
    image_path: Path
    ground_truth_text: str
    box_file_path: Path | None = None
    gt_txt_path: Path | None = None


@dataclass
class EvaluationMetrics:
    cer: float
    wer: float
    char_count: int
    word_count: int
    edits: int


def _levenshtein(a: str, b: str) -> int:
    if not a:
        return len(b)
    if not b:
        return len(a)
    rows = len(a) + 1
    cols = len(b) + 1
    dp = [[0] * cols for _ in range(rows)]
    for i in range(rows):
        dp[i][0] = i
    for j in range(cols):
        dp[0][j] = j
    for i in range(1, rows):
        for j in range(1, cols):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)
    return dp[rows - 1][cols - 1]


def _word_levenshtein(a: list[str], b: list[str]) -> int:
    if not a:
        return len(b)
    if not b:
        return len(a)
    rows = len(a) + 1
    cols = len(b) + 1
    dp = [[0] * cols for _ in range(rows)]
    for i in range(rows):
        dp[i][0] = i
    for j in range(cols):
        dp[0][j] = j
    for i in range(1, rows):
        for j in range(1, cols):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)
    return dp[rows - 1][cols - 1]


def evaluate_ocr(predicted: str, ground_truth: str) -> EvaluationMetrics:
    """Compute CER and WER between predicted and ground-truth text."""
    char_edits = _levenshtein(predicted, ground_truth)
    cer = char_edits / max(len(ground_truth), 1)

    pred_words = re.split(r"\s+", predicted.strip()) if predicted.strip() else []
    gt_words = re.split(r"\s+", ground_truth.strip()) if ground_truth.strip() else []
    word_edits = _word_levenshtein(pred_words, gt_words)
    wer = word_edits / max(len(gt_words), 1)

    return EvaluationMetrics(
        cer=round(cer, 4),
        wer=round(wer, 4),
        char_count=len(ground_truth),
        word_count=len(gt_words),
        edits=char_edits,
    )


class GroundTruthBuilder:
    """Builds Tesseract-compatible ground-truth pairs for fine-tuning."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._manifest: list[GroundTruthPair] = []

    def add_pair(self, image_path: Path, ground_truth_text: str) -> GroundTruthPair:
        stem = image_path.stem
        gt_path = self.output_dir / f"{stem}.gt.txt"
        gt_path.write_text(ground_truth_text, encoding="utf-8")
        pair = GroundTruthPair(
            image_path=image_path,
            ground_truth_text=ground_truth_text,
            gt_txt_path=gt_path,
        )
        self._manifest.append(pair)
        log.info("Ground-truth pair added", stem=stem)
        return pair

    def export_manifest(self, manifest_path: Path) -> None:
        lines = [str(p.image_path.resolve()) for p in self._manifest]
        manifest_path.write_text("\n".join(lines), encoding="utf-8")
        log.info("Manifest exported", path=str(manifest_path), count=len(lines))

    @property
    def pair_count(self) -> int:
        return len(self._manifest)
