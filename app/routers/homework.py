import hashlib
import json
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Body, Depends, HTTPException, Path
from openai import OpenAI
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.config import settings
from app.database import get_db
from app.homework_criteria import PRACTICE_CRITERIA
from app.models.models import HomeworkResult, User
from app.schemas.homework import (
    HomeworkCheckItem,
    HomeworkSubmitRequest,
    HomeworkSubmitResponse,
    validate_min_checks,
)
from app.stepik_code import generate_stepik_code

router = APIRouter(tags=["Homework"])

DAILY_ATTEMPT_LIMIT = 5
GRADING_MODEL = "gpt-4o-mini"
GRADING_TIMEOUT_SECONDS = 18
POINTS_BY_STATUS = {"done": 1.0, "partial": 0.5, "not_done": 0.0}
TIMEOUT_SUMMARY = "Автоматически принято — превышено время ожидания ответа"

CRITERIA_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "criteria": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "criterion": {"type": "string"},
                    "status": {"type": "string", "enum": ["done", "partial", "not_done"]},
                    "reason": {"type": "string"},
                },
                "required": ["criterion", "status", "reason"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["criteria"],
    "additionalProperties": False,
}

_openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)


def compute_fingerprint(checks: list[HomeworkCheckItem], notes: str | None) -> str:
    payload = {
        "checks": [check.model_dump() for check in checks],
        "notes": notes,
    }
    serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False)

    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def count_today_attempts(db: Session, user_id: int, practice: str) -> int:
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    return (
        db.query(HomeworkResult)
        .filter(
            HomeworkResult.user_id == user_id,
            HomeworkResult.practice == practice,
            HomeworkResult.created_at >= today_start,
        )
        .count()
    )


def call_openai_grader(
    practice: str,
    checks: list[HomeworkCheckItem],
    notes: str | None,
) -> list[dict] | None:
    user_content = json.dumps(
        {
            "practice": practice,
            "criteria_to_evaluate": PRACTICE_CRITERIA[practice],
            "submitted_checks": [check.model_dump() for check in checks],
            "submitted_notes": notes,
        },
        ensure_ascii=False,
    )

    try:
        response = _openai_client.chat.completions.create(
            model=GRADING_MODEL,
            timeout=GRADING_TIMEOUT_SECONDS,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a strict QA mentor grading a student's API testing homework. "
                        "For each entry in criteria_to_evaluate, decide whether submitted_checks and "
                        "submitted_notes prove it is done, partial or not_done, and give a short reason "
                        "grounded in the actual submitted data. Return every criterion exactly once, in "
                        "the same order as given."
                    ),
                },
                {"role": "user", "content": user_content},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "homework_grading",
                    "strict": True,
                    "schema": CRITERIA_JSON_SCHEMA,
                },
            },
        )

        return json.loads(response.choices[0].message.content)["criteria"]
    except Exception:
        return None


def score_criteria(criteria_verdicts: list[dict]) -> tuple[int, str]:
    total_points = sum(POINTS_BY_STATUS.get(item["status"], 0.0) for item in criteria_verdicts)
    score = round(total_points / len(criteria_verdicts) * 100)
    done_count = sum(1 for item in criteria_verdicts if item["status"] == "done")
    summary = f"{score}/100, выполнено {done_count} из {len(criteria_verdicts)} критериев"

    return score, summary


def build_response(record: HomeworkResult, attempts_left: int) -> HomeworkSubmitResponse:
    code = generate_stepik_code(record.practice) if record.status == "passed" else None

    return HomeworkSubmitResponse(
        status=record.status,
        score=record.score,
        summary=record.summary,
        criteria=record.criteria_verdicts,
        attempts_left=attempts_left,
        auto_accepted=record.auto_accepted,
        code=code,
    )


@router.post(
    "/homework/{practice}/submit",
    response_model=HomeworkSubmitResponse,
    summary="Submit homework checks for AI grading",
    description=(
        "Submits the filled checks table (and optional notes) for one practice and returns an AI-graded "
        "result.\n\n"
        "Authorization is required.\n\n"
        "Business rules:\n"
        "- checks must meet the practice's minimum row count\n"
        "- resubmitting the exact same checks/notes for the same practice returns the cached result "
        "instead of calling the AI grader again\n"
        "- at most 5 new AI-graded submissions per practice per day\n"
        "- if the AI grader times out or fails, the submission is auto-accepted with score 100"
    ),
    responses={
        200: {
            "description": "Submission graded (or returned from cache) successfully",
        },
        401: {
            "description": "Missing, invalid or inactive token",
        },
        422: {
            "description": "Validation error. For example, checks is empty or shorter than the practice minimum.",
        },
        429: {
            "description": "Daily submission limit reached for this practice",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Daily submission limit reached for practice 'catalog': 5 per day. Try again tomorrow."
                    }
                }
            },
        },
    },
)
def submit_homework(
    practice: Literal["catalog", "auth", "cart-orders", "reviews-bug-hunting"] = Path(
        description="Practice slug.",
        examples=["catalog"],
    ),
    payload: HomeworkSubmitRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        validate_min_checks(practice, payload.checks)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    fingerprint_hash = compute_fingerprint(payload.checks, payload.notes)

    cached = (
        db.query(HomeworkResult)
        .filter(
            HomeworkResult.user_id == current_user.id,
            HomeworkResult.practice == practice,
            HomeworkResult.fingerprint_hash == fingerprint_hash,
        )
        .order_by(HomeworkResult.id.desc())
        .first()
    )

    if cached:
        attempts_left = max(0, DAILY_ATTEMPT_LIMIT - count_today_attempts(db, current_user.id, practice))
        return build_response(cached, attempts_left)

    today_attempts = count_today_attempts(db, current_user.id, practice)

    if today_attempts >= DAILY_ATTEMPT_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=(
                f"Daily submission limit reached for practice '{practice}': "
                f"{DAILY_ATTEMPT_LIMIT} per day. Try again tomorrow."
            ),
        )

    ai_result = call_openai_grader(practice, payload.checks, payload.notes)

    if ai_result:
        criteria_verdicts = ai_result
        score, summary = score_criteria(criteria_verdicts)
        status = "passed" if score >= 80 else "needs_revision"
        auto_accepted = False
    else:
        criteria_verdicts = []
        score = 100
        summary = TIMEOUT_SUMMARY
        status = "passed"
        auto_accepted = True

    homework_result = HomeworkResult(
        user_id=current_user.id,
        practice=practice,
        submitted_checks=[check.model_dump() for check in payload.checks],
        submitted_notes=payload.notes,
        fingerprint_hash=fingerprint_hash,
        status=status,
        score=score,
        summary=summary,
        criteria_verdicts=criteria_verdicts,
        auto_accepted=auto_accepted,
    )

    db.add(homework_result)
    db.commit()
    db.refresh(homework_result)

    attempts_left = max(0, DAILY_ATTEMPT_LIMIT - (today_attempts + 1))

    return build_response(homework_result, attempts_left)
