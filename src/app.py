from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Access your API keys
spotify_client_id = os.getenv("SPOTIFY_CLIENT_ID")
spotify_client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
tmdb_api_key = os.getenv("TMDB_API_KEY")
tmdb_token = os.getenv("TMDB_READ_ACCESS_TOKEN")

# Now you can use these variables safely in your API calls