# auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from security import decode_token
import sqlite3

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = decode_token(token)
        username: str = payload.get("sub")
        user_id: str = payload.get("id")
        user_type: str = payload.get("user_type")
        if username is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        return {"id": user_id, "username": username, "user_type": user_type}
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")
