"""Visual extraction locator, matcher, learning, and cross-document testing."""
from app.services.locators.locator_service import (
    analyze_pdf_selection,
    create_locator_from_selection,
    compile_locator_to_rule,
)
from app.services.locators.matcher import match_locator_against_page
from app.services.locators.learning import learn_generalized_locator
from app.services.locators.tester import test_locator_cross_documents

__all__ = [
    "analyze_pdf_selection",
    "create_locator_from_selection",
    "compile_locator_to_rule",
    "match_locator_against_page",
    "learn_generalized_locator",
    "test_locator_cross_documents",
]
