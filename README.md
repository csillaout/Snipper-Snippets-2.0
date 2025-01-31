# Snipper-Snippets-2.0

Snipper Snippets new/simple version

# FastAPI Blog and User Management

This FastAPI application provides a simple way to manage users and blogs with JWT authentication. Users can be created with their email and password, and blogs can be created with encrypted content. The application also provides endpoints to retrieve all users and blogs, with the content decrypted before returning it to the client.

## Features

- Create users with hashed passwords
- Create blogs with encrypted content
- Retrieve all users (excluding passwords)
- Retrieve all blogs with decrypted content
- JWT authentication for creating and retrieving blogs
- Interactive API documentation with Swagger UI

## Requirements

- Python 3.6+

## Setup

To get started with this project, follow these steps:

1. **Clone the repository:**

   ```sh
   git clone <repository_url>
   cd <repository_directory>
   ```

2. **Create a virtual environment:**

   ```sh
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the required dependencies:**

   ```sh
   pip install -r requirements.txt
   ```

4. **Run the FastAPI application:**

   ```sh
   uvicorn main:app --reload
   ```

## Usage

Once the server is running, you can access the application in your browser at `http://127.0.0.1:8000`.

### API Endpoints

- **Create User:**

  - **POST** `/user`
  - Body:
    ```json
    {
      "email": "user@example.com",
      "password": "yourpassword"
    }
    ```

- **Get All Users:**

  - **GET** `/users`
  - Response: List of user emails

- **Create Blog:**

  - **POST** `/blog`
  - Body:
    ```json
    {
      "title": "Blog Title",
      "content": "This is the blog content."
    }
    ```

- **Get All Blogs:**

  - **GET** `/blogs`
  - Response: List of blogs with decrypted content

### Swagger UI

FastAPI automatically generates interactive API documentation using Swagger UI. To access it, navigate to `http://127.0.0.1:8000/docs` in your browser. Here you can see all the available endpoints, their methods, and you can interact with them directly.

### Example Workflow

1. Create a User:

Use the POST /user endpoint to create a new user with an email and password.

2. Get JWT Token:

Use the POST /token endpoint with the email and password to get a JWT token.

3. Authorize with JWT Token:

In Swagger UI, click on the Authorize button, enter the token in the format Bearer <your_jwt_token>, and click Authorize.

4. Create a Blog:

Use the POST /blog endpoint to create a new blog post. Ensure you are authorized with the JWT token.

5. Get Blogs:

Use the GET /blogs endpoint to retrieve the list of blogs. Ensure you are authorized with the JWT token.
