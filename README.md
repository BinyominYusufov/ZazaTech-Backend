# ZazaTech Backend

FastAPI + SQLModel + **synchronous** SQLite (sync SQLAlchemy — no
aiosqlite/greenlet, so `pip install` needs no C++/Rust toolchain on
Python 3.14; FastAPI runs the sync route handlers in a threadpool).

## Запуск

```bash
# 1. venv
python -m venv venv && source venv/bin/activate
#    Windows PowerShell: python -m venv venv ; venv\Scripts\Activate.ps1

# 2. зависимости
pip install -r requirements.txt

# 3. конфиг (заполнить JWT_SECRET в .env)
cp .env.example .env
#    Windows PowerShell: Copy-Item .env.example .env

# 4. создать первого super_admin
python scripts/seed.py
#    -> ✓ Super admin created: admin@zazetech.com / Admin123!

# 5. запуск
uvicorn app.main:app --reload
```

## API docs

http://localhost:8000/docs

Дефолтный админ после `seed.py`: **admin@zazetech.com** / **Admin123!**
Логин: `POST /api/auth/login` (form: `username`=email, `password`).

## Endpoints

Доступ: **public** — без токена · **auth** — любой залогиненный ·
**super_admin** — только роль super_admin.

| Метод | URL | Доступ | Описание |
|-------|-----|--------|----------|
| GET | `/` | public | meta |
| GET | `/health` | public | healthcheck |
| POST | `/api/auth/login` | public | логин, выдаёт JWT |
| GET | `/api/auth/me` | auth | текущий пользователь |
| POST | `/api/auth/logout` | public | logout (JWT stateless) |
| GET | `/api/users` | super_admin | список пользователей |
| GET | `/api/users/{id}` | super_admin | пользователь по id |
| POST | `/api/users` | super_admin | создать пользователя |
| PUT | `/api/users/{id}` | super_admin | обновить пользователя |
| DELETE | `/api/users/{id}` | super_admin | удалить пользователя |
| GET | `/api/services` | public | список услуг |
| GET | `/api/services/{id}` | public | услуга по id |
| POST | `/api/services` | auth | создать услугу |
| PUT | `/api/services/{id}` | auth | обновить услугу |
| DELETE | `/api/services/{id}` | auth | удалить услугу |
| GET | `/api/projects` | public | список проектов |
| GET | `/api/projects/{id}` | public | проект по id |
| POST | `/api/projects` | auth | создать проект |
| PUT | `/api/projects/{id}` | auth | обновить проект |
| DELETE | `/api/projects/{id}` | auth | удалить проект |
| GET | `/api/blogs?published=` | public | список постов (фильтр) |
| GET | `/api/blogs/{id}` | public | пост по id |
| POST | `/api/blogs` | auth | создать пост |
| PUT | `/api/blogs/{id}` | auth | обновить пост |
| DELETE | `/api/blogs/{id}` | auth | удалить пост |
| POST | `/api/contacts` | public | отправить обращение |
| GET | `/api/contacts?read=` | auth | список обращений (фильтр) |
| GET | `/api/contacts/{id}` | auth | обращение по id |
| PUT | `/api/contacts/{id}/read` | auth | пометить прочитанным |
| DELETE | `/api/contacts/{id}` | auth | удалить обращение |
| GET | `/api/dashboard/stats` | auth | счётчики по сущностям |

**31 endpoint.** `/uploads/...` раздаётся статикой (`StaticFiles`).

## Структура

```
app/
├── core/        config.py · database.py (sync) · security.py · files.py
│                exceptions.py · utils.py
├── models/      SQLModel: user, service, project, blog, contact (+схемы)
├── routers/     auth · users · services · projects · blogs · contacts
│                · dashboard · health
├── dependencies/auth.py  (get_current_user, require_role)
├── middleware/  security.py (заголовки) · rate_limit.py (429)
└── main.py      lifespan · middleware · exception handlers · routers
scripts/seed.py  создание первого super_admin
uploads/         загруженные файлы (отдаётся через /uploads)
```

## Ответы

Успех: данные сущности напрямую (`UserResponse`, `list[...]`) либо
`{"success": true, ...}` (login / dashboard / delete).
Ошибки (глобально): `{"success": false, "message": "..."}`,
валидация — `+ "errors": [{"field","msg"}]`.

## Rate limit

100 req/min на IP; 5 req/min на IP для `/api/auth/login`.
Превышение → `429 {"success": false, "message": "Too many requests, slow down"}`.
In-memory, на процесс (для одного `uvicorn`-воркера).
