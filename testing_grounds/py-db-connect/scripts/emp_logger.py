import uuid
import random
from datetime import datetime
import mysql.connector
import time

OUTPUT_FILE = "/data/op.txt"

DB_CONFIG = {
    "host": "db",          # service name in docker-compose
    "user": "myuser",
    "password": "mypass",
    "database": "mydatabase",
}

def ensure_table(conn):
    """Create table if it does not exist."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            no INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            uid VARCHAR(36) NOT NULL,
            time_of_entry DATETIME NOT NULL
        )
    """)
    conn.commit()
    cursor.close()

def insert_employee(conn):
    """Insert a new employee row."""
    names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank"]
    name = random.choice(names)
    uid = str(uuid.uuid4())
    time_of_entry = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO employees (name, uid, time_of_entry) VALUES (%s, %s, %s)",
        (name, uid, time_of_entry),
    )
    conn.commit()
    cursor.close()

def get_last_employee(conn):
    """Fetch the last inserted employee row."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees ORDER BY no DESC LIMIT 1")
    row = cursor.fetchone()
    cursor.close()
    return row

def write_to_file(row):
    """Write the last row into a text file."""
    with open(OUTPUT_FILE, "w") as f:
        f.write(f"no={row[0]}, name={row[1]}, uid={row[2]}, time_of_entry={row[3]}\n")

def main():
    conn = mysql.connector.connect(**DB_CONFIG)

    ensure_table(conn)
    insert_employee(conn)
    row = get_last_employee(conn)
    if row:
        write_to_file(row)

    conn.close()

if __name__ == "__main__":
    time.sleep(10)
    main()
