# Backend/api/auth.py
import json
import hashlib
import secrets
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

USERS_FILE  = Path(__file__).parent.parent / "data" / "users.json"
TOKENS_FILE = Path(__file__).parent.parent / "data" / "tokens.json"

# TTL de sesión: 8 horas
TOKEN_TTL_HORAS = 8

# ── Persistencia de tokens ────────────────────────────────────────────────────

def _cargar_tokens() -> dict:
    """Lee tokens guardados en disco, descarta los expirados al cargar."""
    try:
        with open(TOKENS_FILE, "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

    ahora = datetime.now()
    vigentes = {}
    for token, info in data.items():
        try:
            creado = datetime.fromisoformat(info["created_at"])
            if ahora - creado < timedelta(hours=TOKEN_TTL_HORAS):
                vigentes[token] = info
        except Exception:
            pass   # token con formato inválido → descartar
    return vigentes


def _guardar_tokens(tokens: dict):
    """Escribe el dict de tokens activos en disco."""
    try:
        TOKENS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TOKENS_FILE, "w") as f:
            json.dump(tokens, f, indent=2)
    except Exception as e:
        print(f"[auth] Warning: no se pudo guardar tokens.json: {e}")


# Cargar tokens al iniciar el módulo
active_tokens: dict = _cargar_tokens()


# ── Usuarios ──────────────────────────────────────────────────────────────────

def cargar_usuarios():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def validar_usuario(username: str, password: str) -> Optional[dict]:
    """
    Valida credenciales. Retorna {username, role} si son correctas, None si no.
    """
    usuarios = cargar_usuarios()
    password_hash = hash_password(password)
    for u in usuarios:
        if u["username"] == username and u["password"] == password_hash:
            return {"username": u["username"], "role": u.get("role", "tecnico")}
    return None


# ── Tokens ────────────────────────────────────────────────────────────────────

def crear_token(username: str, role: str = "tecnico") -> str:
    """Crea un token de sesión, lo guarda en memoria y en disco."""
    token = secrets.token_urlsafe(32)
    active_tokens[token] = {
        "username": username,
        "role": role,
        "created_at": datetime.now().isoformat()
    }
    _guardar_tokens(active_tokens)
    return token


def validar_token(token: str) -> Optional[dict]:
    """
    Valida token: verifica existencia y TTL.
    Retorna los datos del usuario o None si es inválido/expirado.
    """
    info = active_tokens.get(token)
    if not info:
        return None
    try:
        creado = datetime.fromisoformat(info["created_at"])
        if datetime.now() - creado >= timedelta(hours=TOKEN_TTL_HORAS):
            # Expirado — limpiar
            del active_tokens[token]
            _guardar_tokens(active_tokens)
            return None
    except Exception:
        return None
    return info


def eliminar_token(token: str):
    """Elimina un token (logout) y persiste el cambio."""
    if token in active_tokens:
        del active_tokens[token]
        _guardar_tokens(active_tokens)
