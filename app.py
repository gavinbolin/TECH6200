from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import json
import os
import functools

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import models and API blueprint
from models import db, User, Recipe, decrypt, add_inventory, _find_inventory_item, remove_inventory, update_inventory, list_inventory, save_recipe, remove_recipe, get_recipe_details, ready_to_make, set_preference, get_preferences, remove_preference, clear_preferences, search_recipes
from api import api_bp

app = Flask(__name__)
secret_key = os.environ.get('SECRET_KEY')
if not secret_key:
    raise ValueError("SECRET_KEY environment variable is required")
app.secret_key = secret_key
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI', 'sqlite:///scrounge.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Session security configuration
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour session timeout

# Configure logging
import logging
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

# Add file handler for production logging
if not app.debug:
    import sys
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)

db.init_app(app)

with app.app_context():
    db.create_all()

# Register API blueprint
app.register_blueprint(api_bp)


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


# Data functions are imported from models.py


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------
@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        # Input validation
        if not username or not password:
            flash('Username and password are required.')
            return render_template('register.html')
        if len(username) < 3 or len(username) > 50:
            flash('Username must be between 3 and 50 characters.')
            return render_template('register.html')
        if len(password) < 6:
            flash('Password must be at least 6 characters long.')
            return render_template('register.html')
        if password != confirm:
            flash('Passwords do not match.')
            return render_template('register.html')
        if User.query.filter_by(username=username).first():
            flash('Username already taken.')
            return render_template('register.html')

        try:
            user = User(username=username, password_hash=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            flash('Account created! Please log in.')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error creating user: {e}")
            flash('An error occurred during registration. Please try again.')
            return render_template('register.html')

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
    item_name = request.form.get('item_name', '').strip()
    quantity = request.form.get('quantity', '').strip()

    if not item_name or not quantity:
        flash('Item name and quantity are required.')
        return redirect(url_for('inventory'))

    if len(item_name) > 100 or len(quantity) > 100:
        flash('Item name and quantity must be less than 100 characters.')
        return redirect(url_for('inventory'))

    try:
        add_inventory(item_name, quantity, session['user_id'])
        flash('Item added successfully!')
    except Exception as e:
        app.logger.error(f"Error adding inventory: {e}")
        flash('An error occurred while adding the item.')

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
    old_name = request.form.get('old_name', '').strip()
    item_name = request.form.get('item_name', '').strip()
    quantity = request.form.get('quantity', '').strip()

    if not item_name or not quantity:
        flash('Item name and quantity are required.')
        return redirect(url_for('inventory'))

    if len(item_name) > 100 or len(quantity) > 100:
        flash('Item name and quantity must be less than 100 characters.')
        return redirect(url_for('inventory'))

    try:
        update_inventory(old_name, item_name, quantity, session['user_id'])
        flash('Item updated successfully!')
    except Exception as e:
        app.logger.error(f"Error updating inventory: {e}")
        flash('An error occurred while updating the item.')

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
    except json.JSONDecodeError:
        flash('Invalid recipe data format.')
        return redirect(request.referrer or url_for('recipe_book'))
    except Exception as e:
        app.logger.error(f"Error saving recipe: {e}")
        flash('An error occurred while saving the recipe.')
        return redirect(request.referrer or url_for('recipe_book'))

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
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(debug=debug)
