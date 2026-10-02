import psycopg2, psycopg2.extras
from config import settings
from shop_app import seed


def connect():
    return psycopg2.connect(settings.DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)


class Database:
    def __init__(self):
        self.conn = connect()

    def fetch_all(self, sql, args=()):
        with self.conn.cursor() as cur:
            cur.execute(sql, args)
            rows = cur.fetchall()
        self.conn.rollback()          # end read transaction so we always see fresh committed data
        return rows

    def fetch_one(self, sql, args=()):
        rows = self.fetch_all(sql, args)
        return rows[0] if rows else None

    def execute(self, sql, args=()):
        with self.conn.cursor() as cur:
            cur.execute(sql, args)
        self.conn.commit()

    def reset(self):
        seed.reset(self.conn)

    def close(self):
        self.conn.close()
