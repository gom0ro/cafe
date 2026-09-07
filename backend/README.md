# Backend — Alembic & Migrations

Use Alembic to manage database migrations.

Quick commands:

```bash
# from repo root
cd backend
# create a revision (autogenerate):
alembic revision --autogenerate -m "add tables"
# apply migrations:
alembic upgrade head
```

Make sure `DATABASE_URL` env var is set when running in CI or locally if not matching `alembic.ini`.
