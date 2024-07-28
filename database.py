import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    'dbname': "meme_postgres",
    'user': "nika",
    'password': "nika20",
    'host': "localhost",
    'port': "5432"
}

def create_database():
    conn = psycopg2.connect(dbname='postgres', user=DB_CONFIG['user'], password=DB_CONFIG['password'], host=DB_CONFIG['host'])
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{DB_CONFIG['dbname']}'")
    exists = cursor.fetchone()
    if not exists:
        cursor.execute(f'CREATE DATABASE {DB_CONFIG["dbname"]}')
    cursor.close()
    conn.close()

# Создаем базу данных, если она не существует
create_database()

# Устанавливаем соединение с PostgreSQL
try:
    connection = psycopg2.connect(**DB_CONFIG)

    cur = connection.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS person(
            id SERIAL PRIMARY KEY,
            name VARCHAR(255),
            age INT
        );
    """)
    connection.commit()
    cur.close()
    connection.close()

except Exception as e:
    print(f"Не удалось установить соединение: {e}")

# смотрим на подписки юзера
def get_user_subscriptions(user_id):
    try:
        connection = psycopg2.connect(**DB_CONFIG)

        cursor = connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT * FROM subscriptions WHERE user_id = %s', (user_id,))
        user_subscriptions = cursor.fetchall()
        connection.close()
        return user_subscriptions
    except Exception as e:
        print(f"Ошибка при получении подписок пользователя: {e}")

def add_subscription(user_id, user_name, tarif, expiration_date):
    try:
        connection = psycopg2.connect(**DB_CONFIG)

        cursor = connection.cursor()
        cursor.execute(
            'INSERT INTO subscriptions (user_id, user_name, tarif, expiration_date) VALUES (%s, %s, %s, %s)',
            (user_id, user_name, tarif, expiration_date)
        )
        connection.commit()
        connection.close()
    except Exception as e:
        print(f"Ошибка при добавлении подписки: {e}")

def create_table():
    try:
        connection = psycopg2.connect(**DB_CONFIG)

        cursor = connection.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                user_name TEXT,
                tarif TEXT,
                expiration_date TIMESTAMP
            )
        ''')
        connection.commit()
        cursor.close()
        connection.close()
    except Exception as e:
        print(f"Ошибка при создании таблицы: {e}")

create_table()
