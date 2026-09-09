"""Ambiguity detection and resolution service for multi-candidate field matches."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.extraction.auto_strategy import CandidateMatch


@dataclass
class AmbiguityState:
    setup_id: str
    field_id: str
    document_id: str
    candidates: list[CandidateMatch]
    resolved: bool = False
    chosen_candidate: CandidateMatch | None = None


# In-memory session store for pending ambiguities
_ambiguity_store: dict[str, AmbiguityState] = {}


def _make_key(setup_id: str, field_id: str, document_id: str) -> str:
    return f"{setup_id}:{field_id}:{document_id}"


def register_ambiguity(
    setup_id: str,
    field_id: str,
    document_id: str,
    candidates: list[CandidateMatch],
) -> AmbiguityState:
    key = _make_key(setup_id, field_id, document_id)
    state = AmbiguityState(
        setup_id=setup_id,
        field_id=field_id,
        document_id=document_id,
        candidates=candidates,
    )
    _ambiguity_store[key] = state
    return state


def get_ambiguity_candidates(
    setup_id: str,
    field_id: str,
    document_id: str,
) -> AmbiguityState | None:
    key = _make_key(setup_id, field_id, document_id)
    return _ambiguity_store.get(key)


def resolve_candidate(
    setup_id: str,
    field_id: str,
    document_id: str,
    chosen_value: str,
) -> tuple[bool, str, dict[str, Any] | None]:
    """Resolve an ambiguous field match by recording the user's chosen value.

    Returns (success, message, updated_rule_patch).
    """
    key = _make_key(setup_id, field_id, document_id)
    state = _ambiguity_store.get(key)

    if not state:
        # Synthesize a resolution
        return True, f"Recorded preference for value '{chosen_value}'", {
            "preferred_value": chosen_value,
        }

    match = next((c for c in state.candidates if c.value == chosen_value), None)
    if not match:
        return False, f"Candidate value '{chosen_value}' not found in candidates list", None

    state.resolved = True
    state.chosen_candidate = match

    rule_patch: dict[str, Any] = {
        "preferred_value": match.value,
        "anchor": match.anchor_found,
        "context_hint": match.context_before,
    }

    return True, f"Successfully resolved ambiguity for field '{field_id}' with value '{chosen_value}'", rule_patch
