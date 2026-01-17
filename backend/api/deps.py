from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import Depends,HTTPException,status
from fastapi.security import OAuth2PasswordBearer

from jose import JWTError, jwt
from dotenv import load_dotenv
import os
import bcrypt
from .database import SessionLocal

load_dotenv()

SECRET_KEY = os.getenv("AUTH_SECRET_KEY")
ALGORITHM = os.getenv("AUTH_ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

class Hash:
    @staticmethod
    def hash(password: str) -> str:
        pwd_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(pwd_bytes, salt)
        return hashed_password.decode('utf-8')

    @staticmethod
    def verify(plain_password: str, hashed_password: str) -> bool:
        password_bytes = plain_password.encode('utf-8')
        hash_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)

bcrypt_context = Hash()

oauth2_bearer = OAuth2PasswordBearer(tokenUrl="token")
oauth2_bearer_dependency = Annotated[str, Depends(oauth2_bearer)]

async def get_current_user(token:oauth2_bearer_dependency):
    try:
        payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id:int = payload.get("id")

        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Could not validate credentials")
        return {'username':username,'user_id':user_id}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Could not validate credentials")
    

user_dependency = Annotated[dict, Depends(get_current_user)]
