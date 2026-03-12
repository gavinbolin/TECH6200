from flask import Flask, render_template, request, redirect, url_for
import requests
import json
import os

app = Flask(__name__)

# Global data structures (copied from main.py)
inventory_list = []
recipes_list = []
preferences_list = []

def load_data():
    global inventory_list, recipes_list, preferences_list
    if os.path.exists('inventory.json'):
        with open('inventory.json', 'r') as f:
            inventory_list = json.load(f)
    else:
        inventory_list = []

    if os.path.exists('recipes.json'):
        with open('recipes.json', 'r') as f:
            recipes_list = json.load(f)
    else:
        recipes_list = []

    if os.path.exists('preferences.json'):
        with open('preferences.json', 'r') as f:
            preferences_list = json.load(f)
    else:
        preferences_list = []

def save_data():
    with open('inventory.json', 'w') as f:
        json.dump(inventory_list, f, indent=4)
    with open('recipes.json', 'w') as f:
        json.dump(recipes_list, f, indent=4)
    with open('preferences.json', 'w') as f:
        json.dump(preferences_list, f, indent=4)

load_data()

# Functions from main.py
def add_inventory(item_name, quantity):
    item_dict = {'name': item_name, 'quantity': quantity}
    if not any(d['name'] == item_name for d in inventory_list):
        inventory_list.append(item_dict)
        save_data()

def remove_inventory(item_name):
    global inventory_list
    inventory_list = [d for d in inventory_list if d['name'] != item_name]
    save_data()

def list_inventory():
    return inventory_list

def save_recipe(recipe):
    global recipes_list
    recipe_id = len(recipes_list) + 1
    recipe_dict = {
        'id': recipe_id,
        'name': recipe['name'],
        'ingredients': recipe['ingredients'],
        'instructions': recipe['instructions'],
        'cuisine': recipe['cuisine'],
        'source': recipe['source']
    }
    recipes_list.append(recipe_dict)
    save_data()

def list_saved_recipes():
    return [(r['id'], r['name']) for r in recipes_list]

def get_recipe_details(recipe_id):
    for r in recipes_list:
        if r['id'] == recipe_id:
            return r
    return None

def can_make_recipe(ingredients):
    inv_names = [d['name'].lower() for d in list_inventory()]
    return all(ing['name'].lower() in inv_names for ing in ingredients)

def ready_to_make():
    recipes = []
    for r in recipes_list:
        if can_make_recipe(r['ingredients']):
            recipes.append((r['id'], r['name']))
    return recipes

def set_preference(cuisine):
    if cuisine not in preferences_list:
        preferences_list.append(cuisine)
        save_data()

def get_preferences():
    return preferences_list

def remove_preference(cuisine):
    if cuisine in preferences_list:
        preferences_list.remove(cuisine)
        save_data()

def clear_preferences():
    preferences_list.clear()
    save_data()

def search_recipes(query):
    url = f"https://www.themealdb.com/api/json/v1/1/filter.php?i={query}"
    resp = requests.get(url)
    if resp.status_code == 200:
        data = resp.json()
        if data['meals']:
            meals = data['meals']
            full_meals = []
            for meal in meals:
                full = get_recipe_from_api(meal['idMeal'])
                if full:
                    full_meals.append(full)
            prefs = get_preferences()
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

@app.route("/")
def home():
    return render_template('index.html')

@app.route("/inventory")
def inventory():
    inv = list_inventory()
    return render_template('inventory.html', inventory=inv)

@app.route("/add_inventory", methods=['POST'])
def add_inventory_route():
    item_name = request.form['item_name']
    quantity = request.form['quantity']
    add_inventory(item_name, quantity)
    return redirect(url_for('inventory'))

@app.route("/remove_inventory/<item_name>")
def remove_inventory_route(item_name):
    remove_inventory(item_name)
    return redirect(url_for('inventory'))

@app.route("/ready_meals")
def ready_meals():
    meals = ready_to_make()
    return render_template('ready_meals.html', meals=meals)

@app.route("/search_recipes", methods=['GET', 'POST'])
def search_recipes_route():
    if request.method == 'POST':
        query = request.form['query']
        meals = search_recipes(query)
        return render_template('search_recipes.html', is_post=True, meals=meals)
    return render_template('search_recipes.html', is_post=False)

@app.route("/recipe_book")
def recipe_book():
    return render_template('recipe_book.html', recipes=recipes_list)

@app.route("/preferences", methods=['GET', 'POST'])
def preferences():
    if request.method == 'POST':
        action = request.form['action']
        if action == 'add':
            cuisine = request.form['cuisine']
            set_preference(cuisine)
        elif action == 'remove':
            cuisine = request.form['cuisine']
            remove_preference(cuisine)
        elif action == 'clear':
            clear_preferences()
        return redirect(url_for('preferences'))
    prefs = get_preferences()
    return render_template('preferences.html', prefs=prefs)

if __name__ == "__main__":
    app.run(debug=True)
