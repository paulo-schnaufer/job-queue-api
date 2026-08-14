import os
from dotenv import load_dotenv
import psycopg2
from psycopg2 import extras

load_dotenv()

def get_connection():
    db_host = os.getenv("DB_HOST")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASSWORD")
    db_port = os.getenv("DB_PORT")

    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            host=db_host,
            port=db_port,
            password=db_pass,
        )
        extras.register_default_jsonb(conn)
        return conn
    except Exception as e:
        raise Exception(f"Can't connect. Details: {e}")