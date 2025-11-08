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
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
APP_BASE_URL=http://localhost:8000
```

> The SQLite database is stored at `./app.db` by default. Override with `DATABASE_URL` if needed.

### Install Dependencies

```bash
python -m venv .venv
.venv\Scripts\activate           # Windows PowerShell
pip install -r requirements.txt
```

### Run the Development Server

```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`. Visit `http://127.0.0.1:8000/docs` for the interactive Swagger UI.
