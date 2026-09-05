from datetime import date
from unittest.mock import Mock
from uuid import uuid4

import pytest

from src.mappers.task_mapper import add_report_to_task, split_tasks_by_type, update_tasks_fields
from src.schemas.tasks_schemas import ReportStatus, TaskUpdateSchema
from src.schemas.users_schemas import UserUpdateWithTasksSchema


def test_add_report_to_task(refresh_db):
    task = Mock()
    report = Mock()
    report.complexity = "hard"
    report.estimated_hours = 8.5
    report.priority = "high"

    add_report_to_task(task, report)

    assert task.complexity == "hard"
    assert task.estimated_hours == 8.5
    assert task.priority == "high"
    assert task.report_status == ReportStatus.COMPLETED.value


def test_update_tasks_fields():
    id1, id2 = uuid4(), uuid4()
    task1, task2 = Mock(), Mock()
    task1.id = id1
    task2.id = id2

    user = Mock()
    user.tasks = [task1, task2]

    update_data = [
        TaskUpdateSchema(id=id1, title="Task 1 new"),
        TaskUpdateSchema(id=id2, complexity="hard"),
    ]
    update_tasks_fields(update_data, user)

    assert task1.title == "Task 1 new"
    assert task2.complexity == "hard"


def test_update_tasks_fields_when_task_not_found():
    task_id = uuid4()
    non_existent_id = uuid4()

    task_orm = Mock()
    task_orm.id = task_id
    user = Mock()
    user.tasks = [task_orm]

    update_data = [TaskUpdateSchema(id=non_existent_id, title="New")]

    with pytest.raises(KeyError):
        update_tasks_fields(update_data, user)


def test_split_tasks_by_type():
    task1_id = uuid4()
    task2_id = uuid4()
    existing_task_1_update = TaskUpdateSchema(id=task1_id, title="Existing new")
    existing_task_2_update = TaskUpdateSchema(id=task2_id, title="Existing2 new")

    new_task_update = TaskUpdateSchema(
        id=None,
        title="New task",
        description="Description",
        finish_date=date(2026, 6, 1),
    )

    user_id = uuid4()

    update_data = UserUpdateWithTasksSchema(
        id=user_id,
        tasks=[
            existing_task_1_update,
            existing_task_2_update,
            new_task_update,
        ],
    )
    tasks_to_add, tasks_to_update = split_tasks_by_type(update_data)

    assert len(tasks_to_add) == 1
    assert tasks_to_add[0].title == "New task"

    assert len(tasks_to_update) == 2
    titles_to_update = [task.title for task in tasks_to_update]
    assert "Existing new" in titles_to_update
    assert "Existing2 new" in titles_to_update
