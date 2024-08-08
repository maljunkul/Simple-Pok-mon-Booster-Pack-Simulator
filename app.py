from flask import Flask, jsonify, request, render_template
import sqlite3
import requests
import random

app = Flask(__name__)

# Constants
POKEAPI_URL = 'https://pokeapi.co/api/v2/pokemon'
TCGAPI_URL = 'https://api.pokemontcg.io/v2/cards'

# Helper functions
def fetch_cards_from_tcg_api():
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

def get_user_money(user_id):
    conn = sqlite3.connect('pokemon_booster.db')
    c = conn.cursor()
    c.execute('SELECT money FROM users WHERE id = ?', (user_id,))
    money = c.fetchone()[0]
    conn.close()
    return money

def update_user_money(user_id, amount):
    conn = sqlite3.connect('pokemon_booster.db')
    c = conn.cursor()
    c.execute('UPDATE users SET money = money + ? WHERE id = ?', (amount, user_id))
    conn.commit()
    conn.close()

def choose_booster_pack():
    conn = sqlite3.connect('pokemon_booster.db')
    c = conn.cursor()
    c.execute('SELECT id, name, cost FROM booster_packs')
    packs = c.fetchall()
    conn.close()
    return packs

def get_booster_pack_cost(pack_id):
    conn = sqlite3.connect('pokemon_booster.db')
    c =conn.cursor()
    c.execute('SELECT cost FROM booster_packs WHERE id = ?', (pack_id))
    conn.close()
    return cost

def generate_card_from_booster_pack(pack):
    cards_data = fetch_cards_from_tcg_api()
    booster_pack = get_random_cards(cards_data, 5)
    return random.choice(booster_pack)

def get_card_value(card):
    # Implement a method to calculate card value (could be based on rarity or other factors)
    rarity_values = {'rare': 10, 'uncommon': 5, 'common': 1}
    return rarity_values.get(card.get('rarity', 'common'), 1)

def is_best_or_expensive_card(card):
    # Implement logic to determine if the card is particularly valuable or rare
    return card.get('rarity') in ['rare', 'ultra-rare']
# Routes
@app.route('/buy_booster_pack/<int:user_id>', methods=['POST'])
def buy_booster_pack(user_id):
    try:
        user_money = get_user_money(user_id)
        booster_packs = choose_booster_pack()

        if not booster_packs:
            return jsonify ({"status": "error", "message": "No booster packs available"})
        
        pack_id = random.choice([pack[0] for pack in booster_packs])
        pack_cost = get_booster_pack_cost(pack_id)

        if user_money >= pack_cost:
            update_user_money(user_id, -pack_cost)
            new_card = generate_card_from_booster_pack(pack_id)

            card_id = new_card['id']
            card_name = new_card['name']
            card_image_url = new_card['images']['small']
            card_rarity = new_card.get('rarity', 'Unknown')

            conn = sqlite3.connect('pokemon_booster.db')
            c = conn.cursor()

            c.execute('''
            INSERT OR IGNORE INTO cards (id, name, image_url, rarity)
            VALUES (?, ?, ?, ?)
            ''', (card_id, card_name, card_image_url, card_rarity))
            
            c.execute('''
            INSERT OR IGNORE INTO user_cards (user_id, card_id)
            VALUES (?, ?)
            ''', (user_id, card_id))
            
            conn.commit()
            conn.close()
            
            if is_best_or_expensive_card(new_card):
                message = "Congratulations! You got a valuable card!"
            
            else:
                message = "You got a card.Try again for a better one!"

            return jsonify({"status": "success",  "message":message, "card": new_card})
        else:
            return jsonify({"status": "error","message": "Not enough money to buy a booster pack."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
    

@app.route('/user_collection/<int:user_id>', methods=['GET'])
def user_collection(user_id):
    try:
        cards = get_user_cards(user_id)
        return render_template('collection.html', cards=cards)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
    
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)