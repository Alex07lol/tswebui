"""Unit tests for OCR error tolerance layer."""
import re
from app.services.pattern.ocr_tolerance import make_ocr_tolerant


def test_no_tolerance_on_numeric_quantifier():
    # \d{6} quantifier must not be broken
    tolerant = make_ocr_tolerant(r"\d{6}")
    assert tolerant == r"\d{6}"


def test_O_zero_substitution():
    tolerant = make_ocr_tolerant("ORDER")
    assert "[O0]" in tolerant
    assert re.match(tolerant, "0RDER")
    assert re.match(tolerant, "ORDER")


def test_I_one_l_substitution():
    tolerant = make_ocr_tolerant("ID")
    assert "[Il1]" in tolerant
    assert re.match(tolerant, "1D")
    assert re.match(tolerant, "lD")


def test_S_5_substitution():
    tolerant = make_ocr_tolerant("SN")
    assert "[S5]" in tolerant
    assert re.match(tolerant, "5N")


def test_B_8_substitution():
    tolerant = make_ocr_tolerant("BOX")
    assert "[B8]" in tolerant
    assert re.match(tolerant, "8OX")
