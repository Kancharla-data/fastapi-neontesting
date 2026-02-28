from fastapi import APIRouter, HTTPException
from psycopg.rows import dict_row
from db.connection import get_conn
from schemas import UserCreate, UserLogin
from auth import create_token, verify_password, hash_password

router = APIRouter()

# CREATE USER (POST /users)
@router.post("/users")
def create_user(user: UserCreate):
    conn = get_conn()
    cur = conn.cursor(row_factory=dict_row)

    # Check if email already exists
    cur.execute("SELECT * FROM customers WHERE email = %s", (user.email,))
    existing = cur.fetchone()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Insert new user
    print("PASSWORD RECEIVED:", user.password)
    print("PASSWORD LENGTH:", len(user.password))

    cur.execute(
        """
        INSERT INTO customers (name, email, password, role)
        VALUES (%s, %s, %s, %s)
        RETURNING id, name, email, role
        """,
        (user.name, user.email, hash_password(user.password), "customer")
    )

    new_user = cur.fetchone()

    cur.close()
    conn.close()

    return new_user

# LOGIN USER (POST /users/login)
@router.post("/users/login")
def login(credentials: UserLogin):
    conn = get_conn()
    cur = conn.cursor(row_factory=dict_row)

    # Fetch user by email
    cur.execute("SELECT * FROM customers WHERE email = %s", (credentials.email,))
    user = cur.fetchone()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Verify password
    if not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Create JWT token
    token = create_token({"sub": user["email"], "role": user["role"]})

    cur.close()
    conn.close()

    return {"access_token": token, "token_type": "bearer"}