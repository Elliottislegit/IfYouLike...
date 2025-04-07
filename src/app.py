from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Flask app with correct static and template folders
app = Flask(__name__, static_folder='static', template_folder='templates')

# Store credentials safely
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    # Basic search functionality will go here
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(debug=True)