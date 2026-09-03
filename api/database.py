import sqlite3
import math
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = DATA_DIR / "database.sqlite"


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with get_connection() as connection:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS samples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                rng_value INTEGER NOT NULL,
                image_path TEXT NOT NULL,
                algorithm TEXT NOT NULL,
                algorithm_version TEXT NOT NULL,
                used INTEGER NOT NULL DEFAULT 0
                    CHECK (used IN (0, 1))
            );

            CREATE TABLE IF NOT EXISTS rng_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sample_id INTEGER NOT NULL,
                requested_at TEXT NOT NULL,
                client TEXT,

                FOREIGN KEY (sample_id)
                    REFERENCES samples(id)
            );

            CREATE INDEX IF NOT EXISTS idx_samples_queue
                ON samples(used, id);

            CREATE INDEX IF NOT EXISTS idx_samples_timestamp
                ON samples(timestamp);

            CREATE INDEX IF NOT EXISTS idx_rng_requests_sample
                ON rng_requests(sample_id);
        """)

def add_sample(
    rng_value: int,
    image_path: str,
    algorithm: str,
    algorithm_version: str,
) -> int:
    if not 0 <= rng_value <= 4_294_967_295:
        raise ValueError("rng_value must be a 32-bit unsigned integer")

    timestamp = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO samples (
                timestamp,
                rng_value,
                image_path,
                algorithm,
                algorithm_version
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                timestamp,
                rng_value,
                image_path,
                algorithm,
                algorithm_version,
            ),
        )

        return cursor.lastrowid


def get_backlog_count() -> int:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT COUNT(*)
            FROM samples
            WHERE used = 0
            """
        ).fetchone()

        return row[0]


def consume_rng(client: Optional[str] = None):
    requested_at = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        sample = connection.execute(
            """
            SELECT *
            FROM samples
            WHERE used = 0
            ORDER BY id
            LIMIT 1
            """
        ).fetchone()

        if sample is None:
            return None

        connection.execute(
            """
            UPDATE samples
            SET used = 1
            WHERE id = ?
            """,
            (sample["id"],),
        )

        connection.execute(
            """
            INSERT INTO rng_requests (
                sample_id,
                requested_at,
                client
            )
            VALUES (?, ?, ?)
            """,
            (
                sample["id"],
                requested_at,
                client,
            ),
        )

        return sample

def get_samples(limit: int = 50, offset: int = 0):
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                timestamp,
                rng_value,
                image_path,
                algorithm,
                algorithm_version,
                used
            FROM samples
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()

        return rows


def get_sample(sample_id: int):
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT
                id,
                timestamp,
                rng_value,
                image_path,
                algorithm,
                algorithm_version,
                used
            FROM samples
            WHERE id = ?
            """,
            (sample_id,),
        ).fetchone()


def get_sample_count() -> int:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT COUNT(*) FROM samples"
        ).fetchone()

        return row[0]


def get_statistics():
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(used) AS consumed,
                MIN(rng_value) AS minimum,
                MAX(rng_value) AS maximum,
                AVG(rng_value) AS average
            FROM samples
            """
        ).fetchone()

        return row

def get_rng_values():
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT rng_value
            FROM samples
            ORDER BY id
            """
        ).fetchall()

        return [row["rng_value"] for row in rows]

def get_rng_quality(bucket_count: int = 100):
    values = get_rng_values()

    if not values:
        return {
            "sample_count": 0,
            "bucket_count": bucket_count,
            "mean": None,
            "standard_deviation": None,
            "chi_square": None,
            "degrees_of_freedom": bucket_count - 1,
        }

    sample_count = len(values)

    mean = sum(values) / sample_count

    variance = sum(
        (value - mean) ** 2
        for value in values
    ) / sample_count

    standard_deviation = math.sqrt(variance)

    bucket_size = 4_294_967_296 / bucket_count

    observed = [0] * bucket_count

    for value in values:
        index = min(
            int(value / bucket_size),
            bucket_count - 1,
        )
        observed[index] += 1

    expected = sample_count / bucket_count

    chi_square = sum(
        (count - expected) ** 2 / expected
        for count in observed
    )

    return {
        "sample_count": sample_count,
        "bucket_count": bucket_count,
        "mean": mean,
        "standard_deviation": standard_deviation,
        "chi_square": chi_square,
        "degrees_of_freedom": bucket_count - 1,
    }
