import json
import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify

# Load environment variables / obscuring sensitive data
load_dotenv()

# Create Flask app with correct static and template folders
app = Flask(__name__, static_folder='static', template_folder='templates')

# Store credentials safely
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# Define data loading function
def load_data():
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    
    # Create data directory if it doesn't exist
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # Load media items
    try:
        with open(os.path.join(data_dir, 'media_items.json'), 'r') as f:
            media_items = json.load(f)
    except FileNotFoundError:
        # Initialize with empty list if file doesn't exist
        media_items = []
    
    # Load relationships
    try:
        with open(os.path.join(data_dir, 'relationships.json'), 'r') as f:
            relationships = json.load(f)
    except FileNotFoundError:
        # Initialize with empty list if file doesn't exist
        relationships = []  # Fixed variable name

    # Load users
    try:
        with open(os.path.join(data_dir, 'users.json'), 'r') as f:
            users = json.load(f)
    except FileNotFoundError:
        # Initialize with empty list if file doesn't exist
        users = []  # Fixed variable name
    
    return {
        'media_items': media_items,
        'relationships': relationships,
        'users': users
    }

# Initialize data
app_data = load_data()  # Actually call the function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    # Basic search functionality will go here
    return jsonify({"status": "success"})

# Add function to save data back to files
def save_data(filename, data):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    with open(os.path.join(data_dir, filename), 'w') as f:
        json.dump(data, f, indent=2)

if __name__ == '__main__':
    app.run(debug=True)