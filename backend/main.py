# main.py
from fastapi import FastAPI, Depends, HTTPException, status, Body
from fastapi.middleware.cors import CORSMiddleware
from models import init_db
from security import *
from schemas import *
from auth import get_current_user
from db import DatabaseManager, load_config, save_config
import pyotp
import uuid


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ou ["http://localhost:19006"] para ser mais seguro
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

db_instance = None

try:
    db_instance = DatabaseManager()
except Exception as e:
    print(f"[AVISO] Banco de dados ainda não configurado: {e}")


def get_db():
    global db_instance
    if db_instance is None:
        raise HTTPException(status_code=503, detail="Banco de dados não configurado.")
    return db_instance


@app.get("/config")
def get_config(user=Depends(get_current_user)):
    if user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem acessar esta rota.")
    config = load_config().copy()
    config.pop("password", None)  # nunca expõe senha
    return config

@app.post("/config")
def update_config(data: dict = Body(...), user=Depends(get_current_user) if db_instance else None):
    global db_instance  # <- COLOQUE ISSO AQUI, ANTES DE USAR db_instance

    if db_instance and user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem alterar configurações.")

    if "db_type" not in data:
        raise HTTPException(status_code=400, detail="Tipo de banco de dados obrigatório.")

    save_config(data)

    # Tenta reinicializar o banco com a nova config
    try:
        db_instance = DatabaseManager()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao conectar ao banco: {e}")

    return {"msg": "Configuração salva com sucesso e banco inicializado."}



@app.post("/login", response_model=Token)
def login(data: LoginData):
    db = get_db()
    user = db.fetchone("SELECT id, username, password, user_type FROM users WHERE username = ?", (data.username,))
    if not user or not verify_password(data.password, user[2]):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    token = create_access_token({"sub": user[1], "id": user[0], "user_type": user[3]})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/totp", response_model=List[TOTPOut])
def get_totps(user=Depends(get_current_user)):
    db = get_db()
    user = db.fetchone("SELECT id, label, secret, is_default FROM totp_secrets WHERE user_id = ?", (user["id"],))
    return [{
        "id": r[0],
        "label": r[1],
        "secret": r[2],
        "is_default": bool(r[3]),
        "code": pyotp.TOTP(r[2]).now()
    } for r in user]

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

@app.put("/users/{user_id}")
def edit_user(user_id: str, data: UserCreate, user=Depends(get_current_user)):
    if user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem editar usuários.")

    conn = get_db()
    try:
        conn.execute("UPDATE users SET username = ?, email = ?, user_type = ? WHERE id = ?",
                     (data.username, data.email, data.user_type, user_id))
        return {"msg": "Usuário atualizado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao atualizar usuário: {e}")

@app.delete("/users/{user_id}")
def delete_user(user_id: str, user=Depends(get_current_user)):
    if user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem excluir usuários.")

    conn = get_db()
    try:
        conn.execute("DELETE FROM totp_secrets WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        return {"msg": "Usuário e códigos associados excluídos com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao excluir usuário: {e}")

@app.post("/users/{user_id}/reset-password")
def reset_user_password(user_id: str, user=Depends(get_current_user)):
    if user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem resetar senhas.")

    conn = get_db()
    try:
        new_password = hash_password("123")
        conn.execute("UPDATE users SET password = ? WHERE id = ?", (new_password, user_id))
        return {"msg": "Senha resetada para '123'"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao resetar senha: {e}")
