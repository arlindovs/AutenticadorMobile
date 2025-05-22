# main.py
from fastapi import FastAPI, Depends, HTTPException, status
from models import init_db
from security import *
from schemas import *
from auth import get_current_user
import sqlite3
import pyotp
import uuid

app = FastAPI()
init_db()

def get_db():
    return sqlite3.connect("authenticator.db")

@app.post("/login", response_model=Token)
def login(data: LoginData):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, username, password, user_type FROM users WHERE username = ?", (data.username,))
    row = cur.fetchone()
    if not row or not verify_password(data.password, row[2]):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    token = create_access_token({"sub": row[1], "id": row[0], "user_type": row[3]})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/totp", response_model=List[TOTPOut])
def get_totps(user=Depends(get_current_user)):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, label, secret, is_default FROM totp_secrets WHERE user_id = ?", (user["id"],))
    rows = cur.fetchall()
    return [{
        "id": r[0],
        "label": r[1],
        "secret": r[2],
        "is_default": bool(r[3]),
        "code": pyotp.TOTP(r[2]).now()
    } for r in rows]

@app.post("/totp")
def add_totp(data: TOTPCreate, user=Depends(get_current_user)):
    conn = get_db()
    cur = conn.cursor()
    id_ = str(uuid.uuid4())
    cur.execute("INSERT INTO totp_secrets (id, user_id, secret, label, is_default) VALUES (?, ?, ?, ?, 0)",
                (id_, user["id"], data.secret, data.label))
    conn.commit()
    return {"msg": "Código adicionado"}

@app.put("/totp/default")
def set_default(label: str, user=Depends(get_current_user)):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE totp_secrets SET is_default = 0 WHERE user_id = ?", (user["id"],))
    cur.execute("UPDATE totp_secrets SET is_default = 1 WHERE user_id = ? AND label = ?", (user["id"], label))
    conn.commit()
    return {"msg": "Código padrão atualizado"}

@app.delete("/totp/{id}")
def delete_totp(id: str, user=Depends(get_current_user)):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM totp_secrets WHERE id = ? AND user_id = ?", (id, user["id"]))
    conn.commit()
    return {"msg": "Código excluído"}

@app.post("/change-password")
def change_password(data: PasswordChange, user=Depends(get_current_user)):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT password FROM users WHERE id = ?", (user["id"],))
    row = cur.fetchone()
    if not row or not verify_password(data.old_password, row[0]):
        raise HTTPException(status_code=400, detail="Senha antiga incorreta")
    cur.execute("UPDATE users SET password = ? WHERE id = ?", (hash_password(data.new_password), user["id"]))
    conn.commit()
    return {"msg": "Senha atualizada"}

@app.post("/users")
def create_user(data: UserCreate, user=Depends(get_current_user)):
    if user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Apenas admins podem criar usuários")
    conn = get_db()
    cur = conn.cursor()
    id_ = str(uuid.uuid4())
    cur.execute("INSERT INTO users (id, username, email, password, user_type) VALUES (?, ?, ?, ?, ?)",
                (id_, data.username, data.email, hash_password(data.password), data.user_type))
    conn.commit()
    return {"msg": "Usuário criado"}

@app.get("/users")
def list_users(user=Depends(get_current_user)):
    if user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Apenas admins podem ver os usuários")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, username, email, user_type FROM users")
    return [{"id": r[0], "username": r[1], "email": r[2], "user_type": r[3]} for r in cur.fetchall()]
