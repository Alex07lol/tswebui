"""Test suite and regression runner API endpoints."""
from __future__ import annotations

import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.test import TestCase, TestRun, TestSuite
from app.services.testing.runner import TestRunner

router = APIRouter()
runner = TestRunner()


# Schemas
class CreateTestSuiteRequest(BaseModel):
    configuration_id: str
    name: str
    description: str | None = None


class TestSuiteResponse(BaseModel):
    id: str
    configuration_id: str
    name: str
    description: str | None
    created_at: Any

    class Config:
        orm_mode = True


class CreateTestCaseRequest(BaseModel):
    document_id: str
    name: str
    expected_values: dict[str, Any]
    validation_mode: str = "exact"  # exact | regex | numeric_tolerance | date_equivalent
    is_regression: bool = False


class TestCaseResponse(BaseModel):
    id: str
    suite_id: str
    document_id: str | None
    name: str
    expected_values: dict[str, Any] | None
    validation_mode: str
    is_regression: bool
    created_at: Any

    class Config:
        orm_mode = True


class RunSuiteRequest(BaseModel):
    config_version_id: str | None = None


class TestRunResponse(BaseModel):
    id: str
    suite_id: str
    config_version_id: str | None
    status: str
    total_cases: int
    passed_cases: int
    failed_cases: int
    pass_rate: float | None
    results: list[dict[str, Any]] | None
    created_at: Any

    class Config:
        orm_mode = True


@router.post("/suites", response_model=TestSuiteResponse, status_code=status.HTTP_201_CREATED)
async def create_test_suite(
    payload: CreateTestSuiteRequest,
    session: AsyncSession = Depends(get_session),
) -> TestSuiteResponse:
    """Create a new test suite for an extraction configuration."""
    suite = TestSuite(
        id=str(uuid.uuid4()),
        configuration_id=payload.configuration_id,
        name=payload.name,
        description=payload.description,
    )
    session.add(suite)
    await session.flush()
    return TestSuiteResponse(
        id=suite.id,
        configuration_id=suite.configuration_id,
        name=suite.name,
        description=suite.description,
        created_at=suite.created_at,
    )


@router.get("/suites", response_model=list[TestSuiteResponse])
async def list_test_suites(
    configuration_id: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
) -> list[TestSuiteResponse]:
    """List test suites, optionally filtered by configuration_id."""
    stmt = select(TestSuite)
    if configuration_id:
        stmt = stmt.where(TestSuite.configuration_id == configuration_id)
    stmt = stmt.order_by(TestSuite.created_at.desc())
    suites = (await session.execute(stmt)).scalars().all()
    return [
        TestSuiteResponse(
            id=s.id,
            configuration_id=s.configuration_id,
            name=s.name,
            description=s.description,
            created_at=s.created_at,
        )
        for s in suites
    ]


@router.get("/suites/{suite_id}", response_model=TestSuiteResponse)
async def get_test_suite(
    suite_id: str,
    session: AsyncSession = Depends(get_session),
) -> TestSuiteResponse:
    """Get test suite details."""
    suite = (await session.execute(select(TestSuite).where(TestSuite.id == suite_id))).scalar_one_or_none()
    if not suite:
        raise HTTPException(status_code=404, detail="TestSuite not found")
    return TestSuiteResponse(
        id=suite.id,
        configuration_id=suite.configuration_id,
        name=suite.name,
        description=suite.description,
        created_at=suite.created_at,
    )


@router.delete("/suites/{suite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_test_suite(
    suite_id: str,
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete a test suite and its test cases."""
    suite = (await session.execute(select(TestSuite).where(TestSuite.id == suite_id))).scalar_one_or_none()
    if not suite:
        raise HTTPException(status_code=404, detail="TestSuite not found")
    await session.delete(suite)
    await session.flush()


@router.post("/suites/{suite_id}/cases", response_model=TestCaseResponse, status_code=status.HTTP_201_CREATED)
async def add_test_case(
    suite_id: str,
    payload: CreateTestCaseRequest,
    session: AsyncSession = Depends(get_session),
) -> TestCaseResponse:
    """Add a test case to a suite (e.g. Save as Regression Test)."""
    suite = (await session.execute(select(TestSuite).where(TestSuite.id == suite_id))).scalar_one_or_none()
    if not suite:
        raise HTTPException(status_code=404, detail="TestSuite not found")

    case = TestCase(
        id=str(uuid.uuid4()),
        suite_id=suite_id,
        document_id=payload.document_id,
        name=payload.name,
        expected_values_json=json.dumps(payload.expected_values),
        validation_mode=payload.validation_mode,
        is_regression=payload.is_regression,
    )
    session.add(case)
    await session.flush()

    return TestCaseResponse(
        id=case.id,
        suite_id=case.suite_id,
        document_id=case.document_id,
        name=case.name,
        expected_values=payload.expected_values,
        validation_mode=case.validation_mode,
        is_regression=case.is_regression,
        created_at=case.created_at,
    )


@router.get("/suites/{suite_id}/cases", response_model=list[TestCaseResponse])
async def list_test_cases(
    suite_id: str,
    session: AsyncSession = Depends(get_session),
) -> list[TestCaseResponse]:
    """List all test cases in a test suite."""
    stmt = select(TestCase).where(TestCase.suite_id == suite_id).order_by(TestCase.created_at.asc())
    cases = (await session.execute(stmt)).scalars().all()
    return [
        TestCaseResponse(
            id=c.id,
            suite_id=c.suite_id,
            document_id=c.document_id,
            name=c.name,
            expected_values=json.loads(c.expected_values_json) if c.expected_values_json else {},
            validation_mode=c.validation_mode,
            is_regression=c.is_regression,
            created_at=c.created_at,
        )
        for c in cases
    ]


@router.delete("/cases/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_test_case(
    case_id: str,
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete an individual test case."""
    case = (await session.execute(select(TestCase).where(TestCase.id == case_id))).scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="TestCase not found")
    await session.delete(case)
    await session.flush()


@router.post("/suites/{suite_id}/run", response_model=TestRunResponse)
async def run_test_suite(
    suite_id: str,
    payload: RunSuiteRequest | None = None,
    session: AsyncSession = Depends(get_session),
) -> TestRunResponse:
    """Execute a test run for a suite against a configuration version."""
    config_ver_id = payload.config_version_id if payload else None
    try:
        test_run = await runner.run_suite(session, suite_id, config_ver_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test execution error: {e}")

    results = json.loads(test_run.results_json) if test_run.results_json else []
    return TestRunResponse(
        id=test_run.id,
        suite_id=test_run.suite_id,
        config_version_id=test_run.config_version_id,
        status=test_run.status,
        total_cases=test_run.total_cases,
        passed_cases=test_run.passed_cases,
        failed_cases=test_run.failed_cases,
        pass_rate=test_run.pass_rate,
        results=results,
        created_at=test_run.created_at,
    )


@router.get("/runs/{run_id}", response_model=TestRunResponse)
async def get_test_run(
    run_id: str,
    session: AsyncSession = Depends(get_session),
) -> TestRunResponse:
    """Get the full result of a test run."""
    run = (await session.execute(select(TestRun).where(TestRun.id == run_id))).scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="TestRun not found")
    results = json.loads(run.results_json) if run.results_json else []
    return TestRunResponse(
        id=run.id,
        suite_id=run.suite_id,
        config_version_id=run.config_version_id,
        status=run.status,
        total_cases=run.total_cases,
        passed_cases=run.passed_cases,
        failed_cases=run.failed_cases,
        pass_rate=run.pass_rate,
        results=results,
        created_at=run.created_at,
    )


@router.get("/suites/{suite_id}/runs", response_model=list[TestRunResponse])
async def list_suite_runs(
    suite_id: str,
    session: AsyncSession = Depends(get_session),
) -> list[TestRunResponse]:
    """List all previous test runs for a test suite."""
    stmt = select(TestRun).where(TestRun.suite_id == suite_id).order_by(TestRun.created_at.desc())
    runs = (await session.execute(stmt)).scalars().all()
    return [
        TestRunResponse(
            id=r.id,
            suite_id=r.suite_id,
            config_version_id=r.config_version_id,
            status=r.status,
            total_cases=r.total_cases,
            passed_cases=r.passed_cases,
            failed_cases=r.failed_cases,
            pass_rate=r.pass_rate,
            results=json.loads(r.results_json) if r.results_json else [],
            created_at=r.created_at,
        )
        for r in runs
    ]
