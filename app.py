from flask import Flask, jsonify, render_template, request
import sqlite3
import requests
import random

app = Flask(__name__)

# Constants
POKEAPI_URL = 'https://pokeapi.co/api/v2/pokemon/'
TCGAPI_URL = 'https://api.pokemontcg.io/v2/cards'
API_KEY = 'fd387a74-c7a7-42ac-be47-713540f4b69b'  # Your API Key

# Helper functions
def fetch_cards_from_tcg_api(set_name):
    headers = {
        'X-Api-Key': API_KEY
    }
    try:
        response = requests.get(TCGAPI_URL, params={'q': f'set.name:"{set_name}"'}, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        if 'data' in data:
            return data['data']
        else:
            raise Exception(f"Unexpected API response structure: {data}")
    except requests.exceptions.RequestException as e:
        # Log the exception and return an error message
        print(f"Error fetching data from TCG API: {e}")
        raise Exception("Failed to fetch data from Pokemon TCG API")

def get_random_cards(cards, num=5):
    return random.sample(cards, num)

def initialize_db():
    conn = sqlite3.connect('pokemon_booster.db')
    c = conn.cursor()
    c.execute('DROP TABLE IF EXISTS user_cards')
    c.execute('DROP TABLE IF EXISTS cards')
    c.execute('DROP TABLE IF EXISTS booster_packs')

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
        FOREIGN KEY(card_id) REFERENCES cards(id)
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS booster_packs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
    ''')

    c.executemany('INSERT INTO booster_packs (name) VALUES (?)',
                  [('Crown Zenith',), ('Lost Origin',), ('151',)])
    conn.commit()
    conn.close()

def save_card_to_db(card):
    conn = sqlite3.connect('pokemon_booster.db')
    c = conn.cursor()
    c.execute('''
    INSERT OR IGNORE INTO cards (id, name, image_url, rarity)
    VALUES (?, ?, ?, ?)
    ''', (card['id'], card['name'], card['images']['small'], card.get('rarity', 'Unknown')))
    conn.commit()
    conn.close()

def save_user_cards(user_id, cards):
    conn = sqlite3.connect('pokemon_booster.db')
    c = conn.cursor()
    for card in cards:
        c.execute('''
        INSERT INTO user_cards (user_id, card_id)
        VALUES (?, ?)
        ''', (user_id, card['id']))
    conn.commit()
    conn.close()

def get_user_cards(user_id):
    conn = sqlite3.connect('pokemon_booster.db')
    c = conn.cursor()
    c.execute('''
    SELECT cards.id, cards.name, cards.image_url, cards.rarity
    FROM user_cards
    JOIN cards ON user_cards.card_id = cards.id
    WHERE user_cards.user_id = ?
    ''', (user_id,))
    cards = c.fetchall()
    conn.close()
    return cards

def fetch_pokemon_details(name):
    response = requests.get(POKEAPI_URL + name.lower())
    if response.status_code == 200:
        return response.json()
    else:
        return None

def get_booster_packs():
    conn = sqlite3.connect('pokemon_booster.db')
    c = conn.cursor()
    c.execute('SELECT id, name FROM booster_packs')
    packs = c.fetchall()
    conn.close()
    return packs

# Routes
@app.route('/')
def index():
    booster_packs = get_booster_packs()
    return render_template('index.html', booster_packs=booster_packs)

@app.route('/choose_pack/<int:pack_id>', methods=['POST'])
def choose_pack(pack_id):
    packs = {1: 'Crown Zenith', 2: 'Lost Origin', 3: '151'}
    set_name = packs.get(pack_id)
    if not set_name:
        return jsonify({"status": "error", "message": "Invalid pack ID"})

    try:
        cards_data = fetch_cards_from_tcg_api(set_name)
        selected_cards = get_random_cards(cards_data)

        # Save cards to the database
        for card in selected_cards:
            save_card_to_db(card)

        # Save user's selected cards
        save_user_cards(1, selected_cards)  # Assuming a single user with id=1

        return render_template('cards.html', cards=selected_cards)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/pokemon/<string:card_name>', methods=['GET'])
def pokemon_details(card_name):
    details = fetch_pokemon_details(card_name)
    if details:
        return render_template('pokemon_details.html', pokemon=details)
    else:
        return jsonify({"status": "error", "message": "Pokemon not found"})
    
@app.route('/pokemon/<string:card_name>', methods=['GET'])
def pokemon_details(card_name):
    details = fetch_pokemon_details(card_name)
    
    if details:
        return render_template('pokemon_details.html', pokemon=details)
    else:
        # If the card is not a Pokémon, skip the API call and show a message.
        return render_template('non_pokemon.html', card_name=card_name)


if __name__ == '__main__':
    initialize_db()
    app.run(debug=True)
