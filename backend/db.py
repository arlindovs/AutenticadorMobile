# db.py
import sqlite3
import mysql.connector
import psycopg2
from cryptography.fernet import Fernet
import os
import json

KEY_FILE = "encryption_key.key"
CONFIG_FILE = "config.json"

# Garante a chave de criptografia
def load_encryption_key():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
    else:
        with open(KEY_FILE, "rb") as f:
            key = f.read()
    return key

FERNET = Fernet(load_encryption_key())

def load_config():
    if not os.path.exists(CONFIG_FILE):
        raise Exception("Arquivo de configuração não encontrado.")
    with open(CONFIG_FILE, "rb") as f:
        encrypted = f.read()
    decrypted = FERNET.decrypt(encrypted).decode()
    return json.loads(decrypted)

def save_config(config: dict):
    encrypted = FERNET.encrypt(json.dumps(config).encode())
    with open(CONFIG_FILE, "wb") as f:
        f.write(encrypted)

class DatabaseManager:
    def __init__(self):
        self.config = load_config()
        self.conn = self._connect()
        self._init_tables()

    def _connect(self):
        db_type = self.config["db_type"]
        if db_type == "sqlite":
            return sqlite3.connect(self.config.get("db_path", "authenticator.db"), check_same_thread=False)
        elif db_type == "mysql":
            return mysql.connector.connect(
                host=self.config["host"],
                user=self.config["user"],
                password=self.config["password"],
                port=self.config.get("port", 3306),
                database=self.config.get("database", "authenticator")
            )
        elif db_type == "postgres":
            return psycopg2.connect(
                host=self.config["host"],
                user=self.config["user"],
                password=self.config["password"],
                port=self.config.get("port", 5432),
                database=self.config.get("database", "authenticator")
            )
        else:
            raise Exception("Tipo de banco inválido.")

    def _init_tables(self):
        cursor = self.conn.cursor()
        db_type = self.config["db_type"]

        # SQL adaptado para cada banco
        if db_type == "sqlite":
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
        else:
            int_type = "TINYINT(1)" if db_type == "mysql" else "BOOLEAN"
            cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                                                                   id VARCHAR(36) PRIMARY KEY,
                username VARCHAR(255) UNIQUE,
                email VARCHAR(255),
                password VARCHAR(255),
                user_type VARCHAR(50)
                )''')
            cursor.execute(f'''CREATE TABLE IF NOT EXISTS totp_secrets (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36),
                secret VARCHAR(255),
                label VARCHAR(255),
                is_default {int_type},
                FOREIGN KEY (user_id) REFERENCES users(id)
            )''')

        self.conn.commit()

    def execute(self, query, params=()):
        cur = self.conn.cursor()
        if self.config["db_type"] in ("mysql", "postgres"):
            query = query.replace("?", "%s")
        cur.execute(query, params)
        self.conn.commit()
        return cur

    def fetchone(self, query, params=()):
        cur = self.execute(query, params)
        return cur.fetchone()

    def fetchall(self, query, params=()):
        cur = self.execute(query, params)
        return cur.fetchall()
