"""Document clustering for automatic template discovery."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.discovery.fingerprint import DocumentFingerprint, DocumentFingerprinter


@dataclass
class ClusterResult:
    label: str
    is_outlier: bool
    document_ids: list[str]
    representative_fingerprint: DocumentFingerprint


class DocumentClusterer:
    """Partitions documents into template groups based on layout similarity."""

    @classmethod
    def cluster(
        cls,
        doc_map: dict[str, Any],  # doc_id -> ocr_result
        similarity_threshold: float = 0.40,
    ) -> list[ClusterResult]:
        """Cluster documents by structural similarity."""
        fingerprints = {
            doc_id: DocumentFingerprinter.fingerprint(ocr_res)
            for doc_id, ocr_res in doc_map.items()
        }

        clusters: list[list[str]] = []
        cluster_fps: list[DocumentFingerprint] = []

        for doc_id, fp in fingerprints.items():
            best_cluster_idx = -1
            best_sim = 0.0

            for idx, c_fp in enumerate(cluster_fps):
                sim = DocumentFingerprinter.similarity(fp, c_fp)
                if sim > best_sim and sim >= similarity_threshold:
                    best_sim = sim
                    best_cluster_idx = idx

            if best_cluster_idx >= 0:
                clusters[best_cluster_idx].append(doc_id)
            else:
                clusters.append([doc_id])
                cluster_fps.append(fp)

        # Label clusters
        results: list[ClusterResult] = []
        normal_idx = 1
        for idx, doc_ids in enumerate(clusters):
            is_outlier = len(doc_ids) == 1 and len(doc_map) > 2
            label = f"Outlier Document" if is_outlier else f"Template {chr(64 + normal_idx)}"
            if not is_outlier:
                normal_idx += 1

            results.append(
                ClusterResult(
                    label=label,
                    is_outlier=is_outlier,
                    document_ids=doc_ids,
                    representative_fingerprint=cluster_fps[idx],
                )
            )

        return results
