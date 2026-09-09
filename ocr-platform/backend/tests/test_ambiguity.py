"""Unit tests for ambiguity candidate registration and resolution."""
from app.services.extraction.ambiguity import (
    CandidateMatch,
    get_ambiguity_candidates,
    register_ambiguity,
    resolve_candidate,
)


def test_register_and_get_candidates():
    c1 = CandidateMatch(value="SN-1", context_before="Serial:", context_after="")
    c2 = CandidateMatch(value="SN-2", context_before="Alt Serial:", context_after="")
    register_ambiguity("setup-1", "serial_number", "doc-1", [c1, c2])

    state = get_ambiguity_candidates("setup-1", "serial_number", "doc-1")
    assert state is not None
    assert len(state.candidates) == 2
    assert state.resolved is False


def test_resolve_candidate_success():
    c1 = CandidateMatch(value="SN-1", context_before="Serial:", context_after="", anchor_found="Serial:")
    c2 = CandidateMatch(value="SN-2", context_before="Alt Serial:", context_after="")
    register_ambiguity("setup-2", "serial_number", "doc-2", [c1, c2])

    success, msg, patch = resolve_candidate("setup-2", "serial_number", "doc-2", "SN-1")
    assert success is True
    assert patch["preferred_value"] == "SN-1"

    state = get_ambiguity_candidates("setup-2", "serial_number", "doc-2")
    assert state.resolved is True
    assert state.chosen_candidate.value == "SN-1"
