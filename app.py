from flask import Flask, jsonify, render_template, request
import sqlite3
import requests
import random

app = Flask(__name__)

# URL for getting Pokémon details
POKEAPI_URL = 'https://pokeapi.co/api/v2/pokemon/'
# URL for getting Pokémon TCG card data
TCGAPI_URL = 'https://api.pokemontcg.io/v2/cards'
# Your API Key for Pokémon TCG API
API_KEY = 'fd387a74-c7a7-42ac-be47-713540f4b69b'

# Function to get card data from the Pokémon TCG API
def fetch_cards_from_tcg_api(set_name):
    headers = {
        'X-Api-Key': API_KEY  # Add your API key here
    }
    try:
        # Request to get cards from the specified set
        response = requests.get(TCGAPI_URL, params={'q': f'set.name:"{set_name}"'}, headers=headers)
        response.raise_for_status()  # Check if request was successful
        data = response.json()  # Convert response to JSON format
        if 'data' in data:
            return data['data']  # Return the list of cards
        else:
            raise Exception(f"Unexpected API response structure: {data}")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from TCG API: {e}")
        raise Exception("Failed to fetch data from Pokemon TCG API")

# Function to pick random cards from a list
def get_random_cards(cards, num=5):
    return random.sample(cards, num)  # Pick random cards from the list

# Function to set up the database and create tables
def initialize_db():
    conn = sqlite3.connect('pokemon_booster.db')  # Connect to the database
    c = conn.cursor()  # Create a cursor object to interact with the database
    c.execute('DROP TABLE IF EXISTS user_cards')  # Drop existing tables if they exist
    c.execute('DROP TABLE IF EXISTS cards')
    c.execute('DROP TABLE IF EXISTS booster_packs')

    # Create table for storing card details
    c.execute('''
    CREATE TABLE IF NOT EXISTS cards (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        image_url TEXT,
        rarity TEXT
    )
    ''')

    # Create table for storing user card collection
    c.execute('''
    CREATE TABLE IF NOT EXISTS user_cards (
        user_id INTEGER,
        card_id TEXT,
        FOREIGN KEY(card_id) REFERENCES cards(id)
    )
    ''')

    # Create table for storing booster pack information
    c.execute('''
    CREATE TABLE IF NOT EXISTS booster_packs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
    ''')

    # Insert some example booster packs into the table
    c.executemany('INSERT INTO booster_packs (name) VALUES (?)',
                  [('Crown Zenith',), ('Lost Origin',), ('151',)])
    conn.commit()  # Save changes to the database
    conn.close()  # Close the connection to the database

# Function to save card information into the database
def save_card_to_db(card):
    conn = sqlite3.connect('pokemon_booster.db')
    c = conn.cursor()
    c.execute('''
    INSERT OR IGNORE INTO cards (id, name, image_url, rarity)
    VALUES (?, ?, ?, ?)
    ''', (card['id'], card['name'], card['images']['small'], card.get('rarity', 'Unknown')))
    conn.commit()
    conn.close()

# Function to save a list of cards to a user's collection
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

# Function to get the list of cards a user owns
def get_user_cards(user_id):
    conn = sqlite3.connect('pokemon_booster.db')
    c = conn.cursor()
    c.execute('''
    SELECT cards.id, cards.name, cards.image_url, cards.rarity
    FROM user_cards
    JOIN cards ON user_cards.card_id = cards.id
    WHERE user_cards.user_id = ?
    ''', (user_id,))
    cards = c.fetchall()  # Fetch all the user's cards
    conn.close()
    return cards

# Function to get details about a Pokémon
def fetch_pokemon_details(name):
    # Remove any extra descriptors like (Rare) or whitespace
    cleaned_name = name.lower().split(' ')[0].replace('(', '').replace(')', '')
    
    response = requests.get(POKEAPI_URL + cleaned_name)
    if response.status_code == 200:
        return response.json()  # Return the details of the Pokémon
    else:
        return None  # Return None if Pokémon is not found

# Function to get the list of available booster packs
def get_booster_packs():
    conn = sqlite3.connect('pokemon_booster.db')
    c = conn.cursor()
    c.execute('SELECT id, name FROM booster_packs')
    packs = c.fetchall()  # Fetch all booster packs
    conn.close()
    return packs

# Route for the home page
@app.route('/')
def index():
    booster_packs = get_booster_packs()  # Get the list of booster packs
    return render_template('index.html', booster_packs=booster_packs)  # Show the home page with booster packs

# Route to choose a booster pack and show cards
@app.route('/choose_pack/<int:pack_id>', methods=['POST'])
def choose_pack(pack_id):
    # Map pack ID to set name
    packs = {1: 'Crown Zenith', 2: 'Lost Origin', 3: '151'}
    set_name = packs.get(pack_id)
    if not set_name:
        return jsonify({"status": "error", "message": "Invalid pack ID"})  # Error if pack ID is not valid

    try:
        cards_data = fetch_cards_from_tcg_api(set_name)  # Get cards from the chosen pack
        selected_cards = get_random_cards(cards_data)  # Pick random cards

        # Save cards to the database
        for card in selected_cards:
            save_card_to_db(card)

        # Save user's selected cards
        save_user_cards(1, selected_cards)  # Assuming a single user with id=1

        return render_template('cards.html', cards=selected_cards)  # Show the selected cards
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})  # Error message if something goes wrong

# Route to show details of a Pokémon
@app.route('/pokemon/<string:card_name>', methods=['GET'])
def pokemon_details(card_name):
    details = fetch_pokemon_details(card_name)  # Get details of the Pokémon
    if details:
        return render_template('pokemon_details.html', pokemon=details)  # Show Pokémon details
    else:
        return render_template('non_pokemon.html', card_name=card_name)  # Show message if not a Pokémon

# Run the application
if __name__ == '__main__':
    initialize_db()  # Set up the database
    app.run(debug=True)  # Start the web application
