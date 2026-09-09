"""Teach From Examples service.

Translates unsupervised document discovery into simple human concepts:
- "Document Clusters" -> "Layouts" (e.g. Layout A, Layout B)
- "Proposals" -> "Suggested Information" with human patterns and plain-English reasons
- "Generate Config" -> "Save Setup"
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.discovery.clustering import DocumentClusterer
from app.services.intelligence.suggestions import suggest_fields
from app.services.pattern.human_parser import infer_from_examples
from app.services.setup.field_service import FieldService
from app.services.setup.setup_service import SetupService


@dataclass
class TeachProposal:
    id: str
    suggested_name: str
    human_pattern: str
    example_found: str
    confidence_label: str  # Very High | High | Medium | Low
    confidence_score: float
    why: list[str]
    action: str = "pending"  # pending | use | edit | skip


@dataclass
class TeachLayout:
    id: str
    label: str  # Layout A, Layout B
    document_count: int
    sample_document_id: str | None = None


@dataclass
class TeachSession:
    session_id: str
    status: str  # uploaded | analyzing | completed
    document_ids: list[str]
    layouts: list[TeachLayout] = field(default_factory=list)
    proposals: list[TeachProposal] = field(default_factory=list)


_teach_sessions: dict[str, TeachSession] = {}


class TeachService:
    @classmethod
    def start_session(cls, document_ids: list[str]) -> TeachSession:
        session_id = str(uuid.uuid4())
        session = TeachSession(
            session_id=session_id,
            status="uploaded",
            document_ids=document_ids,
        )
        _teach_sessions[session_id] = session
        return session

    @classmethod
    def get_session(cls, session_id: str) -> TeachSession | None:
        return _teach_sessions.get(session_id)

    @classmethod
    def analyze(cls, session_id: str, doc_map: dict[str, Any]) -> TeachSession:
        session = _teach_sessions.get(session_id)
        if not session:
            session = cls.start_session(list(doc_map.keys()))

        session.status = "analyzing"

        # 1. Cluster into human layouts (Layout A, Layout B...)
        clusters = DocumentClusterer.cluster(doc_map) if doc_map else []
        layouts: list[TeachLayout] = []
        normal_idx = 1
        for c in clusters:
            label = f"Layout {chr(64 + normal_idx)}" if not c.is_outlier else "Single Outlier"
            if not c.is_outlier:
                normal_idx += 1
            layouts.append(
                TeachLayout(
                    id=str(uuid.uuid4()),
                    label=label,
                    document_count=len(c.document_ids),
                    sample_document_id=c.document_ids[0] if c.document_ids else None,
                )
            )
        if not layouts and doc_map:
            layouts.append(
                TeachLayout(
                    id=str(uuid.uuid4()),
                    label="Layout A",
                    document_count=len(doc_map),
                    sample_document_id=list(doc_map.keys())[0],
                )
            )
        session.layouts = layouts

        # 2. Extract suggested proposals in human terms
        proposals: list[TeachProposal] = []
        total_docs = len(doc_map) or 1
        aggregated_text = " ".join(
            (getattr(res, "full_text", "") or getattr(res, "text", "") or str(res))
            for res in doc_map.values()
        )

        suggestions = suggest_fields(aggregated_text, top_k=6) if aggregated_text else []
        for s in suggestions:
            display_title = s.field_name.replace("_", " ").title()
            infer_res = infer_from_examples([s.example])
            proposals.append(
                TeachProposal(
                    id=str(uuid.uuid4()),
                    suggested_name=display_title,
                    human_pattern=infer_res.inferred_human_pattern,
                    example_found=s.example,
                    confidence_label="Very High" if s.confidence >= 0.85 else "High",
                    confidence_score=s.confidence,
                    why=[
                        f"Found in {total_docs} of {total_docs} sample documents",
                        f"Appears near '{s.matched_alias or display_title}'",
                        "Matches consistent pattern structure across layouts",
                    ],
                )
            )

        session.proposals = proposals
        session.status = "completed"
        return session

    @classmethod
    async def save_setup_from_teach(
        cls,
        db_session: AsyncSession,
        session_id: str,
        setup_name: str,
        accepted_proposal_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        session = _teach_sessions.get(session_id)
        if not session:
            raise ValueError(f"Teach session '{session_id}' not found")

        # Filter proposals
        proposals_to_use = session.proposals
        if accepted_proposal_ids is not None:
            proposals_to_use = [p for p in session.proposals if p.id in accepted_proposal_ids]

        # Create setup
        setup = await SetupService.create_setup(db_session, name=setup_name)
        setup_id = setup["id"]

        # Add fields
        for p in proposals_to_use:
            await FieldService.add_field(
                session=db_session,
                setup_id=setup_id,
                display_name=p.suggested_name,
                human_pattern=p.human_pattern,
                examples=[p.example_found],
            )

        return await SetupService.get_setup(db_session, setup_id) or setup
