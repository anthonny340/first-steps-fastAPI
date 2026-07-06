import os
from typing import Optional
from datetime import timedelta, timezone, datetime
from fastapi.security import OAuth2PasswordBearer
import jwt

# Se puede configurar un valor alternativo por defecto en caso de que no puede leer correctamente alguna varible de entorno
# Se lo realizaria de la siguiente forma:   SECRETE_KEY = os.getenv('SECRETE_KEY', 'ALTERNATIVA_AQUI')
# Obviamente esto no es recomendable en produccion por temas de seguridad
SECRETE_KEY = os.getenv('SECRETE_KEY')
ALGORITHM = os.getenv('ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '30'))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def create_access_token(data: dict, expire_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(
        tz=timezone.utc) + (expire_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({'exp': expire})
    token = jwt.encode(payload=to_encode, key=SECRETE_KEY, algorithm=ALGORITHM)

    return token


def decode_token():
    pass
