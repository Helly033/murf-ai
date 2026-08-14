import sqlite3
from datetime import datetime

DB_PATH = "call_analytics.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            call_id TEXT UNIQUE,
            room_name TEXT,
            start_time TEXT,
            end_time TEXT,
            duration INTEGER DEFAULT 0,
            status TEXT,
            outcome TEXT,
            human_handoff INTEGER DEFAULT 0,
            transcript TEXT
        )
    """)

    conn.commit()
    conn.close()


def create_call(call_id, room_name):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO calls
        (call_id, room_name, start_time, status)
        VALUES (?, ?, ?, ?)
    """, (
        call_id,
        room_name,
        datetime.now().isoformat(),
        "active"
    ))

    conn.commit()
    conn.close()


def finish_call(call_id, status="completed", outcome="completed",
                human_handoff=False, transcript=""):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT start_time
        FROM calls
        WHERE call_id = ?
    """, (call_id,))

    row = cursor.fetchone()

    if row:
        start_time = datetime.fromisoformat(row[0])
        end_time = datetime.now()
        duration = int((end_time - start_time).total_seconds())

        cursor.execute("""
            UPDATE calls
            SET end_time = ?,
                duration = ?,
                status = ?,
                outcome = ?,
                human_handoff = ?,
                transcript = ?
            WHERE call_id = ?
        """, (
            end_time.isoformat(),
            duration,
            status,
            outcome,
            int(human_handoff),
            transcript,
            call_id
        ))

    conn.commit()
    conn.close()


def get_all_calls():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM calls
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return rows


if __name__ == "__main__":
    init_db()
    print("Call analytics database initialized successfully.")