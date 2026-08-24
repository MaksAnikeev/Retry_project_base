import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import circuitbreaker
import pytest
from httpx import AsyncClient

from src.exceptions import ExternalServiceUnavailableException
from src.schemas.tasks_schemas import TaskAPIResponseSchema


async def mock_fetch_reports(self, tasks):
    return {
        task.id: TaskAPIResponseSchema(
            task_id=task.id,
            complexity="hard",
            estimated_hours=8.5,
            priority="high",
        )
        for task in tasks
    }


async def mock_external_service_error(self, tasks):
    raise ExternalServiceUnavailableException(
        detail="Report service is down for maintenance"
    )


def make_circuit_breaker_error():
    mock_cb = MagicMock()
    mock_cb.name = "report_service_circuit"
    mock_cb.open_until = datetime.now() + timedelta(seconds=30)
    mock_cb.failure_count = 5
    mock_cb.open_remaining = 30.0
    mock_cb.last_failure = Exception("Connection refused")

    return circuitbreaker.CircuitBreakerError(mock_cb)


async def mock_circuit_breaker_open(self, tasks):
    raise make_circuit_breaker_error()


@pytest.mark.parametrize(
    "email, title, status_code",
    [
        ("user3@test.com", "Купить чернила", 200),
        ("user1@test.com", "Купить чернила", 409),
        ("user4@test.com", "Купить бумагу", 422),
    ],
)
async def test_add_user_tasks(
    email, title, status_code, ac: AsyncClient
):
    payload = {
        "email": email,
        "username": "User",
        "password": "admin",
        "tasks": [
            {
                "title": "Купить бумагу",
                "description": "Заказать в офисмаге бумагу",
                "finish_date": "2026-05-21"
            },
            {
                "title": title,
                "description": "Магазин напротив пойти и купить",
                "finish_date": "2026-06-01"
            }
        ]
    }
    with patch(
        "src.services.user_task_service.UserTaskService._fetch_reports",
        mock_fetch_reports,
    ):
        response = await ac.post("/user_tasks", json=payload)
    assert response.status_code == status_code
    if status_code == 200:
        data = response.json()
        assert len(data["tasks"]) == 2
        for task in data["tasks"]:
            assert task["complexity"] == "hard"
            assert task["estimated_hours"] == 8.5
            assert task["priority"] == "high"
            assert task["report_status"] == "completed"


async def test_add_user_external_service_unavailable(ac: AsyncClient):
    with patch(
        "src.services.user_task_service.UserTaskService._fetch_reports",
        mock_external_service_error,
    ):
        payload = {
            "email": "user_external_error@test.com",
            "username": "User_external_error",
            "password": "admin",
            "tasks": [
                {
                    "title": "Задача к тесту external_service_unavailable",
                    "description": "Заказать в офисмаге бумагу",
                    "finish_date": "2026-05-21"
                }
            ]
        }

        response = await ac.post("/user_tasks", json=payload)

    assert response.status_code == 200

    data = response.json()
    tasks = data.get("tasks")
    for task in tasks:
        assert task["title"] == "Задача к тесту external_service_unavailable"
        assert task["report_status"] == "pending"
        assert task["complexity"] is None


async def test_add_user_circuit_breaker_open(ac: AsyncClient):
    with patch(
        "src.services.user_task_service.UserTaskService._fetch_reports",
        mock_circuit_breaker_open,
    ):
        payload = {
            "email": "user_circus@test.com",
            "username": "User_circus",
            "password": "admin",
            "tasks": [
                {
                    "title": "Купить бумагу",
                    "description": "Заказать в офисмаге бумагу",
                    "finish_date": "2026-05-21"
                }
            ]
        }
        response = await ac.post("/user_tasks", json=payload)
    assert response.status_code == 503
    data = response.json()
    assert "message" in data
    assert "temporarily unavailable" in data["message"].lower() or \
           "circuit breaker" in data["message"].lower()


async def test_get_user_tasks(ac: AsyncClient):
    response = await ac.get("/user_tasks")
    assert response.status_code == 200
    data = response.json()
    users = data["items"]
    emails = {u["email"] for u in users}
    assert "user1@test.com" in emails
    assert "user2@test.com" in emails


async def test_get_user_tasks_by_id(ac: AsyncClient):
    response = await ac.get("/user_tasks")
    data = response.json()
    users = data["items"]
    user2_id = next(u["id"] for u in users if u["email"] == "user2@test.com")
    response = await ac.get(f"/user_tasks/users/{user2_id}")
    assert response.status_code == 200
    data = response.json()
    tasks = data['tasks']
    assert len(tasks) == 3
    title_tasks = {task["title"] for task in tasks}
    assert "Вторая задача юзера 2" in title_tasks


@pytest.mark.parametrize(
    "email, title, new_email, report_status,user_existed, task_existed, status_code",
    [
        ("user1@test.com", "New_title_task", "new_user1@test.com", "completed", True, True, 200),
        ("user_external_error@test.com", "New_title_task", "new_user_external_error@test.com", "pending",True, True, 200),
        ("new_user1@test.com", "New_title2_task", "user2@test.com", "completed", True, True, 409),
        ("user2@test.com", "Третья задача юзера 2", "user2@test.com", "completed", True, True, 409),
        ("user2@test.com", "New_title_task", "user2@test.com", "completed", False, True, 404),
        ("user2@test.com", "New_title_task", "user2@test.com", "completed", True, False, 404),
    ],
)
async def test_edit_user_tasks(
    email, title, new_email, report_status, status_code, user_existed, task_existed,
    ac: AsyncClient
):
    response = await ac.get("/user_tasks")
    data = response.json()
    users = data["items"]
    user = next(u for u in users if u["email"] == email)
    user_id = user['id']
    if not user_existed:
        user_id = user_id[:-2] + '11'
    task1 = user['tasks'][0]
    task_id = task1['id']
    if not task_existed:
        task_id = task_id[:-2] + '11'
    unique_task_title = f"Новая задача для добавления {uuid.uuid4().hex[:8]}"


    payload = {
            "id": user_id,
            "email": new_email,
            "username": "New_user",
            "password": "1admin1",
            "tasks": [
                {
                    "id": task_id,
                    "title": title,
                    "complexity": "hard",
                },
                {
                    "title": unique_task_title ,
                    "finish_date": "2026-06-21",
                }
            ]
        }
    response = await ac.patch("/user_tasks", json=payload)
    assert response.status_code == status_code
    if status_code == 200:
        data = response.json()
        assert len(data["tasks"]) == 2
        updated_task = next(
            t for t in data["tasks"]
            if t["id"] == task1["id"]
        )
        assert updated_task["complexity"] == "hard"
        assert updated_task["title"] == title
        assert updated_task["report_status"] == report_status

    if response.status_code == 409 and email=="new_user1@test.com":
        assert f"Пользователь с email {new_email} уже существует" in response.json()['message']

    if response.status_code == 409 and email=="user2@test.com":
        assert f"Task with title '{title}' already exists" in response.json()['message']


@pytest.mark.parametrize(
    "email, user_existed, task_existed, only_user_deleted, status_code",
    [
        ("new_user1@test.com", True, True, False, 200),
        ("user2@test.com", True, True, True, 200),
        ("user3@test.com", False, True, False, 404),
        ("user3@test.com", True, False, False, 404),
    ],
)
async def test_delete_user_or_tasks(
    email, user_existed, task_existed, only_user_deleted, status_code,
    ac: AsyncClient
):
    response = await ac.get("/user_tasks")
    users = response.json()["items"]
    user = next(u for u in users if u["email"] == email)
    original_user_id = user['id']
    original_task_id = user['tasks'][0]['id'] if user['tasks'] else None
    user_id = original_user_id if user_existed else user['id'][:-2] + '11'
    task_id = original_task_id if task_existed else original_task_id[:-2] + '11'

    params = {} if only_user_deleted else {"task_ids": [task_id]}

    response = await ac.delete(
        f"/user_tasks/users/{user_id}",
        params=params,
    )
    assert response.status_code == status_code

    if status_code != 200:
        return

    response = await ac.get("/user_tasks")
    users_after = response.json()["items"]
    if only_user_deleted:
        user_after = next(u for u in users_after if u["id"] == original_user_id)
        assert user_after['is_deleted'] == True
        for t in user_after['tasks']:
            assert t['is_deleted'] == True, f"Задача {t['id']} должна быть удалена вместе с пользователем"
    else:
        user_after = next(u for u in users_after if u["id"] == original_user_id)
        assert user_after['is_deleted'] == False, "Пользователь не должен быть удалён"
        deleted_task = next(t for t in user_after['tasks'] if t["id"] == original_task_id)
        assert deleted_task['is_deleted'] == True, f"Задача {original_task_id} должна быть удалена"
        other_tasks = [
            t for t in user_after['tasks']
            if t["id"] != original_task_id
        ]
        for t in other_tasks:
            assert t['is_deleted'] == False, f"Задача {t['id']} не должна быть удалена"


async def test_email_normalization_prevents_duplicates(ac: AsyncClient):
    payload1 = {
        "email": "normalize_me@test.com",
        "username": "User1",
        "password": "admin",
        "tasks": [],
    }
    await ac.post("/user_tasks", json=payload1)

    payload2 = {
        "email": "NORMALIZE_ME@TEST.COM",
        "username": "User2",
        "password": "admin",
        "tasks": [],
    }
    response = await ac.post("/user_tasks", json=payload2)

    assert response.status_code == 409