from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet
import requests
import json
import os
import functools

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change_this_in_production_please')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///scrounge.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# ---------------------------------------------------------------------------
# Encryption helpers
# ---------------------------------------------------------------------------
def _get_or_create_fernet_key():
    key_file = '.fernet_key'
    if os.path.exists(key_file):
        with open(key_file, 'rb') as f:
            return f.read().strip()
    key = Fernet.generate_key()
    with open(key_file, 'wb') as f:
        f.write(key)
    return key

_fernet = Fernet(_get_or_create_fernet_key())

def encrypt(value):
    if value is None:
        return None
    return _fernet.encrypt(str(value).encode()).decode()

def decrypt(value):
    if value is None:
        return None
    try:
        return _fernet.decrypt(value.encode()).decode()
    except Exception:
        return value  # fallback for any unencrypted legacy values


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    inventories = db.relationship('Inventory', backref='owner', lazy=True, cascade='all, delete-orphan')
    recipes = db.relationship('Recipe', backref='owner', lazy=True, cascade='all, delete-orphan')
    preferences = db.relationship('Preference', backref='owner', lazy=True, cascade='all, delete-orphan')

class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)      # encrypted
    quantity = db.Column(db.Text, nullable=False)  # encrypted
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)         # encrypted
    ingredients = db.Column(db.Text, nullable=False)  # encrypted JSON
    instructions = db.Column(db.Text, nullable=False) # encrypted
    cuisine = db.Column(db.Text)                      # encrypted
    source = db.Column(db.Text)                       # encrypted
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Preference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cuisine = db.Column(db.Text, nullable=False)  # encrypted
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


with app.app_context():
    db.create_all()


# ---------------------------------------------------------------------------
# Auth decorator
# ---------------------------------------------------------------------------
def login_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Data functions (all scoped to user_id)
# ---------------------------------------------------------------------------
def add_inventory(item_name, quantity, user_id):
    for item in Inventory.query.filter_by(user_id=user_id).all():
        if decrypt(item.name) == item_name:
            return  # already exists for this user
    db.session.add(Inventory(name=encrypt(item_name), quantity=encrypt(quantity), user_id=user_id))
    db.session.commit()

def _find_inventory_item(item_name, user_id):
    for item in Inventory.query.filter_by(user_id=user_id).all():
        if decrypt(item.name) == item_name:
            return item
    return None

def remove_inventory(item_name, user_id):
    item = _find_inventory_item(item_name, user_id)
    if item:
        db.session.delete(item)
        db.session.commit()

def update_inventory(old_name, new_name, quantity, user_id):
    item = _find_inventory_item(old_name, user_id)
    if item:
        item.name = encrypt(new_name)
        item.quantity = encrypt(quantity)
        db.session.commit()

def list_inventory(user_id):
    return [{'name': decrypt(i.name), 'quantity': decrypt(i.quantity)}
            for i in Inventory.query.filter_by(user_id=user_id).all()]

def save_recipe(recipe, user_id):
    db.session.add(Recipe(
        name=encrypt(recipe['name']),
        ingredients=encrypt(json.dumps(recipe['ingredients'])),
        instructions=encrypt(recipe['instructions']),
        cuisine=encrypt(recipe.get('cuisine', '')),
        source=encrypt(recipe.get('source', '')),
        user_id=user_id
    ))
    db.session.commit()

def remove_recipe(recipe_id, user_id):
    recipe = Recipe.query.filter_by(id=recipe_id, user_id=user_id).first()
    if recipe:
        db.session.delete(recipe)
        db.session.commit()

def get_recipe_details(recipe_id, user_id):
    r = Recipe.query.filter_by(id=recipe_id, user_id=user_id).first()
    if r:
        return {
            'id': r.id,
            'name': decrypt(r.name),
            'ingredients': json.loads(decrypt(r.ingredients)),
            'instructions': decrypt(r.instructions),
            'cuisine': decrypt(r.cuisine),
            'source': decrypt(r.source)
        }
    return None

def can_make_recipe(ingredients, user_id):
    inv_names = [d['name'].lower() for d in list_inventory(user_id)]
    return all(ing['name'].lower() in inv_names for ing in ingredients)

def ready_to_make(user_id):
    ready = []
    for r in Recipe.query.filter_by(user_id=user_id).all():
        ingredients = json.loads(decrypt(r.ingredients))
        if can_make_recipe(ingredients, user_id):
            ready.append((r.id, decrypt(r.name)))
    return ready

def set_preference(cuisine, user_id):
    for p in Preference.query.filter_by(user_id=user_id).all():
        if decrypt(p.cuisine) == cuisine:
            return
    db.session.add(Preference(cuisine=encrypt(cuisine), user_id=user_id))
    db.session.commit()

def get_preferences(user_id):
    return [decrypt(p.cuisine) for p in Preference.query.filter_by(user_id=user_id).all()]

def remove_preference(cuisine, user_id):
    for p in Preference.query.filter_by(user_id=user_id).all():
        if decrypt(p.cuisine) == cuisine:
            db.session.delete(p)
            db.session.commit()
            return

def clear_preferences(user_id):
    Preference.query.filter_by(user_id=user_id).delete()
    db.session.commit()

def search_recipes(query, user_id):
    url = f"https://www.themealdb.com/api/json/v1/1/filter.php?i={query}"
    resp = requests.get(url)
    if resp.status_code == 200:
        data = resp.json()
        if data['meals']:
            full_meals = []
            for meal in data['meals']:
                full = get_recipe_from_api(meal['idMeal'])
                if full:
                    full_meals.append(full)
            prefs = get_preferences(user_id)
            if prefs:
                full_meals = [m for m in full_meals if m['cuisine'] in prefs]
            return full_meals
    return []

def get_recipe_from_api(meal_id):
    url = f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={meal_id}"
    resp = requests.get(url)
    if resp.status_code == 200:
        data = resp.json()
        if data['meals']:
            meal = data['meals'][0]
            ingredients = []
            for i in range(1, 21):
                ing = meal.get(f"strIngredient{i}")
                if ing:
                    measure = meal.get(f"strMeasure{i}", "")
                    ingredients.append({"name": ing, "measure": measure})
            return {
                'name': meal['strMeal'],
                'ingredients': ingredients,
                'instructions': meal['strInstructions'],
                'cuisine': meal['strArea'],
                'source': meal.get('strSource', '')
            }
    return None


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------
@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        confirm = request.form['confirm_password']
        if not username or not password:
            flash('Username and password are required.')
            return render_template('register.html')
        if password != confirm:
            flash('Passwords do not match.')
            return render_template('register.html')
        if User.query.filter_by(username=username).first():
            flash('Username already taken.')
            return render_template('register.html')
        user = User(username=username, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        flash('Account created! Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('home'))
        flash('Invalid username or password.')
    return render_template('login.html')

@app.route("/logout")
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('login'))


# ---------------------------------------------------------------------------
# Protected app routes
# ---------------------------------------------------------------------------
@app.route("/")
@login_required
def home():
    menu_options = [
        {"url": "/inventory", "text": "1. Manage Inventory"},
        {"url": "/ready_meals", "text": "2. Find Ready-to-Make Meals"},
        {"url": "/search_recipes", "text": "3. Search New Recipes"},
        {"url": "/recipe_book", "text": "4. View Recipe Book"},
        {"url": "/preferences", "text": "5. Set Preferences"},
    ]
    return render_template('index.html', menu_options=menu_options)

@app.route("/inventory")
@login_required
def inventory():
    return render_template('inventory.html', inventory=list_inventory(session['user_id']))

@app.route("/add_inventory", methods=['POST'])
@login_required
def add_inventory_route():
    add_inventory(request.form['item_name'], request.form['quantity'], session['user_id'])
    return redirect(url_for('inventory'))

@app.route("/edit_inventory/<item_name>")
@login_required
def edit_inventory_route(item_name):
    item = _find_inventory_item(item_name, session['user_id'])
    if item:
        return render_template('edit_inventory.html',
                               item={'name': decrypt(item.name), 'quantity': decrypt(item.quantity)})
    return redirect(url_for('inventory'))

@app.route("/update_inventory", methods=['POST'])
@login_required
def update_inventory_route():
    update_inventory(request.form['old_name'], request.form['item_name'],
                     request.form['quantity'], session['user_id'])
    flash('Item updated successfully!')
    return redirect(url_for('inventory'))

@app.route("/remove_inventory/<item_name>")
@login_required
def remove_inventory_route(item_name):
    remove_inventory(item_name, session['user_id'])
    return redirect(url_for('inventory'))

@app.route("/ready_meals")
@login_required
def ready_meals():
    user_id = session['user_id']
    full_meals = []
    for meal_id, _ in ready_to_make(user_id):
        details = get_recipe_details(meal_id, user_id)
        if details:
            full_meals.append(details)
    return render_template('ready_meals.html', meals=full_meals)

@app.route("/search_recipes", methods=['GET', 'POST'])
@login_required
def search_recipes_route():
    if request.method == 'POST':
        meals = search_recipes(request.form['query'], session['user_id'])
        return render_template('search_recipes.html', is_post=True, meals=meals)
    return render_template('search_recipes.html', is_post=False)

@app.route("/save_recipe", methods=['POST'])
@login_required
def save_recipe_route():
    try:
        recipe = {
            'name': request.form['name'],
            'ingredients': json.loads(request.form['ingredients']),
            'instructions': request.form['instructions'],
            'cuisine': request.form['cuisine'],
            'source': request.form['source']
        }
        save_recipe(recipe, session['user_id'])
        referrer = request.referrer or ''
        if 'search_recipes' in referrer:
            flash('Recipe saved successfully!')
            return redirect(url_for('search_recipes_route'))
        elif 'ready_meals' in referrer:
            flash('Recipe saved successfully!')
            return redirect(url_for('ready_meals'))
        return redirect(url_for('recipe_book'))
    except Exception as e:
        print(f"Error saving recipe: {e}")
        return f"Error saving recipe: {e}", 500

@app.route("/remove_recipe/<int:recipe_id>")
@login_required
def remove_recipe_route(recipe_id):
    remove_recipe(recipe_id, session['user_id'])
    flash('Recipe removed successfully!')
    return redirect(url_for('recipe_book'))

@app.route("/recipe_book")
@login_required
def recipe_book():
    user_id = session['user_id']
    recipe_list = []
    for r in Recipe.query.filter_by(user_id=user_id).all():
        recipe_list.append({
            'id': r.id,
            'name': decrypt(r.name),
            'ingredients': json.loads(decrypt(r.ingredients)),
            'instructions': decrypt(r.instructions),
            'cuisine': decrypt(r.cuisine),
            'source': decrypt(r.source)
        })
    return render_template('recipe_book.html', recipes=recipe_list)

@app.route("/preferences", methods=['GET', 'POST'])
@login_required
def preferences():
    user_id = session['user_id']
    if request.method == 'POST':
        action = request.form['action']
        if action == 'add':
            set_preference(request.form['cuisine'], user_id)
        elif action == 'remove':
            remove_preference(request.form['cuisine'], user_id)
        elif action == 'clear':
            clear_preferences(user_id)
        return redirect(url_for('preferences'))
    return render_template('preferences.html', prefs=get_preferences(user_id))


if __name__ == "__main__":
    app.run(debug=True)
