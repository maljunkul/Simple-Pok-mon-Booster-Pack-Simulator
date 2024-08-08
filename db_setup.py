import sqlite3

def initialize_db():
    conn = sqlite3.connect('pokemon_booster.db')
    c = conn.cursor()

    # Create tables
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        money INTEGER DEFAULT 0
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS cards (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        image_url TEXT,
        rarity TEXT
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS user_cards (
        user_id INTEGER,
        card_id TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(card_id) REFERENCES cards(id),
        PRIMARY KEY(user_id, card_id)
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS booster_packs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        cost INTEGER NOT NULL
    )
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    initialize_db()