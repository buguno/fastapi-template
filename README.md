# FastAPI Template

An opinionated starting point for building async REST APIs with FastAPI, SQLAlchemy 2.0 and PostgreSQL. It ships a complete, fully tested user + JWT authentication slice so that new projects begin with a working vertical instead of an empty folder.

Everything in this repository is meant to be copied, renamed and extended.

---

## Table of contents

- [Highlights](#highlights)
- [Tech stack](#tech-stack)
- [Requirements](#requirements)
- [Getting started](#getting-started)
- [Environment variables](#environment-variables)
- [Task runner](#task-runner)
- [Project structure](#project-structure)
- [Architecture](#architecture)
- [API reference](#api-reference)
- [Database and migrations](#database-and-migrations)
- [Testing](#testing)
- [Tooling and configuration](#tooling-and-configuration)
- [Continuous integration](#continuous-integration)
- [Conventions](#conventions)
- [Known trade-offs](#known-trade-offs)
- [Extending the template](#extending-the-template)
- [License](#license)

---

## Highlights

- **Fully async** — async engine, `AsyncSession`, async route handlers and services end to end.
- **Layered architecture** — routers handle HTTP, services hold business rules, models hold persistence. Services never import FastAPI.
- **Domain exceptions** — business errors are raised as plain Python exceptions and translated to HTTP status codes by a single global handler.
- **JWT authentication** — login, token refresh, password hashing with Argon2, and a reusable `CurrentUser` dependency.
- **100% test coverage** — statements and branches, enforced across the whole `app/` package.
- **Real PostgreSQL in tests** — Testcontainers spins up a throwaway database, so tests exercise the same engine as production.
- **Ready-made tooling** — Ruff (lint + format), typos, Alembic, Dependabot and a GitHub Actions pipeline.

---

## Tech stack

| Concern | Choice |
| --- | --- |
| Language | Python 3.14 |
| Web framework | FastAPI (`fastapi[standard]`) |
| ORM | SQLAlchemy 2.0 (async, `mapped_as_dataclass`) |
| Database driver | psycopg 3 (`postgresql+psycopg://`) |
| Migrations | Alembic (async template) |
| Settings | pydantic-settings |
| Auth | PyJWT + pwdlib (Argon2) |
| Dependency manager | Poetry 2.x |
| Task runner | poethepoet (Poetry plugin) |
| Lint + format | Ruff |
| Spell check | typos |
| Tests | pytest, pytest-asyncio, pytest-cov, pytest-random-order |
| Test data | Faker, factory-boy, freezegun |
| Test database | Testcontainers (PostgreSQL 16) |

`greenlet` is declared as a direct dependency on purpose — see [Known trade-offs](#known-trade-offs).

---

## Requirements

- **Python 3.14+**
- **Poetry 2.x**
- **Docker** — required to run the test suite; Testcontainers talks to the Docker daemon to start PostgreSQL. You do *not* need PostgreSQL installed locally.
- **PostgreSQL** — only for actually running the application (not for tests).

### Installing the task runner

Tasks are defined under `[tool.poe.tasks]` and exposed as native Poetry commands. Install the plugin once:

```bash
pipx install poetry
pipx inject poetry "poethepoet[poetry_plugin]"
```

> On zsh, the quotes around `"poethepoet[poetry_plugin]"` are mandatory. Without them the shell tries to expand the square brackets as a glob and fails with `zsh: no matches found`.

---

## Getting started

```bash
# 1. Install dependencies
poetry install

# 2. Create your local environment file
cp .env.example .env

# 3. Edit .env with your database credentials and a fresh secret key

# 4. Apply migrations
poetry run alembic upgrade head

# 5. Run the development server
poetry serve
```

The API is then available at `http://127.0.0.1:8000`, with interactive docs at `/docs` and `/redoc`.

To activate the virtual environment in your shell:

```bash
eval $(poetry env activate)
```

`poetry shell` was removed in Poetry 2.x. If you prefer it, `pipx inject poetry poetry-plugin-shell` brings it back.

---

## Environment variables

Settings are loaded by `app/settings.py` through pydantic-settings, which reads `.env` and real environment variables (environment variables win).

| Variable | Required | Example | Purpose |
| --- | --- | --- | --- |
| `ENVIRONMENT` | No (defaults to `development`) | `production` | When set to `production`, `/docs` and `/redoc` are disabled |
| `DATABASE_URL` | **Yes** | `postgresql+psycopg://user:pass@localhost:5432/app_db` | Async SQLAlchemy connection URL |
| `SECRET_KEY` | **Yes** | 64-char hex string | Signs and verifies JWTs |
| `ALGORITHM` | **Yes** | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | **Yes** | `30` | Access token lifetime |

Generate a secret key from a Python shell:

```python
import secrets

print(secrets.token_hex(32))
```

Or as a one-liner in your terminal:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

`token_hex(32)` produces 32 random bytes rendered as 64 hexadecimal characters — comfortably above the 256-bit key that HS256 expects.

Two things worth knowing:

- **The URL driver matters.** It must be an async dialect (`postgresql+psycopg://`). A plain `postgresql://` URL fails at import time, because `create_async_engine` rejects sync drivers.
- **`.env` is gitignored**, `.env.example` is committed. Never commit real credentials.

### Disabling the docs in production

`app/main.py` reads `settings.is_production` to decide whether to expose the documentation:

```python
app = FastAPI(
    docs_url=None if settings.is_production else '/docs',
    redoc_url=None if settings.is_production else '/redoc',
)
```

Note that `/openapi.json` is **still served** in production. Disabling the docs pages alone does not hide the API schema — the full contract can be reconstructed from that endpoint. If you need the API to be opaque, also pass `openapi_url=None`.

---

## Task runner

Defined in `[tool.poe.tasks]`. Because `poetry_command = ""` is set, they run as first-class Poetry commands:

| Command | What it does |
| --- | --- |
| `poetry serve` | Starts the dev server (`fastapi dev app/main.py`) with hot reload |
| `poetry lint` | Runs `ruff check` |
| `poetry format` | Runs `ruff check --fix` then `ruff format` |
| `poetry coverage` | Regenerates the HTML coverage report (`coverage html --show-contexts`) |
| `poetry test` | Runs lint, then the test suite, then `coverage` |

`poetry test` accepts extra arguments through `$POE_EXTRA_ARGS`, so you can narrow a run:

```bash
poetry test tests/routers/test_users.py
```

The coverage HTML report lands in `htmlcov/` (gitignored); open `htmlcov/index.html` to browse it. `--cov-context=test` is enabled, so the report shows *which test* covered each line.

`poetry coverage` exists so you can rebuild that report without re-running the suite. It reads the existing `.coverage` file, so it reflects the **last** pytest run rather than the current state of the code.

---

## Project structure

```bash
.
├── .github/
│   ├── dependabot.yml          # Weekly pip dependency updates
│   └── workflows/pipeline.yaml # CI: lint + tests
├── app/
│   ├── main.py                 # App factory, router wiring, exception handler
│   ├── settings.py             # Pydantic settings loaded from .env
│   ├── database.py             # Async engine, get_session dependency, DbSession alias
│   ├── security.py             # Password hashing, JWT, get_current_user, CurrentUser alias
│   ├── exceptions.py           # Domain exceptions (HTTP-agnostic)
│   ├── models/
│   │   ├── base.py             # table_registry (SQLAlchemy registry)
│   │   ├── user.py             # User model
│   │   └── __init__.py         # Re-exports so metadata sees every table
│   ├── schemas/
│   │   ├── user.py             # UserSchema, UserPublic, UserList
│   │   ├── token.py            # Token
│   │   ├── message.py          # Message
│   │   └── filters.py          # FilterPage (pagination)
│   ├── routers/
│   │   ├── users.py            # /users endpoints
│   │   └── auth.py             # /auth endpoints
│   └── services/
│       ├── user.py             # User business rules
│       └── auth.py             # Authentication business rules
├── migrations/                 # Alembic (async env.py)
│   └── versions/
├── tests/
│   ├── conftest.py             # Fixtures and UserFactory
│   ├── test_main.py            # Root endpoint
│   ├── test_database.py        # get_session dependency
│   ├── test_security.py        # JWT behaviour
│   ├── routers/                # HTTP-level tests
│   └── services/               # Unit tests for business rules
├── .editorconfig
├── .env.example
├── alembic.ini
└── pyproject.toml
```

### Why `models/__init__.py` re-exports

`table_registry.metadata` only knows about tables whose modules have been **imported**. If nobody imports `app/models/post.py`, then `create_all` (in tests) and Alembic's autogenerate silently ignore that table — no error, it just disappears.

`app/models/__init__.py` re-exports every model so a single `from app.models import table_registry` guarantees a complete metadata. **Add one line per new model.** `__all__` is what stops Ruff's `F401` from deleting the "unused" imports.

---

## Architecture

The dependency direction is strictly one-way. Nothing below ever imports from the layer above it:

```mermaid
flowchart TD
    Client([HTTP client])

    subgraph HTTP["HTTP layer"]
        Router["routers/<br/><small>paths, status codes, response models</small>"]
        Schema["schemas/<br/><small>Pydantic contracts</small>"]
        Handler["main.py<br/><small>DomainError handler</small>"]
    end

    subgraph Domain["Domain layer"]
        Service["services/<br/><small>business rules, no FastAPI</small>"]
        Errors["exceptions.py<br/><small>DomainError subclasses</small>"]
    end

    subgraph Persistence["Persistence layer"]
        Model["models/<br/><small>SQLAlchemy mappings</small>"]
        Db[("PostgreSQL")]
    end

    Client -->|request| Router
    Router -->|validates with| Schema
    Router -->|delegates to| Service
    Service -->|queries| Model
    Model -->|AsyncSession| Db

    Service -.->|raises| Errors
    Errors -.->|caught by| Handler
    Handler -.->|maps to status code| Client
    Router -->|serializes with| Schema
```

Solid arrows are the happy path; dashed arrows are the error path. The key property is that `services/` has no arrow pointing at anything in the HTTP layer — it never imports FastAPI, which is what makes it testable without a `TestClient`.

### Routers — the HTTP boundary

Routers declare paths, status codes and response models, then delegate. They stay short by design.

```python
@router.post('/', status_code=HTTPStatus.CREATED, response_model=UserPublic)
async def create_user(data: UserSchema, session: DbSession):
    new_user = await user_service.create_user(session, data)
    return new_user
```

### Services — the business rules

Services receive an `AsyncSession` plus plain data, return models, and raise domain exceptions. **They never import FastAPI**, which makes them testable without HTTP.

### Domain exceptions and the global handler

`app/exceptions.py` defines `DomainError` and its subclasses. `app/main.py` maps each one to a status code in a single place:

```python
STATUS_BY_ERROR = {
    UserAlreadyExists: HTTPStatus.CONFLICT,
    UserNotFound: HTTPStatus.NOT_FOUND,
    NotEnoughPermissions: HTTPStatus.FORBIDDEN,
    InvalidCredentials: HTTPStatus.UNAUTHORIZED,
}

@app.exception_handler(DomainError)
def domain_error_handler(request: Request, exc: DomainError):
    status = STATUS_BY_ERROR.get(type(exc), HTTPStatus.BAD_REQUEST)
    return JSONResponse(status_code=status, content={'detail': str(exc)})
```

This is what keeps routers free of `try/except`. Unmapped `DomainError` subclasses fall back to `400`.

The response shape (`{'detail': ...}`) intentionally matches FastAPI's own `HTTPException`, so clients see one consistent error format.

### Annotated dependency aliases

Ruff's `FAST002` rule requires `Annotated` dependencies. Each alias lives next to the function it wraps, which avoids a circular import that a central `dependencies.py` would create:

```python
# app/database.py
DbSession = Annotated[AsyncSession, Depends(get_session)]

# app/security.py
CurrentUser = Annotated[User, Depends(get_current_user)]
```

Usage: `async def update_user(session: DbSession, current_user: CurrentUser)`.

One consequence: `Annotated` parameters have no default value, so they must come **before** any parameter that does. `read_users(session, skip=0, limit=100)` — not the other way around.

---

## API reference

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| `GET` | `/` | — | Health/hello endpoint |
| `POST` | `/users/` | — | Create a user |
| `GET` | `/users/` | — | List users (paginated) |
| `PUT` | `/users/{user_id}` | Bearer | Update your own user |
| `DELETE` | `/users/{user_id}` | Bearer | Delete your own user |
| `POST` | `/auth/token` | — | Log in, returns an access token |
| `POST` | `/auth/refresh` | Bearer | Exchange a valid token for a fresh one |

### Authentication flow

1. `POST /auth/token` with form fields `username` (the user's **email**) and `password`, following the OAuth2 password flow.
2. The response is `{"access_token": "...", "token_type": "bearer"}`.
3. Send `Authorization: Bearer <token>` on protected routes.
4. Call `POST /auth/refresh` before expiry to get a new token.

```bash
# Log in
curl -X POST http://127.0.0.1:8000/auth/token \
  -d "username=user@example.com&password=secret"

# Use the token
curl http://127.0.0.1:8000/users/ \
  -H "Authorization: Bearer $TOKEN"
```

**The `sub` claim holds the email**, not the id — `get_current_user` looks the user up by email.

### Refresh semantics

`/auth/refresh` requires a token that is **still valid**. It is a renewal endpoint, not a separate refresh-token grant: if the access token has already expired, the user must log in again. Clients should refresh proactively (before expiry), not reactively on a `401`.

There is also no cap on total session length — a client that keeps refreshing stays logged in indefinitely. Add a claim recording the original login time if you need an absolute limit.

### Pagination

`GET /users/` accepts `offset` and `limit` as query parameters, validated by `FilterPage`:

```python
class FilterPage(BaseModel):
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1, le=100)
```

Passing the model through `Annotated[FilterPage, Query()]` flattens it into ordinary query parameters — the OpenAPI schema shows `offset` and `limit` as plain integers with their bounds, not a nested object. Invalid values return `422`.

The `le=100` ceiling is deliberate: without it, `?limit=999999` would drag the whole table.

### Authorization rules

`PUT` and `DELETE` on `/users/{user_id}` only allow users to act on **their own** record. A mismatch raises `NotEnoughPermissions` → `403`.

### Error responses

| Status | When |
| --- | --- |
| `401` | Missing, malformed, expired token, or bad credentials |
| `403` | Acting on another user's record |
| `404` | User not found |
| `409` | Username or email already taken |
| `422` | Request body or query parameters failed validation |

Authentication failures all return the same message (`Incorrect email or password` on login, `Could not validate credentials` on token checks) regardless of cause. This is intentional — distinguishing "unknown email" from "wrong password" enables user enumeration. Tests assert this, so any attempt to make the messages more specific will fail the suite.

---

## Database and migrations

### The model

`User` uses SQLAlchemy 2.0's `mapped_as_dataclass`, which makes instances real dataclasses — that is what lets tests call `asdict(user)`.

```python
@mapped_as_dataclass(table_registry)
class User:
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    created_at: Mapped[datetime] = mapped_column(init=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(init=False, server_default=func.now())
```

`updated_at` currently only has `server_default`, so it is set on insert but **not** refreshed on update. Add `onupdate=func.now()` if you want true modification tracking — and see the note in [Testing](#testing) about the time mock.

### Alembic

`migrations/env.py` is the **async** template and pulls the URL from settings rather than `alembic.ini`:

```python
config.set_main_option('sqlalchemy.url', settings.DATABASE_URL)
target_metadata = table_registry.metadata
```

That is why `alembic.ini` still contains the placeholder `driver://user:pass@localhost/dbname` — it is never used.

```bash
# Create a migration from model changes
poetry run alembic revision --autogenerate -m "add posts table"

# Apply
poetry run alembic upgrade head

# Roll back one revision
poetry run alembic downgrade -1

# History
poetry run alembic history
```

**Always review autogenerated migrations.** Alembic does not detect every change — renames appear as drop + create, and server defaults or constraint changes are often missed.

`migrations/` is excluded from Ruff (`extend-exclude`), because Alembic generates files in its own style (double quotes, long lines). Fighting that on every `revision` is not worth it.

---

## Testing

```bash
poetry test                              # lint + full suite + HTML coverage
poetry run pytest                        # suite only
poetry run pytest tests/routers -v       # a subset
poetry run pytest --cov-report=term-missing   # show uncovered lines
```

**Docker must be running.** Almost every test depends on the `session` fixture, which needs a container. Without the daemon you get `docker.errors.DockerException` at setup, not a helpful message. The first run also pulls the `postgres:16` image.

### How the database fixtures work

```python
@pytest.fixture(scope='session')
def engine():
    with PostgresContainer('postgres:16', driver='psycopg') as postgres:
        yield create_async_engine(postgres.get_connection_url())

@pytest_asyncio.fixture
async def session(engine):
    async with engine.begin() as conn:
        await conn.run_sync(table_registry.metadata.create_all)
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(table_registry.metadata.drop_all)
```

The container is **session-scoped** (one for the whole suite) while the schema is recreated per test. A function-scoped container would start and stop one Docker container per test.

The container fixture is deliberately **synchronous**: an async fixture with `scope='session'` would clash with `asyncio_default_fixture_loop_scope = 'function'` and raise `ScopeMismatch`.

### Available fixtures

| Fixture | Scope | Provides |
| --- | --- | --- |
| `engine` | session | Async engine bound to the Testcontainers database |
| `session` | function | `AsyncSession` with a freshly created schema |
| `client` | function | `TestClient` with `get_session` overridden to use the test session |
| `user` | function | A persisted user; `user.clean_password` holds the plaintext password |
| `other_user` | function | A second persisted user, for permission tests |
| `users` | function | Four persisted users, for pagination tests |
| `token` | function | A valid bearer token for `user` |
| `mock_db_time` | function | Context manager that freezes `created_at`/`updated_at` |
| `faker` | function | Faker instance (from the pytest plugin) |
| `faker_session_locale` | session | Sets the Faker locale to `pt_BR` |

### `user.clean_password`

The stored password is hashed, but login tests need the plaintext. The fixture attaches it as a runtime attribute:

```python
user.clean_password = password
```

This is genuine monkey patching — the attribute does not exist on the model. SQLAlchemy is unaware of it, so it is never persisted and does not survive a `session.refresh()`. It would also break if `User` used `slots=True`.

### `UserFactory`

`tests/conftest.py` defines a factory-boy factory used to build (not persist) users:

```python
class UserFactory(factory.Factory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'test{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@test.com')
    password = factory.LazyAttribute(lambda obj: f'{obj.username}!secret')
```

Two deliberate choices:

- It inherits from `factory.Factory`, not `SQLAlchemyModelFactory`, because **factory-boy does not support `AsyncSession`**. Persistence is the fixture's job.
- `Sequence` is used instead of `factory.Faker` for the unique columns. Sequences guarantee uniqueness by construction; random Faker values can collide and cause flaky `UNIQUE` violations.

Note that `factory.Faker` keeps its **own** Faker instance, separate from the pytest fixture — the `pt_BR` locale does not reach it. Use `factory.Faker.override_default_locale('pt_BR')` if you switch to it.

### Faker determinism

The Faker pytest plugin seeds every test with `DEFAULT_SEED = 0` and calls `fake.unique.clear()` before each one. Data is therefore **reproducible across runs**, and two tests calling `faker.user_name()` in the same order receive the same value. Use `faker.unique` when persisting several records in one test.

### `mock_db_time`

`created_at` and `updated_at` use `server_default=func.now()`, so the database decides their value and date assertions would be impossible. `mock_db_time` registers a temporary SQLAlchemy `before_insert` hook:

```python
with mock_db_time(model=User) as time:
    session.add(User(...))
    await session.commit()
```

It only hooks **inserts**. If you add `onupdate=func.now()` to `updated_at`, you will also need a `before_update` listener — and at that point it should be a separate hook, since an update must not rewrite `created_at`.

### Time-based tests

`freezegun` drives token expiry tests:

```python
with freeze_time('2023-07-14 12:00:00'):
    token = login()

with freeze_time('2023-07-14 12:31:00'):
    # token is now expired
```

The 31-minute gap is tied to `ACCESS_TOKEN_EXPIRE_MINUTES=30`. Raising that value above 31 will break these tests.

### Test layout

- `tests/routers/` — HTTP level, through `TestClient`: status codes, JSON bodies, auth headers.
- `tests/services/` — unit level, through `session` only: business rules and domain exceptions.
- `tests/test_security.py`, `tests/test_database.py`, `tests/test_main.py` — the corresponding top-level modules.

Router tests already exercise the happy paths of the services. The service tests exist for the error branches — including two (`UserNotFound` on update/delete) that are **unreachable through the API**, because the permission check runs first and guarantees the user exists. Those tests use an unpersisted `unknown_user` fixture with a fabricated id.

`tests/` and every subdirectory contain `__init__.py`. This is not decorative: without it, pytest's default `prepend` import mode imports test modules by bare filename, so `tests/test_user.py` and `tests/routers/test_user.py` would collide with `import file mismatch`.

Tests run in **random order** (`--random-order`), which surfaces hidden inter-test dependencies.

---

## Tooling and configuration

### Ruff

```toml
[tool.ruff]
line-length = 79
extend-exclude = ['migrations']

[tool.ruff.lint]
preview = true
select = ['I', 'F', 'E', 'W', 'PL', 'PT', 'FAST']

[tool.ruff.format]
preview = true
quote-style = 'single'
```

Rule sets: `I` (import sorting), `F` (pyflakes), `E`/`W` (pycodestyle), `PL` (pylint), `PT` (pytest style), `FAST` (FastAPI-specific).

### Coverage

```toml
[tool.coverage.run]
core = "ctrace"
concurrency = ["thread", "greenlet"]
```

The `greenlet` concurrency setting matters: SQLAlchemy's async layer runs sync DBAPI code inside greenlets, and without it coverage misses lines executed there.

### typos

Spell-checks the codebase, with `selectin` allowlisted (a SQLAlchemy loader strategy) and Markdown files excluded.

### EditorConfig

4-space indentation everywhere, 2 spaces for `.yml`/`.yaml`. YAML forbids tabs outright, so the global `indent_style = space` is load-bearing there.

### VS Code

`.vscode/settings.json` points the Python extension at Poetry. Because Poetry stores virtualenvs outside the project by default, VS Code may not detect the interpreter — if imports show as unresolved while `poetry run` works, the interpreter is wrong.

Either select it manually (`Python: Select Interpreter`), or make Poetry create the venv in-project:

```bash
poetry config virtualenvs.in-project true --local
poetry env remove --all
poetry install
```

### Dependabot

`.github/dependabot.yml` checks pip dependencies weekly, in the `America/Sao_Paulo` timezone.

---

## Continuous integration

`.github/workflows/pipeline.yaml` runs on every push and pull request: checkout → Python 3.14 → Poetry (+ the poe plugin) → `poetry install` → `poetry test`.

The plugin injection step is required. Without `pipx inject poetry "poethepoet[poetry_plugin]"`, the runner fails with `The requested command test does not exist` — `poethepoet` is a Poetry plugin, not a project dependency.

### CI environment variables

The test suite does **not** connect to `DATABASE_URL` — Testcontainers provides its own database. That variable only exists because `app/database.py` calls `create_async_engine(settings.DATABASE_URL)` at import time, and the engine is lazy, so it never actually connects.

It therefore only has to be a **syntactically valid async URL**. Do not point CI at a production database: it would expose real credentials to every pull request build for no benefit. The same applies to `SECRET_KEY`, which in tests only signs throwaway tokens.

Plain literals are the safer choice:

```yaml
env:
  ENVIRONMENT: development
  DATABASE_URL: postgresql+psycopg://ci:ci@localhost:5432/ci
  SECRET_KEY: ci-secret-key-not-used-in-production
  ALGORITHM: HS256
  ACCESS_TOKEN_EXPIRE_MINUTES: 30
```

Beware of `${{ vars.X }}` for `ALGORITHM` and `ACCESS_TOKEN_EXPIRE_MINUTES`: since every settings field is required, an unset repository variable expands to an **empty string**, and `ACCESS_TOKEN_EXPIRE_MINUTES=''` raises a `ValidationError` at import.

Two possible improvements: cache the Poetry virtualenv, and add a CI-specific task that skips the `coverage html` step (nothing consumes the HTML report on a runner).

---

## Conventions

### Commits

Conventional Commits, lowercase, with a gerund verb:

```bash
feat(models): exporting table registry and user model
fix(poetry): fixing poetry lock and changing package mode equal false
chore(pyproject): adding poe tasks config
```

If you plan to use `commitizen` or `semantic-release`, prefer the standard `build(deps):` or `chore(deps):` over a custom `deps:` type, which those tools ignore.

### Naming

- **Routers use plural** (`routers/users.py`) — the HTTP resource is a collection.
- **Services use singular** (`services/user.py`) — the domain operates on one entity at a time.
- **Models are unprefixed** (`User`, not `UserModel`) — the module path already carries that information.
- **Schemas are named by role**: `UserSchema` (input), `UserPublic` (output), `UserList` (collection).

### Schemas

- `app/schemas/__init__.py` is intentionally **empty**. Import from the specific module (`from app.schemas.user import UserPublic`), which keeps the resource visible at the import site. Models are the exception, for the metadata reason explained above.
- One module per concept, rather than a catch-all `common.py`.
- `UserPublic` sets `model_config = ConfigDict(from_attributes=True)`, which is what allows returning a SQLAlchemy object directly from a handler. Without it, Pydantic rejects anything that is not a dict.

### Code style

Single quotes, 79-column lines, `HTTPStatus` constants instead of raw integers.

---

## Known trade-offs

**`greenlet` is a direct dependency.** SQLAlchemy declares it conditionally, and its platform marker list omits `arm64` — the value macOS reports on Apple Silicon. Poetry would resolve it, write it to the lock file and then skip installation without any error, leaving `ValueError: the greenlet library is required to use this function` at runtime. Declaring it directly bypasses the marker.

**Tests require Docker.** This buys fidelity: SQLite behaves differently from PostgreSQL in ways this codebase touches. Transaction state after an `IntegrityError` is the clearest example — PostgreSQL aborts the transaction and *requires* the rollback in `update_user`, while SQLite would let the test pass without it.

**`Field(init=False)` in settings.** `Settings()` takes no arguments, but Pylance synthesizes an `__init__` from the model fields and reports missing arguments. `init=False` removes them from that synthetic signature. The trade-off is that you can no longer construct `Settings(DATABASE_URL=...)` explicitly — `# type: ignore[call-arg]` on the instantiation is the alternative if you want to keep that door open.

**`UserNotFound` is currently dead code** on the API surface, for the reason given in [Testing](#testing). It is kept as a guard for future admin routes that would edit other users.

**`package-mode = false`.** This is an application, not a distributable library, so Poetry does not try to install the project itself. Without it, `poetry install` fails with `No file/folder found for package fastapi-template`, since the code lives in `app/` rather than `fastapi_template/`.

---

## Extending the template

### Adding a resource

1. **Model** — create `app/models/<resource>.py` and import `table_registry` from `app.models.base`.
2. **Re-export** — add it to `app/models/__init__.py` and to `__all__`.
3. **Migration** — `poetry run alembic revision --autogenerate -m "create <resource> table"`, then review the output.
4. **Schemas** — create `app/schemas/<resource>.py` with the input/output models.
5. **Service** — create `app/services/<resource>.py`. Take `AsyncSession` as the first argument, raise domain exceptions, import nothing from FastAPI.
6. **Exceptions** — add any new `DomainError` subclasses and map them in `STATUS_BY_ERROR`.
7. **Router** — create `app/routers/<resources>.py` with its own `prefix` and `tags`, then `include_router` it in `app/main.py`.
8. **Tests** — HTTP tests in `tests/routers/`, rule tests in `tests/services/`. Remember `__init__.py` in new directories.

### Growing beyond layers

The layered layout works well up to roughly 20–30 endpoints. Past that, consider grouping by domain instead:

```bash
app/users/{router.py,models.py,schemas.py,service.py}
app/auth/{router.py,schemas.py,service.py}
```

Do not start there — it only pays off once the layers themselves get large.

### If you add an `/auth` sub-path

`OAuth2PasswordBearer(tokenUrl='auth/token')` in `app/security.py` must match the real login URL. If the auth router's prefix changes, update it — otherwise the *Authorize* button in `/docs` breaks silently while the tests keep passing, since they call the URL directly.

### Upgrading to a real refresh-token grant

The current `/auth/refresh` requires a still-valid token. To support renewal after expiry, issue a second long-lived token distinguished by a `type` claim, and validate that claim in the refresh endpoint. `create_access_token` already accepts an arbitrary payload, so the change stays local.

---

## License

Licensed under the MIT License. See [`LICENSE`](LICENSE) for more details.
