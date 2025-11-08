# UBHackaton2025

Created by:
Jay Shoemaker
Rowan Sayers-Fay
Johnny Chen

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
# LOGIN_TOKEN_EXPIRE_MINUTES=15
```

> The SQLite database is stored at `./backend/app.db` by default. Override with `DATABASE_URL` if needed.

### Install Dependencies

```bash
python -m venv .venv
.venv\Scripts\activate           # Windows PowerShell
pip install -r backend/requirements.txt
```

### Run the Development Server

```bash
cd backend
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`. Visit `http://127.0.0.1:8000/docs` for the interactive Swagger UI.
