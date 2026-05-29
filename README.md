# Это проект для отработки межсервисного взаимодействия через retry, jitter, circuit_breaker
Есть два сервиса:
- retry_project_base - это базовый сервис в нем реализована регистрация пользователя и создание пользователю задач. 

При создании задачи происходит:

-- обращение ко второму сервису

-- расчет метаданных по задаче

-- сохранение расчетных метрик в своей бд

-- возвращение расчетных метрик в 1й сервис

-- создание задачи с учетом информации от 2го сервиса

- retry_project_2 - это второй сервис, который получает от первого сервиса информацию по задаче, обрабатывает информацию и возвращает метрики в 1й сервис
для финального создания задачи


## Установка
1. Скачать проект с гитхаба
~~~pycon
/opt/getcourse# git clone https://github.com/MaksAnikeev/it_bot.git .
~~~
2. Создать файл `.env` в корне проекта и прописать туда переменные окружения

данные пустой БД в постгри, она создастся автоматически по указанным вами данным
DB_HOST=
DB_PORT=
DB_NAME=
DB_USER=
DB_PASS=

флаг для переключения вида разработки
MODE=LOCAL

TASK_SERVICE_URL="http://localhost:8001"

Пример
~~~pycon
MODE=LOCAL

DB_HOST=localhost
DB_PORT=5436
DB_NAME=tasks
DB_USER=postgres
DB_PASS=123456


TASK_SERVICE_URL="http://localhost:8001"
~~~

3. Установить зависимости/библиотеки
~~~pycon
pip install poetry
poetry init

# указываем чтобы поетри работало с виртуалкорй, чтобы не писать каждый раз `poetry run`
poetry config --local virtualenvs.in-project true

poetry install
~~~

4. Активировать окружение
.\.venv\Scripts\activate

5. Обновить все пакеты
poetry update

6. Развернуть базу данных в докер контейнере
~~~pycon
docker compose up -d
~~~

7. Установить миграции
~~~pycon
alembic upgrade head  
~~~

8. Запустить проект
~~~pycon
python -m src.main  
~~~