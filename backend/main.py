from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import pika
import json

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db_connection():
    return psycopg2.connect(
        host="postgres",
        database="ordersdb",
        user="ordersuser",
        password="orderspass",
        port="5432"
    )

def send_order_message(order):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host="rabbitmq")
    )

    channel = connection.channel()

    channel.queue_declare(queue="orders_queue")

    channel.basic_publish(
        exchange="",
        routing_key="orders_queue",
        body=json.dumps(order)
    )

    connection.close()

@app.get("/")
def home():
    return {
        "message": "Welcome to Mini Order System"
    }


@app.get("/api/menu")
def get_menu():
    return {
        "menu": [
            {"id": 1, "item": "Burger", "price": 50},
            {"id": 2, "item": "Pizza", "price": 45},
            {"id": 3, "item": "Pasta", "price": 55}
        ]
    }


@app.get("/api/orders")
def get_orders():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT id, customer, item, quantity, status FROM orders ORDER BY id"
    )

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    orders = []

    for row in rows:
        orders.append({
            "id": row[0],
            "customer": row[1],
            "item": row[2],
            "quantity": row[3],
            "status": row[4]
        })

    return {"orders": orders}


@app.post("/api/orders")
def create_order(order: dict):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO orders (customer, item, quantity, status)
        VALUES (%s, %s, %s, %s)
        RETURNING id
        """,
        (
            order["customer"],
            order["item"],
            order["quantity"],
            "Processing"
        )
    )

    order_id = cursor.fetchone()[0]

    connection.commit()

    message = {
    "order_id": order_id,
    "customer": order["customer"],
    "item": order["item"],
    "quantity": order["quantity"],
    "status": "Processing"
}

    send_order_message(message)

    cursor.close()
    connection.close()

    return {
        "message": "Order saved successfully",
        "order_id": order_id,
        "status": "Processing"
    }