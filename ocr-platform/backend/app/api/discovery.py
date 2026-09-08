"""Dataset management and pattern learning discovery API endpoints."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_session
from app.models.configuration import Configuration, ConfigurationVersion
from app.models.dataset import Dataset, DatasetDocument
from app.models.discovery import DiscoveryRun, DocumentCluster, PatternProposal
from app.services.discovery.clustering import DocumentClusterer
from app.services.discovery.learner import PatternLearner
from app.services.ocr.service import OCRService

router = APIRouter()
ocr_service = OCRService()


class CreateDatasetRequest(BaseModel):
    name: str
    description: str | None = None


class AddDocumentsRequest(BaseModel):
    document_ids: list[str]


class ApproveProposalRequest(BaseModel):
    configuration_name: str | None = None
    target_config_id: str | None = None


@router.post("/datasets", status_code=status.HTTP_201_CREATED)
async def create_dataset(
    payload: CreateDatasetRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Create a new dataset for pattern learning."""
    ds_id = str(uuid.uuid4())
    dataset = Dataset(
        id=ds_id,
        name=payload.name,
        description=payload.description,
        document_count=0,
    )
    session.add(dataset)
    await session.flush()
    return {"id": dataset.id, "name": dataset.name, "document_count": 0}


@router.get("/datasets")
async def list_datasets(
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    """List all datasets."""
    stmt = select(Dataset).order_by(Dataset.created_at.desc())
    res = await session.execute(stmt)
    datasets = res.scalars().all()
    return [
        {
            "id": d.id,
            "name": d.name,
            "description": d.description,
            "document_count": d.document_count,
            "status": d.status,
        }
        for d in datasets
    ]


@router.post("/datasets/{dataset_id}/documents")
async def add_documents_to_dataset(
    dataset_id: str,
    payload: AddDocumentsRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Attach uploaded documents to a dataset."""
    stmt = select(Dataset).where(Dataset.id == dataset_id).options(selectinload(Dataset.documents))
    res = await session.execute(stmt)
    dataset = res.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    existing_doc_ids = {dd.document_id for dd in dataset.documents}
    added = 0
    for doc_id in payload.document_ids:
        if doc_id not in existing_doc_ids:
            session.add(
                DatasetDocument(
                    id=str(uuid.uuid4()),
                    dataset_id=dataset_id,
                    document_id=doc_id,
                    added_order=len(dataset.documents) + added + 1,
                )
            )
            added += 1

    dataset.document_count += added
    await session.flush()
    return {"dataset_id": dataset.id, "total_documents": dataset.document_count, "added": added}


@router.post("/datasets/{dataset_id}/discover", status_code=status.HTTP_201_CREATED)
async def run_discovery(
    dataset_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Execute pattern learning on all documents in a dataset."""
    ds_stmt = select(Dataset).where(Dataset.id == dataset_id).options(selectinload(Dataset.documents))
    dataset = (await session.execute(ds_stmt)).scalar_one_or_none()
    if not dataset or not dataset.documents:
        raise HTTPException(status_code=400, detail="Dataset has no documents to analyze")

    run_id = str(uuid.uuid4())
    run = DiscoveryRun(
        id=run_id,
        dataset_id=dataset_id,
        status="running",
        started_at=datetime.now(timezone.utc).isoformat(),
    )
    session.add(run)
    await session.flush()

    # Load OCR results
    doc_ocr_map: dict[str, Any] = {}
    for dd in dataset.documents:
        ocr_res = await ocr_service.get_ocr_result_for_document(session, dd.document_id)
        if ocr_res:
            doc_ocr_map[dd.document_id] = ocr_res

    if not doc_ocr_map:
        run.status = "failed"
        run.error_message = "No OCR results available for dataset documents. Run OCR first."
        await session.flush()
        raise HTTPException(status_code=400, detail=run.error_message)

    # 1. Cluster documents
    clusters = DocumentClusterer.cluster(doc_ocr_map)
    run.documents_processed = len(doc_ocr_map)
    run.clusters_found = len(clusters)

    total_proposals = 0

    # 2. Learn proposals per cluster
    for c in clusters:
        cluster_id = str(uuid.uuid4())
        db_cluster = DocumentCluster(
            id=cluster_id,
            run_id=run.id,
            label=c.label,
            document_count=len(c.document_ids),
            is_outlier=c.is_outlier,
            fingerprint_json=json.dumps(c.representative_fingerprint.structural_hash),
        )
        session.add(db_cluster)
        await session.flush()

        cluster_ocr_docs = [doc_ocr_map[did] for did in c.document_ids if did in doc_ocr_map]
        proposals = PatternLearner.learn_proposals_for_cluster(cluster_ocr_docs)
        total_proposals += len(proposals)

        for p in proposals:
            db_proposal = PatternProposal(
                id=str(uuid.uuid4()),
                cluster_id=cluster_id,
                field_name=p.field_name,
                display_name=p.display_name,
                anchor=p.anchor,
                strategy=p.strategy,
                pattern_json=json.dumps(p.pattern_config),
                evidence_json=json.dumps(p.evidence_samples),
                confidence_anchor=p.confidence_anchor,
                confidence_pattern=p.confidence_pattern,
                confidence_position=p.confidence_position,
                confidence_overall=p.confidence_overall,
                status="pending",
            )
            session.add(db_proposal)

    run.proposals_generated = total_proposals
    run.status = "completed"
    run.completed_at = datetime.now(timezone.utc).isoformat()
    await session.flush()

    return {
        "run_id": run.id,
        "dataset_id": dataset.id,
        "status": run.status,
        "documents_processed": run.documents_processed,
        "clusters_found": run.clusters_found,
        "proposals_generated": run.proposals_generated,
    }


@router.get("/discovery/runs/{run_id}")
async def get_discovery_run(
    run_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Get discovery run details including clusters."""
    stmt = (
        select(DiscoveryRun)
        .where(DiscoveryRun.id == run_id)
        .options(selectinload(DiscoveryRun.clusters))
    )
    run = (await session.execute(stmt)).scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Discovery run not found")

    return {
        "id": run.id,
        "dataset_id": run.dataset_id,
        "status": run.status,
        "documents_processed": run.documents_processed,
        "clusters_found": run.clusters_found,
        "proposals_generated": run.proposals_generated,
        "clusters": [
            {
                "id": c.id,
                "label": c.label,
                "document_count": c.document_count,
                "is_outlier": c.is_outlier,
            }
            for c in run.clusters
        ],
    }


@router.get("/discovery/runs/{run_id}/proposals")
async def get_run_proposals(
    run_id: str,
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    """List all field/rule proposals generated by a discovery run."""
    stmt = (
        select(PatternProposal)
        .join(DocumentCluster, DocumentCluster.id == PatternProposal.cluster_id)
        .where(DocumentCluster.run_id == run_id)
        .order_by(PatternProposal.confidence_overall.desc())
    )
    res = await session.execute(stmt)
    proposals = res.scalars().all()

    return [
        {
            "id": p.id,
            "cluster_id": p.cluster_id,
            "field_name": p.field_name,
            "display_name": p.display_name,
            "anchor": p.anchor,
            "strategy": p.strategy,
            "pattern": json.loads(p.pattern_json) if p.pattern_json else {},
            "evidence_samples": json.loads(p.evidence_json) if p.evidence_json else [],
            "confidence": {
                "anchor": p.confidence_anchor,
                "pattern": p.confidence_pattern,
                "position": p.confidence_position,
                "overall": p.confidence_overall,
            },
            "status": p.status,
        }
        for p in proposals
    ]


@router.post("/proposals/{proposal_id}/approve")
async def approve_proposal(
    proposal_id: str,
    payload: ApproveProposalRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Approve a proposal and automatically promote it into an ExtractionConfiguration."""
    p_stmt = select(PatternProposal).where(PatternProposal.id == proposal_id)
    proposal = (await session.execute(p_stmt)).scalar_one_or_none()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    proposal.status = "approved"

    # Find or create target Configuration
    target_cfg = None
    if payload.target_config_id:
        c_stmt = (
            select(Configuration)
            .where(Configuration.id == payload.target_config_id)
            .options(selectinload(Configuration.versions))
        )
        target_cfg = (await session.execute(c_stmt)).scalar_one_or_none()

    if not target_cfg:
        cfg_name = payload.configuration_name or f"Learned Config ({proposal.display_name or proposal.field_name})"
        slug = f"learned_{proposal.field_name}_{uuid.uuid4().hex[:6]}"
        target_cfg = Configuration(
            id=str(uuid.uuid4()),
            name=cfg_name,
            slug=slug,
            description="Auto-generated configuration from pattern learning",
        )
        session.add(target_cfg)

        initial_snapshot = {
            "schema_version": 1,
            "id": slug,
            "name": cfg_name,
            "fields": [],
        }
        version = ConfigurationVersion(
            id=str(uuid.uuid4()),
            configuration_id=target_cfg.id,
            version_number=1,
            status="draft",
            config_snapshot=json.dumps(initial_snapshot),
        )
        session.add(version)
        await session.flush()
    else:
        version = max(target_cfg.versions, key=lambda v: v.version_number)

    # Append new field into configuration snapshot
    cfg_data = json.loads(version.config_snapshot) if version.config_snapshot else {"fields": []}
    pat_data = json.loads(proposal.pattern_json) if proposal.pattern_json else {"type": "regex", "value": r".+"}

    new_field = {
        "id": proposal.field_name,
        "metadata": {"display_name": proposal.display_name or proposal.field_name},
        "output": {"variable": proposal.field_name, "type": "string"},
        "extraction": {
            "strategy": proposal.strategy or "anchored_pattern",
            "anchor": {"value": proposal.anchor or "", "match": "fuzzy", "minimum_similarity": 0.8},
            "search": {"direction": "after", "scope": "same_line"},
            "pattern": pat_data,
        },
        "normalization": ["trim"],
        "validation": {"required": False},
    }
    cfg_data.setdefault("fields", []).append(new_field)
    version.config_snapshot = json.dumps(cfg_data)
    await session.flush()

    return {
        "proposal_id": proposal.id,
        "status": proposal.status,
        "configuration_id": target_cfg.id,
        "configuration_name": target_cfg.name,
        "field_id": proposal.field_name,
    }


@router.post("/proposals/{proposal_id}/reject")
async def reject_proposal(
    proposal_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Reject a proposed field rule."""
    p_stmt = select(PatternProposal).where(PatternProposal.id == proposal_id)
    proposal = (await session.execute(p_stmt)).scalar_one_or_none()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    proposal.status = "rejected"
    await session.flush()
    return {"proposal_id": proposal.id, "status": proposal.status}
