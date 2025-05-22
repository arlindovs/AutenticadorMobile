# models.py
import sqlite3
import uuid
from security import hash_password

def init_db():
    conn = sqlite3.connect("authenticator.db")
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                                                           id TEXT PRIMARY KEY,
                                                           username TEXT UNIQUE,
                                                           email TEXT,
                                                           password TEXT,
                                                           user_type TEXT
                      )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS totp_secrets (
                                                                  id TEXT PRIMARY KEY,
                                                                  user_id TEXT,
                                                                  secret TEXT,
                                                                  label TEXT,
                                                                  is_default INTEGER,
                                                                  FOREIGN KEY (user_id) REFERENCES users(id)
        )''')

    # Verifica se o usuário admin já existe
    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    if cursor.fetchone() is None:
        user_id = str(uuid.uuid4())
        hashed = hash_password("admin")
        cursor.execute('''INSERT INTO users (id, username, email, password, user_type)
                          VALUES (?, ?, ?, ?, ?)''',
                       (user_id, 'admin', 'admin@example.com', hashed, 'admin'))
        print("[INFO] Usuário admin criado com a senha padrão.")

    conn.commit()
    conn.close()
