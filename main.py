from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPBasic, HTTPBasicCredentials, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Union
from passlib.context import CryptContext
from cryptography.fernet import Fernet
from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi.openapi.utils import get_openapi

app = FastAPI()

# Auth0 Configuration
AUTH0_DOMAIN = "your-auth0-domain"
API_AUDIENCE = "https://your-api.com"
ALGORITHMS = ["RS256"]
SECRET_KEY = "your-secret-key"

# Authentication setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")
security = HTTPBasic()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory data stores
users_db = []
blogs_db = []

# Encryption key
key = Fernet.generate_key()
fernet = Fernet(key)

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

# Function to verify JWT token
def verify_token(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        return {"email": email}
    except JWTError:
        raise credentials_exception

# Function to verify username and password
def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    for user in users_db:
        if user["email"] == credentials.username and pwd_context.verify(credentials.password, user["password"]):
            return {"email": user["email"]}
    raise HTTPException(status_code=401, detail="Invalid credentials")

# Combined authentication dependency
def get_current_user(
    token_data: dict = Depends(verify_token),
    credentials: dict = Depends(verify_credentials)
):
    return token_data if token_data else credentials

# Endpoint to register a new user
@app.post("/user")
def create_user(user: User):
    hashed_password = pwd_context.hash(user.password)
    users_db.append({"email": user.email, "password": hashed_password})
    return {"msg": "User created successfully"}

# Endpoint to login and receive a JWT token
@app.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    for user in users_db:
        if user["email"] == form_data.username and pwd_context.verify(form_data.password, user["password"]):
            token_data = {"sub": user["email"], "exp": datetime.utcnow() + timedelta(hours=2)}
            token = jwt.encode(token_data, SECRET_KEY, algorithm="HS256")
            return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

# Protected route: Create a blog
@app.post("/blog")
def create_blog(blog: Blog, user: dict = Depends(get_current_user)):
    blogs_db.append(blog.dict())
    return {"msg": "Blog created successfully"}

# Protected route: Get all blogs
@app.get("/blogs", response_model=List[Blog])
def get_blogs(user: dict = Depends(get_current_user)):
    return blogs_db

# Custom OpenAPI schema to include Bearer token and Basic Auth security scheme
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
        },
        "BasicAuth": {
            "type": "http",
            "scheme": "basic",
        }
    }
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            openapi_schema["paths"][path][method]["security"] = [
                {"BearerAuth": []},
                {"BasicAuth": []}
            ]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Run FastAPI
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)