from fastapi import FastAPI
from pydantic import BaseModel, EmailStr
from typing import List
from passlib.context import CryptContext
from cryptography.fernet import Fernet

app = FastAPI()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory data stores
users_db = []
blogs_db = []

# Encryption key and Fernet instance
key = Fernet.generate_key()
fernet = Fernet(key)

# Pydantic models
class User(BaseModel):
    email: EmailStr
    password: str

class Blog(BaseModel):
    title: str
    content: str

# Function to hash a password
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Function to encrypt text
def encrypt_text(text: str) -> str:
    return fernet.encrypt(text.encode()).decode()

# Function to decrypt text
def decrypt_text(text: str) -> str:
    return fernet.decrypt(text.encode()).decode()

# POST request to create a new user
@app.post("/user")
def create_user(user: User):
    hashed_password = hash_password(user.password)
    user_dict = user.dict()
    user_dict["password"] = hashed_password
    users_db.append(user_dict)
    return {"msg": "User created successfully"}

# GET request to retrieve all users (excluding passwords from the response)
@app.get("/users", response_model=List[EmailStr])
def get_users():
    return [user["email"] for user in users_db]

# GET request to retrieve raw user data
@app.get("/raw_users")
def get_raw_users():
    return users_db

# POST request to create a new blog
@app.post("/blog")
def create_blog(blog: Blog):
    blog_dict = blog.dict()
    blog_dict["content"] = encrypt_text(blog.content)
    blogs_db.append(blog_dict)
    return {"msg": "Blog created successfully"}

# GET request to retrieve all blogs
@app.get("/blogs", response_model=List[Blog])
def get_blogs():
    decrypted_blogs = [
        {**blog, "content": decrypt_text(blog["content"])} for blog in blogs_db
    ]
    return decrypted_blogs

# GET request to retrieve raw blog data
@app.get("/raw_blogs")
def get_raw_blogs():
    return blogs_db

# Main entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)