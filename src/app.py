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
    # Get the JSON data from the request
    data = request.json
    query = data.get('query', '')
    media_type = data.get('type', '')
    
    # For now, return mock results (your sample data)
    results = []
    
    for item in app_data['media_items']:
        if item['type'] == media_type and query.lower() in item['title'].lower():
            results.append(item)
    
    # Return the results as JSON
    return jsonify({"results": results})

@app.route('/get_recommendations', methods=['POST'])
def get_recommendations():
    # Get the selected item ID from the request
    data = request.json
    selected_id = data.get('item_id')
    
    # Find the selected item
    selected_item = None
    for item in app_data['media_items']:
        if item['id'] == selected_id:
            selected_item = item
            break
    
    if not selected_item:
        return jsonify({"error": "Item not found"}), 404
    
    # Find relationships for this item
    recommendations = []
    for relation in app_data['relationships']:
        # If this item is the source, recommend the target
        if relation['source_id'] == selected_id:
            target_id = relation['target_id']
            # Find the target item
            for item in app_data['media_items']:
                if item['id'] == target_id:
                    # Add recommendation info
                    recommendations.append({
                        "item": item,
                        "similarity_score": relation['similarity_score'],
                        "relationship_type": relation['relationship_type']
                    })
        
        # If this item is the target, recommend the source
        elif relation['target_id'] == selected_id:
            source_id = relation['source_id']
            # Find the source item
            for item in app_data['media_items']:
                if item['id'] == source_id:
                    # Add recommendation info
                    recommendations.append({
                        "item": item,
                        "similarity_score": relation['similarity_score'],
                        "relationship_type": relation['relationship_type']
                    })
    
    return jsonify({
        "selected_item": selected_item,
        "recommendations": recommendations
    })

# Add function to save data back to files
def save_data(filename, data):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    with open(os.path.join(data_dir, filename), 'w') as f:
        json.dump(data, f, indent=2)

if __name__ == '__main__':
    app.run(debug=True)