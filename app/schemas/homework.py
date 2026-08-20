from enum import Enum

from pydantic import BaseModel, Field


class HomeworkPractice(str, Enum):
    catalog = "catalog"
    auth = "auth"
    cart_orders = "cart-orders"
    reviews_bug_hunting = "reviews-bug-hunting"


MIN_CHECKS_BY_PRACTICE: dict[HomeworkPractice, int] = {
    HomeworkPractice.catalog: 8,
    HomeworkPractice.auth: 7,
    HomeworkPractice.cart_orders: 9,
    HomeworkPractice.reviews_bug_hunting: 6,
}


class HomeworkCheckItem(BaseModel):
    endpoint: str = Field(min_length=1, examples=["/products/{id}"])
    method: str = Field(min_length=1, examples=["GET"])
    request: str = Field(min_length=1, examples=["product_id = 1"])
    status_code: int = Field(examples=[200])
    response: str = Field(min_length=1, examples=['{"id":1,"name":"..."}'])
    expected: str = Field(min_length=1, examples=["200, товар возвращается"])
    actual: str = Field(min_length=1, examples=["200, товар совпадает"])
    result: str = Field(min_length=1, examples=["Passed"])
    comment: str = Field(min_length=1, examples=["Пример заполнения"])


class HomeworkSubmitRequest(BaseModel):
    checks: list[HomeworkCheckItem]
    notes: str | None = Field(default=None, examples=["Каталог работает корректно, багов не найдено."])


class HomeworkCriterionVerdict(BaseModel):
    criterion: str = Field(examples=["Карточка товара: id в ответе совпадает с id в запросе"])
    status: str = Field(examples=["done"], description="One of: done, partial, not_done.")
    reason: str = Field(examples=["Проверено на GET /products/1, id совпадает."])


class HomeworkSubmitResponse(BaseModel):
    status: str = Field(examples=["passed"], description="One of: passed, needs_revision.")
    score: int = Field(examples=[87], description="Score from 0 to 100.")
    summary: str = Field(examples=["87/100, выполнено 7 из 8 критериев"])
    criteria: list[HomeworkCriterionVerdict]
    attempts_left: int = Field(examples=[4], description="Remaining submissions for this practice today.")
    auto_accepted: bool = Field(
        examples=[False],
        description="True if the submission was accepted automatically because the AI grader was unavailable.",
    )
    code: str | None = Field(
        default=None,
        examples=["A1B2C3D4"],
        description="Stepik completion code, present only when status is 'passed'.",
    )


def validate_min_checks(practice: str, checks: list[HomeworkCheckItem]) -> None:
    # practice is a path param, not a body field, so this can't be a model_validator
    min_checks = MIN_CHECKS_BY_PRACTICE[practice]

    if len(checks) < min_checks:
        raise ValueError(
            f"Practice '{practice}' requires at least {min_checks} checks, "
            f"got {len(checks)}."
        )
