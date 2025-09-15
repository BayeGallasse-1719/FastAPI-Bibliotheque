from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
from typing import Optional
from shema import TokenData, AdherentResponse
from fastapi import HTTPException, Depends
from database import DB_CONFIG

# variable local
load_dotenv()

# Parametre constante
SECRET_KEY = os.getenv('SECRET_KEY', 'changeme')
ALGORITHM = 'HS256'
TOKEN_EXPIRES = 30

# hashage mot de passe
pwd_contexte = CryptContext(schemes=['bcrypt'], deprecated = 'auto')

# shema d'authentifiaction
Oauth2_shema = OAuth2PasswordBearer(tokenUrl='token')

# fonctions de securite
def verify_pwd(plain_pwd: str, hashed_pwd: str):
    return pwd_contexte.verify(plain_pwd, hashed_pwd)

def get_pwd_hash(password: str):
    return pwd_contexte.hash(password)

def create_acces_token(data: dict, expire_delta: Optional[timedelta]=None):
    to_encode = data.copy()
    if expire_delta:
        expires = datetime.utcnow() + expire_delta
    else:
        expires = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRES)
    to_encode.update({'exp': expires})
    encode_jwt = jwt.encode(to_encode, key=SECRET_KEY, algorithm=ALGORITHM)
    return encode_jwt

def verify_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token invalide")
        return TokenData(email=email)
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Token invalide ou expire")

# dependances d'authentification
def get_current_adherent(token: str = Depends(Oauth2_shema)):
    conn = DB_CONFIG()
    cursor = conn.cursor()
    try:
        token_data = verify_token(token)
        cursor.execute("""SELECT id_adherent, nom_adherent, prenom_adherent, email, is_active
                        FROM adherents WHERE email = %s""", (token_data.email,))
        adherent = cursor.fetchone()
        if adherent is None:
            raise HTTPException(status_code=404, detail="Utilisateur introuvable")
        return AdherentResponse(
            id_adherent=adherent[0],
            nom_adherent=adherent[1],
            prenom_adherent=adherent[2],
            email=adherent[3],
            is_active=adherent[4]
        )
    finally:
        cursor.close()
        conn.close()


def get_adherent_active(current_adh: AdherentResponse=Depends(get_current_adherent)):
    if not current_adh.is_active:
        raise HTTPException(status_code=404, detail='Utilisateur inactive')
    return current_adh
    
