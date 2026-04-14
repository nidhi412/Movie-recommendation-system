import os
import json
import logging
import requests
from bson import ObjectId
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import pymongo

app = Flask(__name__)
app.secret_key = 'super-secret-key'
bcrypt = Bcrypt(app)

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Files
USERS_FILE = "users.json"
OMDB_API_KEY = "890d679a"

# Ensure users.json exists
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump([], f)

# MongoDB connection
try:
    connection_string = "mongodb+srv://nidhi:Abcd123$@cluster0.20lqo.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    client = pymongo.MongoClient(connection_string, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    logger.info("Connected successfully to MongoDB")
    db = client.get_database("MovieDB")
    movies_collection = db.get_collection("Movies")
except Exception as e:
    logger.error(f"MongoDB connection failed: {e}")
    client = db = movies_collection = None

def fetch_poster(title, year=None):
    base_url = "http://www.omdbapi.com/"
    params = {
        "apikey": OMDB_API_KEY,
        "t": title,
    }
    if year:
        params["y"] = str(year)
    try:
        response = requests.get(base_url, params=params)
        data = response.json()
        return data.get("Poster") if data.get("Response") == "True" else None
    except Exception as e:
        print(f"Error fetching poster: {e}")
        return None

class User(UserMixin):
    def __init__(self, id_, username, email):
        self.id = id_
        self.username = username
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    with open(USERS_FILE, "r") as f:
        users = json.load(f)
    if user_id.isdigit():
        user_id = int(user_id)
        if 0 <= user_id < len(users):
            user = users[user_id]
            return User(id_=user_id, username=user["username"], email=user["email"])
    return None

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        with open(USERS_FILE, "r+") as f:
            users = json.load(f)
            if any(u["email"] == email for u in users):
                flash("Email already exists. Please login.", "warning")
                return redirect(url_for("login"))
            hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
            users.append({"username": username, "email": email, "password": hashed_pw, "favorites": []})
            f.seek(0)
            json.dump(users, f, indent=2)
            f.truncate()
        flash("Account created! Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        with open(USERS_FILE, "r") as f:
            users = json.load(f)
        for idx, user in enumerate(users):
            if user["email"] == email and bcrypt.check_password_hash(user["password"], password):
                login_user(User(id_=idx, username=user["username"], email=user["email"]))
                flash("Login successful!", "success")
                return redirect(url_for("index"))
        flash("Invalid credentials.", "danger")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

@app.route("/")
@login_required
def index():
    return render_template("index.html", user=current_user, recommendations=[])

@app.route("/results", methods=["POST"])
@login_required
def results():
    recommendations = []
    error_message = None
    try:
        movie_name = request.form.get("movie_name", "")
        actor_name = request.form.get("actor_name", "")
        director_name = request.form.get("director_name", "")
        release_year = request.form.get("release_year", "")
        genres = request.form.get("genres", "")
        imdb_score = request.form.get("imdb_score", "")

        if movies_collection is None:
            error_message = "Database connection is not available. Please check server logs."
            return render_template("results.html", recommendations=[], error_message=error_message)

        query = {}
        if movie_name:
            query["movie_title"] = {"$regex": movie_name, "$options": "i"}
        if actor_name:
            query["actors.name"] = {"$regex": actor_name, "$options": "i"}
        if director_name:
            query["director.name"] = {"$regex": director_name, "$options": "i"}
        if release_year:
            try:
                query["title_year"] = int(release_year)
            except ValueError:
                pass
        if genres:
            query["genres"] = {"$regex": genres, "$options": "i"}
        if imdb_score:
            try:
                score = float(imdb_score)
                query["imdb_score"] = {"$gte": score}
            except ValueError:
                pass

        recommendations = list(movies_collection.find(query))

        for movie in recommendations:
            movie["poster_url"] = fetch_poster(movie.get("movie_title"), movie.get("title_year"))

    except Exception as e:
        logger.error(f"Error in /results: {e}")
        error_message = f"An error occurred: {str(e)}"

    return render_template("results.html", recommendations=recommendations, error_message=error_message)

@app.route("/add_favorite", methods=["POST"])
@login_required
def add_favorite():
    movie_id = request.form.get("movie_id")
    if movie_id:
        movie = movies_collection.find_one({"_id": ObjectId(movie_id)})
        if movie:
            # ✅ Convert ObjectId to string
            movie["_id"] = str(movie["_id"])

            # ✅ (Optional) Select only needed fields for storing favorites
            minimal_movie = {
                "_id": movie["_id"],
                "movie_title": movie.get("movie_title"),
                "title_year": movie.get("title_year"),
                "genres": movie.get("genres"),
                "imdb_score": movie.get("imdb_score"),
                "movie_imdb_link": movie.get("movie_imdb_link"),
            }

            with open(USERS_FILE, "r+") as f:
                users = json.load(f)
                user_data = users[int(current_user.id)]
                favorites = user_data.get("favorites", [])

                # Prevent duplicates
                if not any(fav["_id"] == minimal_movie["_id"] for fav in favorites):
                    favorites.append(minimal_movie)
                    user_data["favorites"] = favorites
                    f.seek(0)
                    json.dump(users, f, indent=2)
                    f.truncate()
            flash("Added to favorites!", "success")
    return redirect(url_for("favorites"))

@app.route("/favorites")
@login_required
def favorites():
    with open(USERS_FILE, "r") as f:
        users = json.load(f)
        favorites = users[int(current_user.id)].get("favorites", [])
    return render_template("favorites.html", favorites=favorites)
@app.route("/remove_favorite", methods=["POST"])
@login_required
def remove_favorite():
    movie_id = request.form.get("movie_id")
    if movie_id:
        with open(USERS_FILE, "r+") as f:
            users = json.load(f)
            user_data = users[int(current_user.id)]
            # Remove the favorite that matches the movie ID
            user_data["favorites"] = [m for m in user_data.get("favorites", []) if m.get("_id") != movie_id]
            f.seek(0)
            json.dump(users, f, indent=2)
            f.truncate()
    flash("Removed from favorites!", "info")
    return redirect(url_for("favorites"))
@app.route("/recommendations")
@login_required
def recommendations():
    from collections import Counter

    with open(USERS_FILE, "r") as f:
        users = json.load(f)
        user_data = users[int(current_user.id)]
        favorites = user_data.get("favorites", [])
        if not favorites:
            return render_template("recommendations.html", recommendations=[])

        # Support both list and string formats
        favorite_genres = []
        for movie in favorites:
            genres = movie.get("genres")
            if isinstance(genres, list):
                favorite_genres.extend(genres)
            elif isinstance(genres, str):
                favorite_genres.extend([g.strip() for g in genres.split("|")])

        if not favorite_genres:
            return render_template("recommendations.html", recommendations=[])

        genre_counts = Counter(favorite_genres)
        top_genres = [genre for genre, _ in genre_counts.most_common(3)]
        genre_regex = "|".join(top_genres)

        query = {"genres": {"$regex": genre_regex, "$options": "i"}}
        recommendations = list(movies_collection.find(query).limit(10))

        for movie in recommendations:
            movie["poster_url"] = fetch_poster(movie.get("movie_title"), movie.get("title_year"))

    return render_template("recommendations.html", recommendations=recommendations)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
