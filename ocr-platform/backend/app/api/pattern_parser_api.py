"""Human pattern compilation, inference, and auto-strategy API endpoints."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.extraction.auto_strategy import generate_auto_strategy
from app.services.pattern.human_parser import (
    compile_human_pattern,
    infer_from_description,
    infer_from_examples,
)
from app.services.pattern.type_inferrer import infer_output_type

router = APIRouter()


class CompilePatternRequest(BaseModel):
    human_pattern: str
    ocr_tolerant: bool = False


class InferFromExamplesRequest(BaseModel):
    examples: list[str]


class InferFromDescriptionRequest(BaseModel):
    description: str


class GenerateAutoStrategyRequest(BaseModel):
    display_name: str
    human_pattern: str | None = None
    examples: list[str] | None = None
    description: str | None = None
    ocr_text: str | None = None
    ocr_tolerant: bool = True


@router.post("/pattern-parser/compile")
async def compile_pattern(payload: CompilePatternRequest) -> dict[str, Any]:
    """Compile human tokens (e.g. SN-{YYYY}-{NNNNNN}) into regex."""
    result = compile_human_pattern(payload.human_pattern, ocr_tolerant=payload.ocr_tolerant)
    type_res = infer_output_type(human_pattern=payload.human_pattern)
    return {
        "human_pattern": result.human_pattern,
        "regex": result.regex,
        "ocr_tolerant_regex": result.ocr_tolerant_regex,
        "tokens": result.tokens,
        "example_match": result.example_match,
        "inferred_type": type_res.inferred_type,
    }


@router.post("/pattern-parser/from-examples")
async def pattern_from_examples(payload: InferFromExamplesRequest) -> dict[str, Any]:
    """Infer a human-readable pattern from multiple value examples."""
    result = infer_from_examples(payload.examples)
    type_res = infer_output_type(examples=payload.examples)
    return {
        "inferred_human_pattern": result.inferred_human_pattern,
        "regex": result.regex,
        "confidence": result.confidence,
        "example_match": result.example_match,
        "inferred_type": type_res.inferred_type,
    }


@router.post("/pattern-parser/from-description")
async def pattern_from_description(payload: InferFromDescriptionRequest) -> dict[str, Any]:
    """Infer a human pattern from a natural-language description."""
    result = infer_from_description(payload.description)
    type_res = infer_output_type(human_pattern=result.inferred_human_pattern)
    return {
        "inferred_human_pattern": result.inferred_human_pattern,
        "regex": result.regex,
        "confidence": result.confidence,
        "example_match": result.example_match,
        "inferred_type": type_res.inferred_type,
    }


@router.post("/auto-strategy/generate")
async def auto_strategy_generate(payload: GenerateAutoStrategyRequest) -> dict[str, Any]:
    """Generate a production-ready ExtractionRule from user-friendly inputs."""
    res = generate_auto_strategy(
        display_name=payload.display_name,
        human_pattern=payload.human_pattern,
        examples=payload.examples,
        description=payload.description,
        ocr_text=payload.ocr_text,
        ocr_tolerant=payload.ocr_tolerant,
    )
    return {
        "field_id": res.field_id,
        "display_name": res.display_name,
        "human_pattern": res.human_pattern,
        "compiled_regex": res.compiled_regex,
        "output_type": res.output_type,
        "strategy": res.strategy,
        "anchor": res.anchor,
        "rule_dict": res.rule_dict,
        "confidence": res.confidence,
        "ambiguous": res.ambiguous,
        "candidates": [
            {
                "value": c.value,
                "context_before": c.context_before,
                "context_after": c.context_after,
                "anchor_found": c.anchor_found,
                "confidence": c.confidence,
            }
            for c in res.candidates
        ],
        "explanation": res.explanation,
    }
