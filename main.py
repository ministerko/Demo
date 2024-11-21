from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from cryptography.fernet import Fernet
import sqlite3
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request

# FastAPI app initialization
app = FastAPI()

# Encryption setup
key = Fernet.generate_key()
print(key)
cipher = Fernet(key)
print(cipher)

# Serve static files (for CSS, JS, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates (HTML rendering)
templates = Jinja2Templates(directory="templates")

# Database connection helper function
def get_db_connection():
    conn = sqlite3.connect("credit_loan.db")
    conn.row_factory = sqlite3.Row  # This will allow column access by name
    return conn

# Create the user_credits table (if not already created)
def create_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_credits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT NOT NULL,
            credit_data TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Call create_table at startup
create_table()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # Retrieve encrypted data from the database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_name, credit_data FROM user_credits")
    rows = cursor.fetchall()
    conn.close()

    # Render the index page with the encrypted data
    return templates.TemplateResponse("index.html", {"request": request, "rows": rows})

@app.post("/store_credit_data/")
async def store_credit_data(user_name: str = Form(...), credit_data: str = Form(...)):
    # Encrypt the credit data before storing
    encrypted_data = cipher.encrypt(credit_data.encode())

    # Store the encrypted data in the database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO user_credits (user_name, credit_data) VALUES (?, ?)", (user_name, encrypted_data.decode()))
    conn.commit()
    conn.close()

    return JSONResponse({"message": "Credit data stored successfully!"})

@app.get("/get_credit_data/{user_name}")
async def get_credit_data(user_name: str):
    # Retrieve encrypted credit data from the database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT credit_data FROM user_credits WHERE user_name = ?", (user_name,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="User not found")

    encrypted_data = row["credit_data"]

    # Decrypt the credit data
    decrypted_data = cipher.decrypt(encrypted_data.encode()).decode()

    return {"user_name": user_name, "credit_data": decrypted_data}
