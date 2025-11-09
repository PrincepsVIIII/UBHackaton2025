from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import sqlite3, bcrypt

app = FastAPI()

# Mount your static folder (for the HTML page)
app.mount("/static", StaticFiles(directory="static"), name="static")

def verify_user(username: str, password: str):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE username=?", (username,))
    row = cursor.fetchone()
    conn.close()
    if row:
        stored_hash = row[0]
        return bcrypt.checkpw(password.encode("utf-8"), stored_hash)
    return False

@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    if verify_user(username, password):
        return JSONResponse(content={"username": username, "message": "Login successful"})
    return JSONResponse(status_code=401, content={"message": "Invalid username or password"})

@app.get("/")
def serve_home():
    with open("static/index.html") as f:
        return HTMLResponse(f.read())
