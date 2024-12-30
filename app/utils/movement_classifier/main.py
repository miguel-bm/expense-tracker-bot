from datetime import datetime
from pathlib import Path
from typing import Literal

import yaml
from jinja2 import Template
from openai import AsyncOpenAI
from pydantic import BaseModel

from app.models.expense import Expense
from app.models.income import Income
from app.models.movement import Movement
from app.storage.expenses.base import ExpenseStorageInterface
from app.storage.incomes.base import IncomeStorageInterface
from app.utils.categories import get_categories_str
from app.utils.config import settings
from app.utils.logger import logger

EXPENSE_CATEGORIES_PATH = "expense_categories.yml"
INCOME_CATEGORIES_PATH = "income_categories.yml"
SPECIAL_INSTRUCTIONS_PATH = "category_instructions.txt"
STATEMENT_TEXT_KEY = "statement_text"

SYSTEM_PROMPT_PATH = Path(__file__).parent / "prompts/system.jinja2"
USER_PROMPT_PATH = Path(__file__).parent / "prompts/user.jinja2"

SYSTEM_PROMPT_TEMPLATE = Template(SYSTEM_PROMPT_PATH.read_text())
USER_PROMPT_TEMPLATE = Template(USER_PROMPT_PATH.read_text())

SPECIAL_INSTRUCTIONS = Path(SPECIAL_INSTRUCTIONS_PATH).read_text()


class MovementClassification(BaseModel):
    movement_id: str
    concept: str
    category: list[str]
    payment_method: Literal["card", "transfer", "p2p"]


class ClassificationOutput(BaseModel):
    movements: list[MovementClassification]


def is_matching_movement(
    movement: Movement, expense_or_income: Expense | Income
) -> bool:
    return (expense_or_income.timestamp.date() == movement.min_date) and (
        (round(expense_or_income.cost, 2) == round(-movement.amount, 2))
        if isinstance(expense_or_income, Expense)
        else (round(expense_or_income.value, 2) == round(movement.amount, 2))
    )


def is_duplicate_movement(
    movement: Movement, expense_or_income: Expense | Income
) -> bool:
    return (
        (expense_or_income.timestamp.date() == movement.min_date)
        and (
            (round(expense_or_income.cost, 2) == round(-movement.amount, 2))
            if isinstance(expense_or_income, Expense)
            else (round(expense_or_income.value, 2) == round(movement.amount, 2))
        )
        and (expense_or_income.metadata is not None)
        and (STATEMENT_TEXT_KEY in expense_or_income.metadata)
        and (expense_or_income.metadata[STATEMENT_TEXT_KEY] == movement.description)
    )


async def classify_movements(
    movements: list[Movement],
    openai_client: AsyncOpenAI,
) -> ClassificationOutput:
    expense_categories: dict[str, dict | None] = yaml.safe_load(
        Path(EXPENSE_CATEGORIES_PATH).read_text()
    )
    income_categories: dict[str, dict | None] = yaml.safe_load(
        Path(INCOME_CATEGORIES_PATH).read_text()
    )
    system_prompt = SYSTEM_PROMPT_TEMPLATE.render(
        expense_categories=get_categories_str(expense_categories),
        income_categories=get_categories_str(income_categories),
        special_instructions=SPECIAL_INSTRUCTIONS,
        language=settings.DEFAULT_LANGUAGE,
    )
    user_prompt = USER_PROMPT_TEMPLATE.render(
        movements=movements,
    )

    response = await openai_client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format=ClassificationOutput,
    )

    parsed_response = response.choices[0].message.parsed
    if parsed_response is None:
        raise ValueError("No response from OpenAI")
    return parsed_response


async def process_movements(
    movements: list[Movement],
    sender: str,
    expense_storage: ExpenseStorageInterface,
    income_storage: IncomeStorageInterface,
    openai_client: AsyncOpenAI,
) -> list[Expense | Income]:
    logger.info(f"Processing {len(movements)} movements")
    expenses = await expense_storage.get_expenses(force_reload=True)
    logger.info(f"Found {len(expenses)} expenses")
    incomes = await income_storage.get_incomes(force_reload=True)
    logger.info(f"Found {len(incomes)} incomes")
    min_movement_date = min(movement.min_date for movement in movements)

    unmatched_expenses = [
        expense
        for expense in expenses
        if (
            (expense.input_method in ("bot", "manual"))
            and (STATEMENT_TEXT_KEY not in (expense.metadata or {}))
            and (expense.timestamp.date() >= min_movement_date)
        )
    ]
    unmatched_incomes = [
        income
        for income in incomes
        if (income.input_method in ("bot", "manual"))
        and (STATEMENT_TEXT_KEY not in (income.metadata or {}))
        and (income.timestamp.date() >= min_movement_date)
    ]

    unmatched_movements: list[Movement] = []

    # Match the movements with the expenses based on the date and amount
    for i, movement in enumerate(movements):
        for j, unmatched_expense in enumerate(unmatched_expenses):
            if is_matching_movement(movement, unmatched_expense):
                # Match the movement with the expense, adding the STATEMENT_TEXT_KEY to the expense metadata and removing the expense from the list to match
                metadata = unmatched_expense.metadata or {}
                new_metadata = {**metadata, STATEMENT_TEXT_KEY: movement.description}
                new_expense = unmatched_expense.model_copy(
                    update={"metadata": new_metadata}
                )
                await expense_storage.update_expense(new_expense)
                unmatched_expenses.pop(j)
                break  # Go to the next movement
        else:
            for j, unmatched_income in enumerate(unmatched_incomes):
                if is_matching_movement(movement, unmatched_income):
                    new_metadata = {
                        **(unmatched_income.metadata or {}),
                        STATEMENT_TEXT_KEY: movement.description,
                    }
                    new_income = unmatched_income.model_copy(
                        update={"metadata": new_metadata}
                    )
                    await income_storage.update_income(new_income)
                    unmatched_incomes.pop(j)
                    break
            else:
                unmatched_movements.append(movement)

    logger.info(
        f"Matched {len(movements) - len(unmatched_movements)} movements with previously inputed expenses"
    )

    existing_expenses = [
        e
        for e in expenses
        if (STATEMENT_TEXT_KEY in (e.metadata or {}))
        and (e.timestamp.date() >= min_movement_date)
    ]
    existing_incomes = [
        i
        for i in incomes
        if (STATEMENT_TEXT_KEY in (i.metadata or {}))
        and (i.timestamp.date() >= min_movement_date)
    ]
    new_movements: list[Movement] = []

    # Match the movements with the existing ETL expenses based on the date and amount
    for i, movement in enumerate(unmatched_movements):
        for j, existing_etl_expense in enumerate(existing_expenses):
            if is_duplicate_movement(movement, existing_etl_expense):
                # We no longer need to match this movement with an expense, so we can skip it in the next loop
                existing_expenses.pop(j)
                break
        else:
            for j, existing_etl_income in enumerate(existing_incomes):
                if is_duplicate_movement(movement, existing_etl_income):
                    # We no longer need to match this movement with an income, so we can skip it in the next loop
                    existing_incomes.pop(j)
                    break
            else:
                new_movements.append(movement)

    logger.info(f"There are {len(new_movements)} new movements to be processed")

    # The new movements need to go through category classification to turn them into expenses or incomes, and then be added to the expense storage
    if not new_movements:
        logger.info("No new movements to process")
        return []

    logger.info("Classifying new movements")
    classifications = await classify_movements(new_movements, openai_client)
    for classification in classifications.movements:
        if classification.category[0] == "other":
            logger.warning(f"Movement {classification.movement_id} classified as other")

    classifications_map = {
        classification.movement_id: classification
        for classification in classifications.movements
    }

    new_expenses_or_incomes: list[Expense | Income] = []
    expenses_to_add: list[Expense] = []
    incomes_to_add: list[Income] = []
    for movement in new_movements:
        if movement.movement_id in classifications_map:
            classification = classifications_map[movement.movement_id]
            if movement.amount <= 0:
                new_expense = Expense(
                    expense_id=movement.movement_id,
                    timestamp=datetime.combine(movement.min_date, datetime.min.time()),
                    sender=sender,
                    cost=-movement.amount,
                    concept=classification.concept,
                    category=classification.category,
                    payment_method=classification.payment_method,
                    input_method="etl",
                    metadata={STATEMENT_TEXT_KEY: movement.description},
                )
                expenses_to_add.append(new_expense)
                new_expenses_or_incomes.append(new_expense)
                logger.info(f"Added expense {new_expense.expense_id}")
            else:
                new_income = Income(
                    income_id=movement.movement_id,
                    timestamp=datetime.combine(movement.min_date, datetime.min.time()),
                    sender=sender,
                    value=movement.amount,
                    concept=classification.concept,
                    category=classification.category,
                    payment_method=classification.payment_method,
                    input_method="etl",
                    metadata={STATEMENT_TEXT_KEY: movement.description},
                )
                incomes_to_add.append(new_income)
                new_expenses_or_incomes.append(new_income)
                logger.info(f"Added income {new_income.income_id}")
        else:
            logger.warning(f"Movement {movement.movement_id} not classified by LLM")

    if expenses_to_add:
        await expense_storage.add_expenses(expenses_to_add)
    if incomes_to_add:
        await income_storage.add_incomes(incomes_to_add)

    logger.info("Finished processing movements")
    return new_expenses_or_incomes
