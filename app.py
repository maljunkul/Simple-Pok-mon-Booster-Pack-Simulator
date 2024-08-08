from flask import Flask, jsonify, request, render_template
import sqlite3
import requests
import random

app = Flash(__name__)

# Constants
POKEAPI_URL = 'https://pokeapi.co/api/v2/pokemon'
TCGAPI_URL = 'https://api.pokemontcg.io/v2/cards'

# Helper functions
def fetch_card_from_tcg_api():
    response = requests.get(TCGAPI_URL)
    if response.status_code == 200:
        return response.json()['data']
    else:
        raise Exception("Failed to fetch data from Pokemon TCG API")

def get_random_cards(cards, num = 5):
    return random.sample(cards, num)

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


# Routes
@app.route('/buy_booster_pack/<int:user_id>', methods=['POST'])
def buy_booster_pack(user_id):
    try:
        cards_data = fetch_cards_from_tcg_api()
        booster_pack = get_random_cards(cards_data, 5)

        conn =sqlite3.connect('pokemon_booster.db')
        c = conn.cursor()

        for card in booster_pack:
            card_id = card['id']
            c.execute('''
            INSERT OR IGNORE INTO cards (id, name, image_url, rarity)
            VALUES (?, ?, ?, ?)
            ''', (card_id, card['name'], card['images']['small'], card['rarity']))
            c.execute('''
            INSERT OR IGNORE INTO user_cards (user_id, card_id)
            VALUES (?, ?)
            ''', (user_id, card_id))
        
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "cards": booster_pack})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
    
@app.route