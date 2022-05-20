import sqlite3


def create_table():
    with sqlite3.connect('rpc_database.db') as conn:
        cur = conn.cursor()
        cur.execute("""CREATE TABLE users (
                    username text,
                    pswrd text,
                    email text,
                    wins integer,
                    losses integer
                    )""")


def signup(username, password, email):
    with sqlite3.connect('rpc_database.db') as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM users WHERE username='{username}'")
        if cur.fetchone() is None:
            cur.execute(f"INSERT INTO users VALUES ('{username}', '{password}', '{email}', 0, 0)")
            conn.commit()
            return True
        else:
            return False


def login(username, password):
    with sqlite3.connect('rpc_database.db') as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT pswrd FROM users WHERE username='{username}'")
        real_password = cur.fetchone()
        if real_password and real_password[0] == password:
            return True
        else:
            return False


def print_table():
    with sqlite3.connect('rpc_database.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users")
        result = cur.fetchall()
        for row in result:
            print(row)
        print('\r\n')


def add_win(username):
    with sqlite3.connect('rpc_database.db') as conn:
        cur = conn.cursor()
        cur.execute(f"UPDATE users SET wins = wins + 1 WHERE username = '{username}'")
        conn.commit()


def add_loss(username):
    with sqlite3.connect('rpc_database.db') as conn:
        cur = conn.cursor()
        cur.execute(f"UPDATE users SET losses = losses + 1 WHERE username = '{username}'")
        conn.commit()
