import json
import os
import requests
from urllib.parse import quote_plus
import re
import time
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, Response, send_file
import threading
import hashlib
import random

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

app = Flask(__name__, static_folder='static', template_folder='templates')

tmdb_key = os.getenv('TMDB_API_KEY')

# ===== CACHING IMPLEMENTATION =====

# Simple in-memory cache implementation
cache = {}
cache_lock = threading.Lock()  # Thread-safe operations

# Cache configuration
CACHE_TIMEOUT = {
    'api_request': 3600,    # 1 hour for general API requests
    'book_details': 86400,  # 24 hours for book details
    'movie_details': 86400  # 24 hours for movie details
}

def get_cache_key(prefix, *args, **kwargs):
    """Generate a unique cache key based on function arguments"""
    key_parts = [prefix]
    # Add all args and kwargs to the key
    for arg in args:
        key_parts.append(str(arg))
    for k, v in sorted(kwargs.items()):
        key_parts.append(f"{k}:{v}")
    # Create a hash of the combined string
    key_string = ":".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()

def cached(cache_type):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = get_cache_key(func.__name__, *args, **kwargs)
            
            # Try to get from cache
            with cache_lock:
                cache_item = cache.get(cache_key)
                
                # If found and not expired, return cached value
                if cache_item:
                    timestamp, value = cache_item
                    if time.time() - timestamp < CACHE_TIMEOUT.get(cache_type, 3600):
                        return value
            
            # Call the function if not cached or expired
            result = func(*args, **kwargs)
            
            # Cache the result
            with cache_lock:
                cache[cache_key] = (time.time(), result)
            
            return result
        return wrapper
    return decorator

# ===== CURATED DATA =====

# Curated dataset for popular books to ensure quality recommendations
CURATED_BOOKS = {
    'dune': {
        'title': 'Dune',
        'genres': ['science fiction', 'space opera', 'political intrigue', 'desert planet', 'ecology'],
        'related_books': ['foundation', 'hyperion', 'left-hand-of-darkness', 'enders-game'],
        'related_movies': ['star wars', 'avatar', 'arrival', 'blade runner 2049']
    },
    'the lord of the rings': {
        'title': 'The Lord of the Rings',
        'genres': ['fantasy', 'epic', 'adventure', 'quest', 'good vs evil'],
        'related_books': ['the hobbit', 'game of thrones', 'wheel of time', 'earthsea'],
        'related_movies': ['harry potter', 'the hobbit', 'willow', 'stardust']
    },
    'harry potter': {
        'title': 'Harry Potter',
        'genres': ['fantasy', 'magic', 'coming of age', 'boarding school', 'friendship'],
        'related_books': ['percy jackson', 'his dark materials', 'earthsea', 'neverwhere'],
        'related_movies': ['fantastic beasts', 'the chronicles of narnia', 'the sorcerers apprentice']
    },
    'warhammer 40k': {
        'title': 'Warhammer 40K',
        'genres': ['science fiction', 'military', 'space', 'dystopian', 'war', 'grimdark'],
        'related_books': ['starship troopers', 'forever war', 'old mans war', 'armor'],
        'related_movies': ['starship troopers', 'aliens', 'edge of tomorrow', 'enders game']
    },
    'eisenhorn': {
        'title': 'Eisenhorn',
        'genres': ['science fiction', 'detective', 'inquisition', 'warhammer 40k', 'military'],
        'related_books': ['ravenor', 'gaunts ghosts', 'horus heresy', 'ciaphas cain'],
        'related_movies': ['blade runner', 'detective fiction', 'sci-fi noir', 'alien']
    },
    'foundation': {
        'title': 'Foundation',
        'genres': ['science fiction', 'galactic empire', 'psychohistory', 'future history', 'space'],
        'related_books': ['dune', 'hyperion', 'asimovs robot series', 'revelation space'],
        'related_movies': ['interstellar', 'arrival', '2001 a space odyssey']
    },
    'enders game': {
        'title': 'Ender\'s Game',
        'genres': ['science fiction', 'military', 'space', 'child soldiers', 'aliens'],
        'related_books': ['old mans war', 'the forever war', 'starship troopers'],
        'related_movies': ['the last starfighter', 'edge of tomorrow', 'starship troopers']
    },
    '1984': {
        'title': '1984',
        'genres': ['dystopian', 'political fiction', 'social science fiction', 'surveillance state'],
        'related_books': ['brave new world', 'fahrenheit 451', 'we', 'handmaids tale'],
        'related_movies': ['v for vendetta', 'equilibrium', 'minority report', 'gattaca']
    },
    'to kill a mockingbird': {
        'title': 'To Kill a Mockingbird',
        'genres': ['southern gothic', 'legal drama', 'coming of age', 'racism', 'social issues'],
        'related_books': ['the help', 'go set a watchman', 'the color purple', 'the secret life of bees'],
        'related_movies': ['the help', 'hidden figures', 'just mercy', 'mississippi burning']
    },
    'pride and prejudice': {
        'title': 'Pride and Prejudice',
        'genres': ['romance', 'regency', 'social satire', 'marriage', 'class'],
        'related_books': ['sense and sensibility', 'emma', 'jane eyre', 'wuthering heights'],
        'related_movies': ['sense and sensibility', 'emma', 'little women', 'bridgerton']
    },
    'frankenstein': {
        'title': 'Frankenstein',
        'genres': ['horror', 'gothic', 'science fiction', 'romanticism', 'creation'],
        'related_books': ['dracula', 'jekyll and hyde', 'picture of dorian gray'],
        'related_movies': ['bride of frankenstein', 'the fly', 'ex machina', 'blade runner']
    },
    'time machine': {
        'title': 'The Time Machine',
        'genres': ['science fiction', 'time travel', 'dystopian', 'social commentary'],
        'related_books': ['war of the worlds', 'brave new world', '1984'],
        'related_movies': ['back to the future', '12 monkeys', 'primer', 'looper']
    }
}

# Define theme mapping for cross-media recommendations
CROSS_MEDIA_MAPPING = {
    # Book subjects that map well to movie keywords
    'adventure': ['adventure', 'quest', 'journey', 'exploration'],
    'fantasy': ['fantasy', 'magic', 'magical', 'supernatural'],
    'science fiction': ['science fiction', 'sci-fi', 'futuristic', 'space', 'dystopia'],
    'thriller': ['thriller', 'suspense', 'mystery', 'crime'],
    'romance': ['romance', 'love story', 'romantic'],
    'horror': ['horror', 'supernatural', 'ghost', 'monster'],
    'historical': ['historical', 'period piece', 'history', 'biography'],
    'war': ['war', 'military', 'battle'],
    'philosophical': ['philosophical', 'existential', 'thought-provoking'],
    'dystopian': ['dystopia', 'post-apocalyptic', 'dystopian'],
    'mystery': ['mystery', 'detective', 'investigation', 'crime'],
    'drama': ['drama', 'emotional', 'character study'],
    'action': ['action', 'adventure', 'exciting']
}

# High-value themes that create stronger recommendations
HIGH_VALUE_THEMES = [
    'dystopia', 'cyberpunk', 'time travel', 'artificial intelligence',
    'robots', 'space exploration', 'alternate history', 'multiverse',
    'mythology', 'supernatural', 'psychological thriller', 'mind bending',
    'surrealism', 'existential', 'philosophical', 'political intrigue',
    'heist', 'revenge', 'redemption', 'coming of age', 'anti-hero',
    'detective', 'noir', 'mystery', 'thriller', 'horror', 'gothic'
]

# Expanded list of generic terms to filter out
GENERIC_TERMS = [
    'sequel', 'based on', 'book', 'fiction', 'novel', 'series', 'adaptation',
    'paperback', 'hardcover', 'ebook', 'author', 'writer', 'director',
    'movie', 'film', 'cinema', 'feature', 'award', 'bestseller', 'classic',
    'popular', 'famous', 'renowned', 'celebrated', 'acclaimed', 'published'
]

# ===== HELPER FUNCTIONS =====

def filter_shared(shared):
    """Filter out generic or unhelpful topics"""
    return [s for s in shared if s and not any(ep in s.lower() for ep in GENERIC_TERMS)]

def normalize_term(term):
    """Normalize a term by removing punctuation, extra spaces, and converting to lowercase"""
    return re.sub(r'[^\w\s]', '', term.lower()).strip()

def find_cross_media_matches(source_genres, target_type):
    """Find matching themes across different media types"""
    matching_terms = set()
    normalized_source = [normalize_term(g) for g in source_genres]
    
    # Check direct matches and mapped values
    for genre in normalized_source:
        # Direct match
        matching_terms.add(genre)
        
        # Look for mapped values
        for key, values in CROSS_MEDIA_MAPPING.items():
            if any(genre == normalize_term(term) or genre in normalize_term(term) for term in [key] + values):
                matching_terms.update([key] + values)
    
    return matching_terms

def expand_themes(themes, mapping):
    """Expand themes using the defined mappings"""
    expanded = set(themes)
    for theme in themes:
        theme_lower = theme.lower()
        for base, mapped in mapping.items():
            if base in theme_lower or any(m in theme_lower for m in mapped):
                expanded.update([base] + mapped)
    return expanded

def match_to_curated(title, description=''):
    """Try to match a book to our curated database"""
    title_lower = title.lower()
    
    # Direct title match
    for key, data in CURATED_BOOKS.items():
        if key in title_lower or data['title'].lower() in title_lower:
            return data
    
    # Fuzzy match - check if most of the title words match
    title_words = set(title_lower.split())
    for key, data in CURATED_BOOKS.items():
        key_words = set(key.split())
        data_words = set(data['title'].lower().split())
        
        # Check overlap with key or title
        if len(title_words & key_words) >= min(len(title_words), len(key_words)) / 2:
            return data
        if len(title_words & data_words) >= min(len(title_words), len(data_words)) / 2:
            return data
    
    # Check description if available
    if description:
        desc_lower = description.lower()
        for key, data in CURATED_BOOKS.items():
            if key in desc_lower or data['title'].lower() in desc_lower:
                return data
    
    return None

# ===== API REQUEST FUNCTION =====

@cached('api_request')
def make_request(url, params=None):
    """Make an HTTP request with error handling and caching"""
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Request error for {url}: {str(e)}")
        return None

# ===== DATA FETCHING FUNCTIONS =====

@cached('book_details')
def fetch_book_details_from_open_library(key):
    """Fetch book details from OpenLibrary with enhanced description and genre handling"""
    url = f'https://openlibrary.org{key}.json'
    b = make_request(url)
    
    if not b:
        return None
        
    title = b.get('title', 'Unknown')
    author = 'Unknown'
    
    # Get author (cached)
    if b.get('authors'):
        try:
            ak = b['authors'][0]['author']['key']
            author_data = make_request(f'https://openlibrary.org{ak}.json')
            if author_data:
                author = author_data.get('name', 'Unknown')
        except (KeyError, IndexError, TypeError):
            # Handle missing author data gracefully
            pass
    
    # Get year with error handling
    year = 'Unknown'
    try:
        if b.get('first_publish_date'):
            year_match = re.search(r'\d{4}', b.get('first_publish_date'))
            if year_match:
                year = year_match.group(0)
    except:
        pass
    
    # Get description
    desc = ''
    if 'description' in b:
        try:
            desc = b['description'].get('value') if isinstance(b['description'], dict) else b['description']
        except:
            pass
    
    # Get cover image
    img = ''
    try:
        if b.get('covers'):
            img = f"https://covers.openlibrary.org/b/id/{b['covers'][0]}-L.jpg"
    except:
        pass
    
    # Get genres with improved collection
    genres = []
    
    # Try to get subjects from multiple fields
    for subject_field in ['subjects', 'subject_places', 'subject_times', 'subject_people']:
        if b.get(subject_field):
            genres.extend([s for s in b.get(subject_field, []) if s and len(s) > 2])
    
    # Fetch work data for more subjects if available
    try:
        if not genres and b.get('works') and b['works'][0].get('key'):
            work_key = b['works'][0]['key']
            work_data = make_request(f'https://openlibrary.org{work_key}.json')
            if work_data and work_data.get('subjects'):
                genres.extend(work_data.get('subjects', []))
    except:
        pass
    
    # Check if we have curated data for this book
    curated_data = match_to_curated(title, desc)
    if curated_data:
        # Use curated genres if we have few or none
        if not genres or len(genres) < 3:
            genres = curated_data.get('genres', genres)
        
        # Use curated description if we have none
        if not desc and curated_data.get('title'):
            desc = f"A {', '.join(curated_data.get('genres', [''])[:3])} book."
    
    # Filter genres to remove generic terms
    genres = filter_shared(genres)
    
    return {
        'title': title,
        'creator': author,
        'year': year,
        'description': desc,
        'image_url': img,
        'genres': genres,
        'data_source': 'openlibrary'
    }

@cached('book_details')
def fetch_book_details_from_google(book_id):
    """Fetch book details from Google Books API"""
    try:
        book_data = make_request(f'https://www.googleapis.com/books/v1/volumes/{book_id}')
        
        if not book_data or 'volumeInfo' not in book_data:
            return None
            
        info = book_data['volumeInfo']
        
        # Extract basic information
        title = info.get('title', 'Unknown')
        
        # Get authors
        authors = info.get('authors', ['Unknown'])
        author = authors[0] if authors else 'Unknown'
        
        # Get year
        year = 'Unknown'
        if info.get('publishedDate'):
            year_match = re.search(r'\d{4}', info.get('publishedDate', ''))
            if year_match:
                year = year_match.group(0)
        
        # Get description
        desc = info.get('description', '')
        if desc and len(desc) > 800:
            desc = desc[:797] + '...'
            
        # Get cover image
        img = ''
        if info.get('imageLinks'):
            img = info.get('imageLinks', {}).get('thumbnail', '')
            # Use higher quality image if available
            img = img.replace('&zoom=1', '&zoom=0').replace('http://', 'https://')
        
        # Get categories
        categories = info.get('categories', [])
        if not categories and info.get('mainCategory'):
            categories = [info.get('mainCategory')]
            
        # Extract additional subjects from description
        if desc and (not categories or len(categories) < 3):
            # Check for common genres in description
            genre_keywords = [
                'fantasy', 'science fiction', 'mystery', 'thriller', 'romance',
                'horror', 'historical', 'memoir', 'biography', 'adventure',
                'dystopian', 'young adult', 'children', 'philosophy', 'politics'
            ]
            desc_lower = desc.lower()
            for keyword in genre_keywords:
                if keyword in desc_lower and keyword not in categories:
                    categories.append(keyword)
        
        # Check if we have curated data for this book
        curated_data = match_to_curated(title, desc)
        if curated_data and (not categories or len(categories) < 3):
            categories = curated_data.get('genres', categories)
        
        # Filter categories to remove generic terms
        categories = filter_shared(categories)
        
        return {
            'title': title,
            'creator': author,
            'year': year,
            'description': desc,
            'image_url': img,
            'genres': categories,
            'data_source': 'google'
        }
    except Exception as e:
        print(f"Error fetching book details from Google: {str(e)}")
        return None

@cached('book_details')
def fetch_book_details(key_or_id, source='auto'):
    """Hybrid function to fetch book details from the best available source"""
    if source == 'auto':
        # Determine source based on ID format
        if key_or_id.startswith('/'):
            source = 'openlibrary'
        else:
            source = 'google'
    
    if source == 'openlibrary':
        result = fetch_book_details_from_open_library(key_or_id)
        
        # If missing description or insufficient genres, try Google Books
        if result and (not result.get('description') or len(result.get('genres', [])) < 2):
            google_result = None
            try:
                # Search Google Books by title and author
                search_query = f"{result['title']} {result['creator']}"
                resp = make_request('https://www.googleapis.com/books/v1/volumes', params={
                    'q': search_query,
                    'maxResults': 1
                })
                if resp and 'items' in resp and resp['items']:
                    book_id = resp['items'][0]['id']
                    google_result = fetch_book_details_from_google(book_id)
            except Exception as e:
                print(f"Error searching Google Books: {str(e)}")
            
            # Merge results if we found something in Google Books
            if google_result:
                # Keep OpenLibrary data but add Google genres if needed
                if not result.get('genres') or len(result.get('genres', [])) < 2:
                    result['genres'] = google_result.get('genres', result.get('genres', []))
                
                # Use Google description if OpenLibrary has none
                if (not result.get('description') or result.get('description') == '') and google_result.get('description'):
                    result['description'] = google_result.get('description')
                
                # Use Google image if OpenLibrary has none
                if not result.get('image_url') and google_result.get('image_url'):
                    result['image_url'] = google_result.get('image_url')
                
                # Merge data source information
                result['data_source'] = f"{result.get('data_source', 'openlibrary')}+{google_result.get('data_source', 'google')}"
        
        return result
    
    elif source == 'google':
        return fetch_book_details_from_google(key_or_id)
    
    return None

@cached('movie_details')
def fetch_movie_details(mid):
    """Fetch movie details with caching"""
    # Get movie details
    m = make_request(f'https://api.themoviedb.org/3/movie/{mid}', params={
        'api_key': tmdb_key,
        'language': 'en-US'
    })
    
    if not m:
        return None
        
    # Basic validation
    score_pct = m.get('vote_average', 0) * 10
    if score_pct < 50 or 0:
        return None
        
    title = m.get('title', 'Unknown')
    year = m.get('release_date', '')[:4] if m.get('release_date') else 'Unknown'
    desc = m.get('overview', '')
    img = f"https://image.tmdb.org/t/p/w500{m['poster_path']}" if m.get('poster_path') else ''
    
    # Get credits (cached)
    credits = make_request(f'https://api.themoviedb.org/3/movie/{mid}/credits', params={
        'api_key': tmdb_key
    })
    
    director = 'Unknown'
    if credits:
        director = next((c['name'] for c in credits.get('crew', []) if c['job'] == 'Director'), 'Unknown')
    
    # Get genres
    genres = [g['name'] for g in m.get('genres', [])]
    
    # Get keywords (cached)
    kws = make_request(f'https://api.themoviedb.org/3/movie/{mid}/keywords', params={
        'api_key': tmdb_key
    })
    
    if kws:
        genres += [k['name'] for k in kws.get('keywords', [])]
    
    # Filter to remove generic terms
    genres = filter_shared(genres)
    
    return {
        'title': title,
        'creator': director,
        'year': year,
        'description': desc,
        'image_url': img,
        'genres': genres,
        'score_pct': score_pct
    }

# ===== ROUTES =====

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/experimental')
def experimental():
    """Experimental version of the site"""
    return render_template('experimental.html')

@app.route('/search', methods=['POST'])
def search():
    """Search for books or movies"""
    try:
        data = request.json
        q = quote_plus(data.get('query', ''))
        t = data.get('type')
        results = []
        
        if t == 'book':
            # Search for books in OpenLibrary
            resp = make_request(f'https://openlibrary.org/search.json', params={
                'q': q,
                'language': 'eng',
                'limit': 14
            })
            
            if resp and resp.get('docs'):
                for b in resp.get('docs', []):
                    if not b.get('cover_i'):
                        continue
                    key = b['key']
                    det = fetch_book_details(key, 'openlibrary')
                    if det:
                        results.append({'id': f"book-{key.replace('/', '-')}", **det, 'type': 'book'})
        
        elif t == 'movie':
            # Search for movies in TMDB
            resp = make_request(f'https://api.themoviedb.org/3/search/movie', params={
                'api_key': tmdb_key,
                'query': q,
                'language': 'en-US',
                'include_adult': 'false'
            })
            
            if resp and resp.get('results'):
                for m in resp.get('results', [])[:14]:
                    if not m.get('poster_path'):
                        continue
                    mid = str(m['id'])
                    det = fetch_movie_details(mid)
                    if det:
                        results.append({'id': f"movie-{mid}", **det, 'type': 'movie'})
        
        else:
            data_dir = os.path.join(os.path.dirname(__file__), 'data')
            items = json.load(open(os.path.join(data_dir, 'media_items.json')))
            for i in items:
                if i['type'] == t and data.get('query', '').lower() in i['title'].lower():
                    results.append(i)
        
        return jsonify({'results': results})
    
    except Exception as e:
        print(f"Search error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_recommendations', methods=['POST'])
def get_recommendations():
    """Get recommendations for a specific item"""
    try:
        data = request.json
        sel_id = data.get('item_id')
        pool = []
        
        # Book recommendations
        if sel_id.startswith('book-'):
            key = sel_id[5:].replace('-', '/')
            sel = fetch_book_details(key, 'openlibrary')
            
            if not sel:
                return jsonify({'error': 'Book not found'}), 404
                
            sel.update({'id': sel_id, 'type': 'book'})
            
            # Check if we have curated data for better recommendations
            curated_data = match_to_curated(sel['title'], sel.get('description', ''))
            
            # PART 1: Author recommendations (up to 3)
            author_count = 0
            author = sel['creator']
            if author != 'Unknown':
                try:
                    resp = make_request(f'https://openlibrary.org/search.json', params={
                        'author': author,
                        'limit': 6
                    })
                    
                    if resp and resp.get('docs'):
                        for d in resp.get('docs', []):
                            if author_count >= 3:
                                break
                                
                            book_key = d['key']
                            # Skip the current book
                            if book_key.replace('/', '-') == key.replace('/', '-'):
                                continue
                                
                            det = fetch_book_details(book_key, 'openlibrary')
                            if det:
                                pool.append({
                                    'id': f"book-{book_key.replace('/', '-')}", 
                                    'type': 'book', 
                                    'source': f"By the same author: {author}", 
                                    'match_score': 80,
                                    **det
                                })
                                author_count += 1
                except Exception as e:
                    print(f"Error getting author recommendations: {str(e)}")
            
            # PART 2: Subject-based recommendations (up to 3)
            subject_count = 0
            book_genres = sel.get('genres', [])
            
            # If we have curated data, use those genres
            if curated_data:
                book_genres = curated_data.get('genres', book_genres)
            
            # Try to get subject recommendations
            for subject in book_genres[:5]:
                if subject_count >= 3:
                    break
                    
                try:
                    # Format the subject for OpenLibrary URL
                    subject_url = subject.replace(" ", "_").lower()
                    resp = make_request(f'https://openlibrary.org/subjects/{subject_url}.json', params={
                        'limit': 5
                    })
                    
                    if resp and resp.get('works'):
                        for w in resp.get('works', []):
                            if subject_count >= 3:
                                break
                                
                            work_key = w['key']
                            # Skip books already in the pool or the selected book
                            book_id = f"book-{work_key.replace('/', '-')}"
                            if book_id == sel_id or any(p.get('id') == book_id for p in pool):
                                continue
                            
                            det = fetch_book_details(work_key, 'openlibrary')
                            if det:
                                # Check for meaningful overlap
                                shared_genres = set(det.get('genres', [])) & set(book_genres)
                                if len(shared_genres) >= 2:
                                    pool.append({
                                        'id': book_id, 
                                        'type': 'book', 
                                        'source': f"Shares themes: {', '.join(list(shared_genres)[:3])}", 
                                        'match_score': 70 + (len(shared_genres) * 5),
                                        **det
                                    })
                                    subject_count += 1
                except Exception as e:
                    print(f"Error getting subject recommendations: {str(e)}")
                    continue
            
            # PART 3: Cross-media book->movie recommendations (at least 3)
            movie_count = 0
            cross_media_themes = set()
            
            # Create expanded themes set for better movie matching
            for genre in book_genres:
                genre_lower = genre.lower()
                # Add direct genre
                cross_media_themes.add(genre_lower)
                # Add mapped genres
                for book_genre, movie_genres in CROSS_MEDIA_MAPPING.items():
                    if book_genre in genre_lower:
                        cross_media_themes.update(movie_genres)
            
            # If we have curated data, use its related movies
            if curated_data and curated_data.get('related_movies'):
                for movie_title in curated_data.get('related_movies', [])[:4]:
                    if movie_count >= 3:
                        break
                        
                    try:
                        # Search for the movie
                        movie_resp = make_request(f'https://api.themoviedb.org/3/search/movie', params={
                            'api_key': tmdb_key,
                            'query': movie_title,
                            'language': 'en-US'
                        })
                        
                        if movie_resp and movie_resp.get('results'):
                            m = movie_resp['results'][0]
                            if m.get('poster_path'):
                                mid = str(m['id'])
                                det = fetch_movie_details(mid)
                                if det:
                                    # Get a relevant relationship description
                                    relationship = f"Film with themes from '{sel['title']}'"
                                    
                                    # Check for shared genres for a better description
                                    shared = set(g.lower() for g in det.get('genres', [])) & cross_media_themes
                                    if shared:
                                        relationship = f"Film with similar themes: {', '.join(list(shared)[:3])}"
                                    
                                    pool.append({
                                        'id': f"movie-{mid}", 
                                        'type': 'movie', 
                                        'source': relationship, 
                                        'match_score': 75,
                                        **det
                                    })
                                    movie_count += 1
                    except Exception as e:
                        print(f"Error getting curated movie recommendations: {str(e)}")
                        continue
            
            # If we still need more movie recommendations
            if movie_count < 3:
                # Try each theme to find good movie matches
                for theme in cross_media_themes:
                    if movie_count >= 3:
                        break
                        
                    try:
                        resp = make_request(f'https://api.themoviedb.org/3/search/movie', params={
                            'api_key': tmdb_key,
                            'query': theme,
                            'language': 'en-US',
                            'page': 1
                        })
                        
                        if resp and resp.get('results'):
                            for m in resp.get('results', [])[:5]:
                                if movie_count >= 3:
                                    break
                                    
                                if not m.get('poster_path'):
                                    continue
                                    
                                mid = str(m['id'])
                                movie_id = f"movie-{mid}"
                                
                                # Skip movies already in the pool
                                if any(p.get('id') == movie_id for p in pool):
                                    continue
                                    
                                det = fetch_movie_details(mid)
                                if det:
                                    # Check for meaningful thematic overlap
                                    movie_themes = set(g.lower() for g in det.get('genres', []))
                                    shared = movie_themes & cross_media_themes
                                    
                                    if len(shared) >= 2:
                                        relationship = f"Film with similar themes: {', '.join(list(shared)[:3])}"
                                        
                                        pool.append({
                                            'id': movie_id, 
                                            'type': 'movie', 
                                            'source': relationship, 
                                            'match_score': 65 + (len(shared) * 5),
                                            **det
                                        })
                                        movie_count += 1
                    except Exception as e:
                        print(f"Error getting theme-based movie recommendations: {str(e)}")
                        continue
        
        # Movie recommendations
        else:
            mid = sel_id.split('-')[1]
            sel = fetch_movie_details(mid)
            
            if not sel:
                return jsonify({'error': 'Movie not found'}), 404
                
            sel.update({'id': sel_id, 'type': 'movie'})
            
            # PART 1: Director recommendations (up to 2)
            director_count = 0
            director = sel['creator']
            
            if director != 'Unknown':
                try:
                    # Search for the director
                    resp = make_request(f'https://api.themoviedb.org/3/search/person', params={
                        'api_key': tmdb_key,
                        'query': director,
                        'language': 'en-US'
                    })
                    
                    if resp and resp.get('results'):
                        person_id = resp['results'][0]['id']
                        credits = make_request(f'https://api.themoviedb.org/3/person/{person_id}/movie_credits', params={
                            'api_key': tmdb_key,
                            'language': 'en-US'
                        })
                        
                        if credits:
                            # Get movies directed by this person
                            directed = [m for m in credits.get('crew', []) 
                                      if m.get('job') == 'Director' 
                                      and str(m.get('id')) != mid  # Skip current movie
                                      and m.get('poster_path')]    # Must have poster
                            
                            for m in directed[:2]:
                                curr_mid = str(m['id'])
                                det = fetch_movie_details(curr_mid)
                                if det:
                                    pool.append({
                                        'id': f"movie-{curr_mid}", 
                                        'type': 'movie', 
                                        'source': f"Also directed by {director}", 
                                        'match_score': 85,
                                        **det
                                    })
                                    director_count += 1
                except Exception as e:
                    print(f"Error getting director's movies: {str(e)}")
            
            # PART 2: Similar movies with shared genres (up to 3)
            movie_count = 0
            try:
                resp = make_request(f'https://api.themoviedb.org/3/movie/{mid}/similar', params={
                    'api_key': tmdb_key,
                    'language': 'en-US',
                    'page': 1
                })
                
                if resp and resp.get('results'):
                    for m in resp.get('results', [])[:8]:
                        if movie_count >= 3:
                            break
                            
                        if not m.get('poster_path'):
                            continue
                            
                        curr_mid = str(m['id'])
                        movie_id = f"movie-{curr_mid}"
                        
                        # Skip movies already in the pool or the current movie
                        if movie_id == sel_id or any(p.get('id') == movie_id for p in pool):
                            continue
                            
                        det = fetch_movie_details(curr_mid)
                        if det:
                            # Check for meaningful thematic overlap
                            shared = set(det.get('genres', [])) & set(sel.get('genres', []))
                            
                            if len(shared) >= 2:
                                relationship = f"Shares genres: {', '.join(list(shared)[:3])}"
                                
                                pool.append({
                                    'id': movie_id, 
                                    'type': 'movie', 
                                    'source': relationship, 
                                    'match_score': 75 + (len(shared) * 5),
                                    **det
                                })
                                movie_count += 1
            except Exception as e:
                print(f"Error getting similar movies: {str(e)}")
            
            # PART 3: Cross-media movie->book recommendations (at least 3)
            book_count = 0
            
            # Create expanded themes set for better book matching
            movie_genres = sel.get('genres', [])
            cross_media_themes = set()
            
            for genre in movie_genres:
                genre_lower = genre.lower()
                # Add direct genre
                cross_media_themes.add(genre_lower)
                # Add mapped genres from reverse mapping
                for book_genre, movie_genres in CROSS_MEDIA_MAPPING.items():
                    if genre_lower in [mg.lower() for mg in movie_genres] or genre_lower == book_genre.lower():
                        cross_media_themes.add(book_genre)
            
            # Try each theme to find good book matches
            for theme in list(cross_media_themes)[:5]:
                if book_count >= 3:
                    break
                    
                try:
                    # First try Google Books for better results
                    gb_resp = make_request('https://www.googleapis.com/books/v1/volumes', params={
                        'q': f'subject:"{theme}"',
                        'maxResults': 5,
                        'printType': 'books',
                        'langRestrict': 'en'
                    })
                    
                    if gb_resp and gb_resp.get('items'):
                        for book in gb_resp.get('items', [])[:3]:
                            if book_count >= 3:
                                break
                                
                            book_id = book.get('id')
                            if not book_id:
                                continue
                                
                            # Skip if no image
                            if not book.get('volumeInfo', {}).get('imageLinks', {}).get('thumbnail'):
                                continue
                                
                            gb_book_id = f"gb-{book_id}"
                            
                            # Skip books already in the pool
                            if any(p.get('id') == gb_book_id for p in pool):
                                continue
                                
                            det = fetch_book_details(book_id, 'google')
                            if det:
                                # Check for meaningful thematic overlap
                                book_themes = set(g.lower() for g in det.get('genres', []))
                                shared = book_themes & cross_media_themes
                                
                                if len(shared) >= 1:
                                    relationship = f"Book with similar themes: {', '.join(list(shared)[:3])}"
                                    
                                    pool.append({
                                        'id': gb_book_id, 
                                        'type': 'book', 
                                        'source': relationship, 
                                        'match_score': 65 + (len(shared) * 5),
                                        **det
                                    })
                                    book_count += 1
                    
                    # If we still need more books, try OpenLibrary
                    if book_count < 3:
                        # Format the subject for OpenLibrary URL
                        subject_url = theme.replace(" ", "_").lower()
                        resp = make_request(f'https://openlibrary.org/subjects/{subject_url}.json', params={
                            'limit': 5
                        })
                        
                        if resp and resp.get('works'):
                            for w in resp.get('works', [])[:3]:
                                if book_count >= 3:
                                    break
                                    
                                work_key = w['key']
                                book_id = f"book-{work_key.replace('/', '-')}"
                                
                                # Skip books already in the pool
                                if any(p.get('id') == book_id for p in pool):
                                    continue
                                    
                                det = fetch_book_details(work_key, 'openlibrary')
                                if det:
                                    # Check for meaningful thematic overlap
                                    book_themes = set(g.lower() for g in det.get('genres', []))
                                    shared = book_themes & cross_media_themes
                                    
                                    if len(shared) >= 1:
                                        relationship = f"Book with similar themes: {', '.join(list(shared)[:3])}"
                                        
                                        pool.append({
                                            'id': book_id, 
                                            'type': 'book', 
                                            'source': relationship, 
                                            'match_score': 65 + (len(shared) * 5),
                                            **det
                                        })
                                        book_count += 1
                except Exception as e:
                    print(f"Error getting cross-media book recommendations: {str(e)}")
                    continue
        
        # FINAL STEP: Score, deduplicate, and diversify recommendations
        if pool:
            # Remove duplicates
            seen = set()
            unique_pool = []
            
            for item in pool:
                item_id = item['id']
                
                # Skip duplicates and the selected item
                if item_id in seen or item_id == sel_id:
                    continue
                    
                seen.add(item_id)
                unique_pool.append(item)
            
            # Sort by match score (highest first)
            unique_pool.sort(key=lambda x: x.get('match_score', 0), reverse=True)
            
            # Ensure diversity of media types
            # Make sure we have both books and movies when possible
            book_recs = [i for i in unique_pool if i['type'] == 'book']
            movie_recs = [i for i in unique_pool if i['type'] == 'movie']
            
            # Always include at least one of each type if available
            diverse_pool = []
            
            # If the selected item is a book, prioritize movies (at least 3 if available)
            if sel['type'] == 'book':
                diverse_pool.extend(movie_recs[:3])
                diverse_pool.extend(book_recs[:3])
            # If the selected item is a movie, prioritize books (at least 3 if available)
            else:
                diverse_pool.extend(book_recs[:3])
                diverse_pool.extend(movie_recs[:3])
            
            # Deduplicate again (just in case)
            seen = set()
            final_pool = []
            
            for item in diverse_pool:
                if item['id'] not in seen:
                    seen.add(item['id'])
                    final_pool.append(item)
            
            # If we have fewer than 6 recommendations, add more from the original pool
            if len(final_pool) < 6:
                for item in unique_pool:
                    if len(final_pool) >= 6:
                        break
                        
                    if item['id'] not in seen:
                        seen.add(item['id'])
                        final_pool.append(item)
            
            # Format recommendations for response (take top 6)
            recs = []
            for it in final_pool[:6]:
                # Remove match_score and source from the item details
                item_copy = {k: v for k, v in it.items() if k != 'match_score' and k != 'source'}
                # Add relationship type from source
                recs.append({'item': item_copy, 'relationship_type': it.get('source', 'Similar item')})
            
            return jsonify({'selected_item': sel, 'recommendations': recs})
        else:
            # No recommendations found
            return jsonify({'selected_item': sel, 'recommendations': []})
    
    except Exception as e:
        print(f"Recommendation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/experimental/search', methods=['POST'])
def experimental_search():
    """Placeholder for experimental search that might include games/music in the future"""
    return search()

@app.route('/experimental/get_recommendations', methods=['POST'])
def experimental_get_recommendations():
    """Placeholder for experimental recommendations that might include games/music in the future"""
    return get_recommendations()

# Route to handle placeholder image requests
@app.route('/static/images/placeholder.png', methods=['GET'])
def placeholder_image():
    """Serve a placeholder image to prevent 404 errors"""
    try:
        # Try to serve a real placeholder image if it exists
        return send_file('static/images/placeholder.png')
    except:
        # If no image exists, create a transparent pixel as fallback
        transparent_pixel = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        return Response(transparent_pixel, mimetype='image/png')

# Cache management endpoint
@app.route('/cache/stats', methods=['GET'])
def cache_stats():
    """Get cache statistics"""
    with cache_lock:
        stats = {
            'total_entries': len(cache),
            'by_type': {},
            'size_estimate_kb': sum(len(str(v[1])) for v in cache.values()) / 1024
        }
        
        # Count by prefix
        for key in cache:
            prefix = key.split(':')[0]
            if prefix not in stats['by_type']:
                stats['by_type'][prefix] = 0
            stats['by_type'][prefix] += 1
    
    return jsonify(stats)

@app.route('/cache/clear', methods=['POST'])
def clear_cache():
    """Clear the cache (admin only)"""
    with cache_lock:
        cache.clear()
    return jsonify({'status': 'Cache cleared'})

if __name__ == '__main__':
    app.run(debug=True)