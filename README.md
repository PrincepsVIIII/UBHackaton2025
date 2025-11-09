# UBHackaton2025

Created by:
Jay Shoemaker,
Rowan Sayers-Fay,
Johnny Chen,
Ethan Fleury

## Backend (Phase 1) – Buffalo Winter Elder Help Routing

### Prerequisites

- Python 3.10+
- Virtual environment tool of your choice (`python -m venv` recommended)

### Environment Variables

Create a `.env` file in the project root with:

```
APP_BASE_URL=http://localhost:8000
SECRET_KEY=change-me-in-production
EMAIL_FROM=noreply@example.com
EMAIL_USE_CONSOLE=true
# Optional overrides
# ACCESS_TOKEN_EXPIRE_MINUTES=1440
# OTP_EXPIRE_MINUTES=5
# MAX_OPEN_REQUESTS_PER_ELDER=1
# ADMIN_EMAILS=admin1@example.edu,admin2@example.edu
# ADMIN_SECRET=super-secret-token
```

> The SQLite database is stored at `./backend/app.db` by default. Override with `DATABASE_URL` if needed.

### Install Dependencies

```bash
python -m venv .venv
.venv\Scripts\activate           # Windows PowerShell
pip install -r backend/requirements.txt
```

### Database Migrations (Alembic)

**First time setup or after pulling new migrations:**

```bash
cd backend
alembic upgrade head
```

**Creating a new migration after model changes:**

```bash
cd backend
alembic revision --autogenerate -m "Description of changes"
# Review the generated migration file, then commit it
alembic upgrade head
```

**Reset database (wipe and reapply all migrations):**

```bash
cd backend
rm -f app.db  # or delete data/app.db in Docker
alembic upgrade head
```

### Run the Development Server

```bash
cd backend
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`. Visit `http://127.0.0.1:8000/docs` for the interactive Swagger UI.

### Docker Workflow

**Build and run:**

```bash
cd docker
docker-compose up --build -d
```

**Migrations run automatically** when the backend container starts. Database is stored in `/app/backend/data/app.db` inside the container.

### Lifecycle Flow Examples

Replace the `Authorization` values with real bearer tokens from the OTP login flow.

```
# Elder creates a request (enforces MAX_OPEN_REQUESTS_PER_ELDER)
curl -X POST http://127.0.0.1:8000/help-request \
  -H "Authorization: Bearer ${ELDER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"title":"Shovel walkway","description":"Need help clearing path","address_override":null,"lat":42.8864,"lng":-78.8784,"urgency_level":"high","weather_factor":0.8}'

# Volunteer lists open requests
curl "http://127.0.0.1:8000/requests/open?volunteer_lat=42.9&volunteer_lng=-78.88" \
  -H "Authorization: Bearer ${VOLUNTEER_TOKEN}"

# Volunteer claims a request
curl -X POST http://127.0.0.1:8000/requests/123/claim \
  -H "Authorization: Bearer ${VOLUNTEER_TOKEN}"

# Volunteer marks the assignment complete (moves request to completed_pending_approval)
curl -X POST http://127.0.0.1:8000/requests/123/complete \
  -H "Authorization: Bearer ${VOLUNTEER_TOKEN}"

# Elder approves completion (finalizes the request)
curl -X POST http://127.0.0.1:8000/requests/123/approve-completion \
  -H "Authorization: Bearer ${ELDER_TOKEN}"

# Admin force-closes a request (requires allowlisted admin or X-Admin-Secret)
curl -X POST http://127.0.0.1:8000/admin/requests/123/force-close \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  -H "X-Admin-Secret: ${ADMIN_SECRET}"
```

