from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from passlib.context import CryptContext
from cryptography.fernet import Fernet
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi.openapi.utils import get_openapi

app = FastAPI()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory data stores
users_db = []
blogs_db = []

# Encryption key and Fernet instance
key = Fernet.generate_key()
fernet = Fernet(key)

# JWT settings
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

# Pydantic models
class User(BaseModel):
    email: EmailStr
    password: str

class Blog(BaseModel):
    title: str
    content: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Function to hash a password
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Function to encrypt text
def encrypt_text(text: str) -> str:
    return fernet.encrypt(text.encode()).decode()

# Function to decrypt text
def decrypt_text(text: str) -> str:
    return fernet.decrypt(text.encode()).decode()

# Function to authenticate a user
def authenticate_user(email: str, password: str):
    for user in users_db:
        if user["email"] == email and pwd_context.verify(password, user["password"]):
            return user
    return None

# Function to create a JWT token
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# OAuth2PasswordBearer instance
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Function to get current user
def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError as e:
        print(f"JWTError: {e}")
        raise credentials_exception
    user = next((user for user in users_db if user["email"] == token_data.email), None)
    if user is None:
        raise credentials_exception
    return user  # Return the user dictionary

# POST request to create a new user
@app.post("/user")
def create_user(user: User):
    hashed_password = hash_password(user.password)
    user_dict = user.dict()
    user_dict["password"] = hashed_password
    users_db.append(user_dict)
    return {"msg": "User created successfully"}

# POST request to get a JWT token
@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# GET request to retrieve all users (excluding passwords from the response)
@app.get("/users", response_model=List[EmailStr])
def get_users():
    return [user["email"] for user in users_db]

# GET request to retrieve raw user data
@app.get("/raw_users")
def get_raw_users():
    return users_db

# POST request to create a new blog, requires authentication
@app.post("/blog")
def create_blog(blog: Blog, current_user: User = Depends(get_current_user)):
    blog_dict = blog.dict()
    blog_dict["content"] = encrypt_text(blog.content)
    blogs_db.append(blog_dict)
    return {"msg": "Blog created successfully"}

# GET request to retrieve all blogs, requires authentication
@app.get("/blogs", response_model=List[Blog])
def get_blogs(current_user: User = Depends(get_current_user)):
    decrypted_blogs = [
        {**blog, "content": decrypt_text(blog["content"])} for blog in blogs_db
    ]
    return decrypted_blogs

# Custom OpenAPI schema to include Bearer token security scheme
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="FastAPI JWT Auth",
        version="1.0.0",
        description="API with JWT authentication",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            openapi_schema["paths"][path][method]["security"] = [
                {"BearerAuth": []}
            ]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Main entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)