from flask_sqlalchemy import SQLAlchemy
from cryptography.fernet import Fernet
import os
import json

db = SQLAlchemy()

# ---------------------------------------------------------------------------
# Encryption helpers
# ---------------------------------------------------------------------------
def _load_fernet_key():
    key = os.environ.get('FERNET_KEY')
    if not key:
        raise ValueError("FERNET_KEY environment variable is required")
    return key.encode()

_fernet = Fernet(_load_fernet_key())

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
    import requests
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
    import requests
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