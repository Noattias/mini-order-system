import pika
import json

from pymongo import MongoClient
from datetime import datetime, timezone


# Connection to MongoDB
mongo_client = MongoClient("mongodb://mongodb:27017/")

# Database
mongo_db = mongo_client["orders_events_db"]

# Collection
events_collection = mongo_db["order_events"]


def process_order(ch, method, properties, body):
    order = json.loads(body)

    print("New order received:")
    print(order)

    event = {
        "event_type": "ORDER_RECEIVED",
        "order_id": order["order_id"],
        "customer": order["customer"],
        "item": order["item"],
        "quantity": order["quantity"],
        "status": order["status"],
        "received_at": datetime.now(timezone.utc)
    }

    result = events_collection.insert_one(event)

    print("Event saved to MongoDB:")
    print(result.inserted_id)

    ch.basic_ack(
        delivery_tag=method.delivery_tag
    )


connection = pika.BlockingConnection(
    pika.ConnectionParameters(host="rabbitmq")
)

channel = connection.channel()

channel.queue_declare(
    queue="orders_queue"
)

channel.basic_consume(
    queue="orders_queue",
    on_message_callback=process_order
)

print("Worker is waiting for messages...")

channel.start_consuming()