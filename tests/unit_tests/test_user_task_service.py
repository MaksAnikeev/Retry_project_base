from unittest.mock import Mock, AsyncMock
from uuid import uuid4

import pytest

from src.database.unit_of_work import UnitOfWork
from src.exceptions import ObjectNotFoundException, AlreadyExistsException
from src.repositories.user_rep import UsersRepository
from src.schemas.tasks_schemas import TaskUpdateSchema
from src.schemas.users_schemas import UserUpdateWithTasksSchema
from src.services.user_task_service import UserTaskService


@pytest.mark.parametrize(
    "task_id_existed, task_id_corrected, error",
    [
        (True, True, AlreadyExistsException),
        (True, False, ObjectNotFoundException),
        (False, False, AlreadyExistsException),
    ],
)
async def test__validate_tasks_update_error(
    task_id_existed, task_id_corrected, error,
    async_session_factory_null_pull
):
    id1, id2 = uuid4(), uuid4()
    task1, task2 = Mock(), Mock()
    task1.id = id1
    task1.title = "task1"
    task2.id = id2
    task2.title = "task2"

    user = Mock()
    user.id = uuid4()
    user.tasks = [task1, task2]

    if task_id_existed and task_id_corrected:
        update_data = UserUpdateWithTasksSchema(
            id=user.id,
            tasks=[
                TaskUpdateSchema(id=id1, title="task2"),
            ],
        )
    if task_id_existed and not task_id_corrected:
        update_data = UserUpdateWithTasksSchema(
            id=user.id,
            tasks=[
                TaskUpdateSchema(id=uuid4(), title="task1"),
            ],
        )
    if not task_id_existed:
        update_data = UserUpdateWithTasksSchema(
            id=user.id,
            tasks=[
                TaskUpdateSchema(title="task1"),
            ],
        )

    service = UserTaskService(
        user_rep=Mock(),
        report_client=Mock(),
        uow=Mock(),
    )
    with pytest.raises(error):
        service._validate_tasks_update(update_data, user)


async def test_get_and_validate_user_error(async_session_factory_null_pull):
    user = Mock()
    user.id = uuid4()
    new_user_id = uuid4()
    async with async_session_factory_null_pull() as session:
        uow = UnitOfWork(session=session)
        user_rep = UsersRepository(session=session)
        mock_report_client = AsyncMock()

        service = UserTaskService(
            user_rep=user_rep,
            report_client=mock_report_client,
            uow=uow
        )
        with pytest.raises(ObjectNotFoundException):
            await service._get_and_validate_user(user_id=new_user_id)