import os
from typing import Optional
from datetime import timedelta, timezone, datetime
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

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


def decode_token(token: str) -> dict:
    payload = jwt.decode(jwt=token, key=SECRETE_KEY, algorithms=ALGORITHM)
    return payload


def get_current_user(token: str = Depends(oauth2_scheme)):
    credential_exc = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                   detail="No autenticado", headers={"WWW-Authenticate": "Bearer"})

    try:
        payload = decode_token(token)
        sub: Optional[str] = payload.get('sub')
        username: Optional[str] = payload.get('username')
        if not sub or not username:
            raise credential_exc

        return {'email': sub, 'username': username}
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except InvalidTokenError:
        raise credential_exc
