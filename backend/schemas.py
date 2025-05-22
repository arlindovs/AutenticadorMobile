# schemas.py
from pydantic import BaseModel
from typing import Optional, List

class Token(BaseModel):
    access_token: str
    token_type: str

class LoginData(BaseModel):
    username: str
    password: str

class TOTPCreate(BaseModel):
    label: str
    secret: str

class TOTPOut(BaseModel):
    id: str
    label: str
    code: str
    is_default: bool

class UserCreate(BaseModel):
    username: str
    email: Optional[str]
    password: str
    user_type: str

class PasswordChange(BaseModel):
    old_password: str
    new_password: str
