
from pydantic import BaseModel
class OrderCreate(BaseModel):
    user_id: int
    product_id: int
    quantity: int
from datetime import datetime
from fastapi import FastAPI, HTTPException
import os, psycopg
from psycopg.rows import dict_row
from db_migration import migrate_schema, seed_sample_data
from routers import users

DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    return psycopg.connect(DATABASE_URL, autocommit=True)

app = FastAPI()

app.include_router(users.router)

# Run DB migration
try:
    migrate_schema()
    seed_sample_data()
except Exception as e:
    print("ERROR: DB Migration failed:", str(e))


@app.get("/")
def get_root():
    return { "msg": "Clothing Store v0.2" }

# GET /categories 
@app.get("/categories")
def get_categories():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT category_id, name 
            FROM categories 
            ORDER BY category_id""")
        return cur.fetchall()

# GET /categories/{id}
@app.get("/categories/{category_id}")
def get_category(category_id: int):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT category_id, name 
            FROM categories 
            WHERE category_id = %s""", (category_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Category not found")
        return row

# POST /categories
@app.post("/categories", status_code=201)
def create_category(data: dict):
    name = data.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Missing 'name'")
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            INSERT INTO categories (
                name
            ) VALUES (
                %s
            ) RETURNING category_id""", (name,))
        return cur.fetchone()

# GET /products
@app.get("/products")
def get_products():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT p.product_id,
                   p.name AS product_name,
                   c.name AS category_name,
                   p.price,
                   p.stock
            FROM products p
            INNER JOIN categories c ON p.category_id = c.category_id
            ORDER BY p.product_id;
        """)
        return cur.fetchall()

# POST/orders        
@app.post("/orders", status_code=201)
def create_order(order: OrderCreate):
    customer_id = order.user_id
    product_id = order.product_id
    quantity = order.quantity

    if not all([customer_id, product_id, quantity]):
        raise HTTPException(400, "Missing user_id, product_id or quantity")

    with get_conn() as conn, conn.cursor() as cur:

        # Check product exists
        cur.execute("SELECT * FROM products WHERE product_id=%s", (product_id,))
        product = cur.fetchone()
        if not product:
            raise HTTPException(404, "Product not found")

        product_name = product[2]
        product_price = product[3]
        product_stock = product[4]

        if product_stock < quantity:
            raise HTTPException(400, "Not enough stock")

        # Create order (your table requires order_date)
        cur.execute("""
            INSERT INTO orders (customer_id, order_date)
            VALUES (%s, NOW())
            RETURNING order_id, order_date
        """, (customer_id,))
        order_row = cur.fetchone()

        order_id = order_row[0]
        created_at = order_row[1]

        # Create order item
        cur.execute("""
            INSERT INTO order_items (order_id, product_id, quantity, price)
            VALUES (%s, %s, %s, %s)
            RETURNING order_item_id
        """, (order_id, product_id, quantity, product_price))
        order_item = cur.fetchone()

        order_item_id = order_item[0]

        # Reduce stock
        cur.execute("""
            UPDATE products
            SET stock = stock - %s
            WHERE product_id = %s
        """, (quantity, product_id))

        return {
            "order_id": order_id,
            "created_at": created_at,
            "customer_id": customer_id,
            "items": [{
                "order_item_id": order_item_id,
                "product_id": product_id,
                "product_name": product_name,
                "price": float(product_price),
                "quantity": quantity,
                "total_price": float(product_price) * quantity
            }]
        }


# GET /statistics/users
@app.get("/statistics/users")
def statistics_users():
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
                SELECT
                    c.customer_id AS user_id,
                    c.first_name || ' ' || c.last_name AS user_name,
                    COUNT(o.order_id) AS order_count,
                    COALESCE(SUM(oi.quantity * oi.price), 0) AS total_spent
                FROM customers c
                LEFT JOIN orders o ON c.customer_id = o.customer_id
                LEFT JOIN order_items oi ON o.order_id = oi.order_id
                GROUP BY c.customer_id, c.first_name, c.last_name
                ORDER BY total_spent DESC;
            """)
            rows = cur.fetchall()
            result = [
                {
                    "user_id": row[0],
                    "user_name": row[1],
                    "order_count": row[2],
                    "total_spent": float(row[3])
                }
                for row in rows
            ]
            return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("ERROR in /statistics/users:", str(e))
        raise HTTPException(status_code=500, detail="Internal Server Error")

# GET /statistics/products
@app.get("/statistics/products")
def statistics_products():
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
                SELECT
                    p.product_id,
                    p.name AS product_name,
                    SUM(oi.quantity) AS units_sold,
                    COUNT(DISTINCT o.order_id) AS orders,
                    COALESCE(SUM(oi.quantity * oi.price), 0) AS turnover
                FROM products p
                LEFT JOIN order_items oi ON p.product_id = oi.product_id
                LEFT JOIN orders o ON oi.order_id = o.order_id
                GROUP BY p.product_id, p.name
                ORDER BY turnover DESC;
            """)
            rows = cur.fetchall()
            result = [
                {
                    "product_id": row[0],
                    "product_name": row[1],
                    "units_sold": row[2],
                    "orders": row[3],
                    "turnover": float(row[4])
                }
                for row in rows
            ]
            return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("ERROR in /statistics/products:", str(e))
        raise HTTPException(status_code=500, detail="Internal Server Error")