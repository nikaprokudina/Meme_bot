import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    'dbname': "meme_postgres",
    'user': "nika",
    'password': "nika20",
    'host': "localhost",
    'port': "5432"
}


# Устанавливаем соединение с PostgreSQL
try:
    connection = psycopg2.connect(**DB_CONFIG)

    cur = connection.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS person(
    id INT PRIMARY KEY,
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
    connection = psycopg2.connect(**DB_CONFIG)

    cursor = connection.cursor()
    cursor.execute(
        'INSERT INTO subscriptions (user_id, user_name, tarif, expiration_date) VALUES (%s, %s, %s, %s)',
        (user_id, user_name, tarif, expiration_date)
    )
    connection.commit()
    connection.close()

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

