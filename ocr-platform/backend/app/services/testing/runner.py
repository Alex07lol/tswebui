"""Test and regression suite runner for extraction configurations."""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.regex_safety import SafeRegex
from app.models.configuration import ConfigurationVersion
from app.models.test import TestCase, TestRun, TestSuite
from app.services.extraction.engine import ExtractionEngine
from app.services.ocr.service import OCRService

log = get_logger(__name__)


def compare_values(actual: Any, expected: Any, mode: str = "exact") -> tuple[bool, str | None]:
    """Compare an extracted value with expected value according to validation_mode.

    Supported modes:
    - exact: Strings match after whitespace strip
    - regex: Expected is regex pattern matching actual
    - numeric_tolerance: Floats match within 0.01 tolerance
    - date_equivalent: Date representations normalize to same date
    """
    act_str = str(actual).strip() if actual is not None else ""
    exp_str = str(expected).strip() if expected is not None else ""

    if mode == "exact":
        matched = act_str.lower() == exp_str.lower()
        reason = None if matched else f"Expected '{exp_str}', got '{act_str}'"
        return matched, reason

    elif mode == "regex":
        if not exp_str:
            return True, None
        matched = SafeRegex.search(exp_str, act_str, timeout_sec=1.0) is not None
        reason = None if matched else f"Actual '{act_str}' did not match pattern '{exp_str}'"
        return matched, reason

    elif mode == "numeric_tolerance":
        # Strip currency symbols and commas
        clean_act = re.sub(r"[^\d.-]", "", act_str)
        clean_exp = re.sub(r"[^\d.-]", "", exp_str)
        try:
            val_act = float(clean_act)
            val_exp = float(clean_exp)
            matched = abs(val_act - val_exp) <= 0.01
            reason = None if matched else f"Numeric mismatch: |{val_act} - {val_exp}| > 0.01"
            return matched, reason
        except ValueError:
            matched = act_str == exp_str
            return matched, None if matched else f"Failed numeric parse for '{act_str}' or '{exp_str}'"

    elif mode == "date_equivalent":
        # Normalize simple delimiters and compare
        norm_act = re.sub(r"[/-]", "-", act_str)
        norm_exp = re.sub(r"[/-]", "-", exp_str)
        matched = norm_act == norm_exp
        reason = None if matched else f"Date mismatch: '{act_str}' != '{exp_str}'"
        return matched, reason

    # Fallback default
    matched = act_str == exp_str
    return matched, None if matched else f"Mismatch: '{act_str}' != '{exp_str}'"


class TestRunner:
    """Executes test suites and regression tests against configuration versions."""

    def __init__(self, ocr_service: OCRService | None = None) -> None:
        self.ocr_service = ocr_service or OCRService()

    async def run_suite(
        self,
        session: AsyncSession,
        suite_id: str,
        config_version_id: str | None = None,
    ) -> TestRun:
        """Run all test cases in a suite against a configuration version."""
        suite_stmt = select(TestSuite).where(TestSuite.id == suite_id)
        suite = (await session.execute(suite_stmt)).scalar_one_or_none()
        if not suite:
            raise ValueError(f"TestSuite {suite_id} not found")

        # Resolve config version
        if not config_version_id:
            ver_stmt = (
                select(ConfigurationVersion)
                .where(ConfigurationVersion.configuration_id == suite.configuration_id)
                .order_by(ConfigurationVersion.version_number.desc())
            )
            config_version = (await session.execute(ver_stmt)).scalars().first()
            if not config_version:
                raise ValueError(
                    f"No configuration version found for configuration {suite.configuration_id}"
                )
            config_version_id = config_version.id
        else:
            ver_stmt = select(ConfigurationVersion).where(
                ConfigurationVersion.id == config_version_id
            )
            config_version = (await session.execute(ver_stmt)).scalar_one_or_none()
            if not config_version:
                raise ValueError(f"ConfigurationVersion {config_version_id} not found")

        cases_stmt = select(TestCase).where(TestCase.suite_id == suite_id)
        test_cases = list((await session.execute(cases_stmt)).scalars().all())

        run_id = str(uuid.uuid4())
        test_run = TestRun(
            id=run_id,
            suite_id=suite.id,
            config_version_id=config_version_id,
            status="running",
            total_cases=len(test_cases),
            passed_cases=0,
            failed_cases=0,
            pass_rate=0.0,
        )
        session.add(test_run)
        await session.flush()

        results_detail: list[dict[str, Any]] = []
        passed_count = 0
        failed_count = 0

        for case in test_cases:
            case_result = await self.run_case(session, case, config_version)
            results_detail.append(case_result)
            if case_result["passed"]:
                passed_count += 1
            else:
                failed_count += 1

        total = len(test_cases)
        pass_rate = round(passed_count / total, 4) if total > 0 else 1.0
        final_status = "passed" if (failed_count == 0 and total > 0) else ("passed" if total == 0 else "failed")

        test_run.status = final_status
        test_run.passed_cases = passed_count
        test_run.failed_cases = failed_count
        test_run.pass_rate = pass_rate
        test_run.results_json = json.dumps(results_detail)

        await session.flush()
        log.info(
            "Test run completed",
            suite_id=suite_id,
            run_id=run_id,
            pass_rate=pass_rate,
            total=total,
        )
        return test_run

    async def run_case(
        self,
        session: AsyncSession,
        case: TestCase,
        config_version: ConfigurationVersion,
    ) -> dict[str, Any]:
        """Execute extraction on a single test case and compare against expected values."""
        case_info: dict[str, Any] = {
            "test_case_id": case.id,
            "name": case.name,
            "document_id": case.document_id,
            "validation_mode": case.validation_mode,
            "is_regression": case.is_regression,
            "passed": False,
            "field_diffs": [],
            "error": None,
        }

        if not case.document_id:
            case_info["error"] = "TestCase has no document associated"
            return case_info

        # 1. Fetch OCR Result for document
        ocr_result = await self.ocr_service.get_ocr_result_for_document(session, case.document_id)
        if not ocr_result:
            case_info["error"] = f"No OCR result found for document {case.document_id}"
            return case_info

        # 2. Extract structured fields
        try:
            raw_cfg = json.loads(config_version.config_snapshot) if config_version.config_snapshot else {}
            extracted = ExtractionEngine.extract_document(ocr_result, raw_cfg)
        except Exception as exc:
            case_info["error"] = f"Extraction failed: {exc}"
            return case_info

        # 3. Map extracted values by logical field_id and output_variable
        actual_map: dict[str, Any] = {}
        confidence_map: dict[str, float] = {}
        for out_var, f in extracted.items():
            val = f.normalized_value if f.normalized_value is not None else f.raw_value
            actual_map[f.field_id] = val
            actual_map[f.output_variable] = val
            confidence_map[f.field_id] = f.final_confidence
            confidence_map[f.output_variable] = f.final_confidence

        # 4. Compare with expected values
        expected_dict: dict[str, Any] = (
            json.loads(case.expected_values_json) if case.expected_values_json else {}
        )

        all_matched = True
        field_diffs: list[dict[str, Any]] = []

        for field_name, expected_val in expected_dict.items():
            actual_val = actual_map.get(field_name)
            matched, reason = compare_values(actual_val, expected_val, case.validation_mode)
            if not matched:
                all_matched = False

            field_diffs.append({
                "field": field_name,
                "expected": expected_val,
                "actual": actual_val,
                "matched": matched,
                "confidence": confidence_map.get(field_name, 0.0),
                "reason": reason,
            })

        case_info["passed"] = all_matched
        case_info["field_diffs"] = field_diffs
        return case_info
