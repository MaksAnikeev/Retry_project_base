from unittest.mock import AsyncMock, patch

from httpx import AsyncClient

from src.config import settings
from src.database.unit_of_work import UnitOfWork
from src.repositories.task_rep import TasksRepository
from src.schemas.tasks_schemas import TaskAPIResponseSchema
from src.workers.report_sync_worker import ReportSyncWorker


async def noop_fetch_and_apply_reports(self, tasks, user_orm):
    pass


async def mock_post_reports_batch_for_worker(requests):
    return [
        TaskAPIResponseSchema(
            task_id=req.task_id,
            complexity="hard",
            estimated_hours=8.5,
            priority="high",
        )
        for req in requests
    ]

async def test_report_sync_worker(
    setup_db,
    ac: AsyncClient,
    async_session_factory_null_pull,
):
    payload = {
        "email": "user_worker@test.com",
        "username": "WorkerUser",
        "password": "admin",
        "tasks": [
            {
                "title": "Купить бумагу",
                "description": "Заказать в офисмаге бумагу",
                "finish_date": "2026-05-21"
            },
            {
                "title": "Купить чернила",
                "description": "Магазин напротив пойти и купить",
                "finish_date": "2026-06-01"
            }
        ]
    }
    with patch(
        "src.services.user_task_service.UserTaskService._fetch_and_apply_reports",
        noop_fetch_and_apply_reports,
    ):
        response = await ac.post("/user_tasks", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["tasks"]) == 2
    user_id = data["id"]
    for task in data["tasks"]:
        assert task["report_status"] == "pending"
        assert task["complexity"] is None

    mock_report_client = AsyncMock()
    mock_report_client.post_reports_batch.side_effect = mock_post_reports_batch_for_worker
    mock_report_client.close = AsyncMock()

    async with async_session_factory_null_pull() as session:
        uow = UnitOfWork(session=session)
        task_repo = TasksRepository(session=session)

        worker = ReportSyncWorker(
            task_repo=task_repo,
            report_client=mock_report_client,
            uow=uow,
            batch_size=settings.BATCH_SIZE,
            max_batch_count=settings.MAX_BATCH_COUNT,
        )
        try:
            stats = await worker.run()
        finally:
            await mock_report_client.close()

        assert stats.processed > 0, "Воркер должен был обработать задачи"

        response = await ac.get("/user_tasks")
        users = response.json()["items"]
        user = next(u for u in users if u["id"] == user_id)
        for task in user["tasks"]:
            assert task["complexity"] == "hard"
            assert task["estimated_hours"] == 8.5
            assert task["priority"] == "high"
            assert task["report_status"] == "completed"
        assert mock_report_client.post_reports_batch.called
        assert mock_report_client.close.called
