import psycopg2

conn = psycopg2.connect(
    user='postgres',
    database='postgres',
    password='1',
    host='pg',
    port='5432'
)
cur = conn.cursor()


def create_table():
    query = '''CREATE TABLE orders(
    id         SERIAL PRIMARY KEY,
    user_id    varchar(255),
    pizza_name varchar(255),
    pizza_id   INTEGER NOT NULL,
    quantity   INTEGER NOT NULL,
    status     TEXT    NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
    );
    '''
    query1 = '''
    CREATE TABLE pizzas(
    id    SERIAL PRIMARY KEY,
    name  VARCHAR(255) NOT NULL,
    price INTEGER      NOT NULL
    );
    '''
    query2 = '''
    CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    user_id varchar(255),
    is_admin BOOLEAN DEFAULT FALSE
    );
    
    '''
    cur.execute(query)
    cur.execute(query1)
    cur.execute(query2)
    conn.commit()

