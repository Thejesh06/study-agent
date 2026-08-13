# backend/routes/auth_routes.py

from fastapi import APIRouter, HTTPException
from backend.database import get_users
from backend.auth import hash_password, verify_password, create_token

router = APIRouter()


@router.post("/signup")
def signup(data: dict):
    username = data.get("username", "").strip().lower()
    password = data.get("password", "")

    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password are required")
    if len(username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    users = get_users()
    if users.find_one({"username": username}):
        raise HTTPException(status_code=409, detail="Username already taken")

    users.insert_one({"username": username, "password_hash": hash_password(password)})

    token = create_token(username)
    return {"status": "created", "username": username, "token": token}


@router.post("/login")
def login(data: dict):
    username = data.get("username", "").strip().lower()
    password = data.get("password", "")

    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password are required")

    users = get_users()
    user = users.find_one({"username": username})
    if not user or not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_token(username)
    return {"token": token, "username": username}
