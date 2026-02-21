import requests
import json
import os

# Global data structures
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
    # Search by ingredient
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
            # Filter by preferences if any
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

# Main loop
while True:
    print("\nScrounge Menu:")
    print("1. Manage Inventory")
    print("2. Find Ready-to-Make Meals")
    print("3. Search New Recipes")
    print("4. View Recipe Book")
    print("5. Set Preferences")
    print("6. Exit")
    choice = input("Choose: ")

    if choice == '1':
        sub = input("1. Add, 2. Remove, 3. List: ")
        if sub == '1':
            item = input("Item name: ")
            quantity = input("Quantity: ")
            add_inventory(item, quantity)
        elif sub == '2':
            print("Current inventory:")
            for d in list_inventory():
                print(f"- {d['name']} ({d['quantity']})")
            item = input("Item name to remove: ")
            if any(d['name'] == item for d in list_inventory()):
                remove_inventory(item)
                print(f"Removed {item} from inventory.")
            else:
                print(f"Item '{item}' not found in inventory.")
        elif sub == '3':
            for d in list_inventory():
                print(f"{d['name']} ({d['quantity']})")

    elif choice == '2':
        meals = ready_to_make()
        if meals:
            for mid, name in meals:
                print(f"{mid}: {name}")
        else:
            print("No recipes ready to make with current inventory.")

    elif choice == '3':
        query = input("Ingredient or name: ")
        meals = search_recipes(query)
        for i, meal in enumerate(meals):
            print(f"{i+1}: {meal['name']}")
        sel = input("Select number to view/save (0 none): ")
        if sel != '0':
            try:
                idx = int(sel) - 1
                recipe = meals[idx]
                print(f"Name: {recipe['name']}")
                print("Ingredients:")
                for ing in recipe['ingredients']:
                    print(f"- {ing['name']} {ing['measure']}")
                print("Instructions:", recipe['instructions'])
                save = input("Save? (y/n): ")
                if save.lower() == 'y':
                    save_recipe(recipe)
            except:
                pass

    elif choice == '4':
        recipes = list_saved_recipes()
        for rid, name in recipes:
            print(f"{rid}: {name}")
        sel = input("Select ID to view (0 none): ")
        if sel != '0':
            try:
                details = get_recipe_details(int(sel))
                if details:
                    print(f"Name: {details['name']}")
                    print("Ingredients:")
                    for ing in details['ingredients']:
                        print(f"- {ing['name']} {ing['measure']}")
                    print("Instructions:", details['instructions'])
            except:
                pass

    elif choice == '5':
        while True:
            prefs = get_preferences()
            print("Current preferences:")
            if prefs:
                for p in prefs:
                    print(f"- {p}")
            else:
                print("None")
            print("\n1. Add preference")
            print("2. Remove preference")
            print("3. Clear all preferences")
            print("4. Back to main menu")
            sub = input("Choose: ")
            if sub == '1':
                cuisine = input("Preferred cuisine: ")
                set_preference(cuisine)
                print(f"Added {cuisine} to preferences.")
            elif sub == '2':
                if not prefs:
                    print("No preferences to remove.")
                else:
                    for i, p in enumerate(prefs):
                        print(f"{i+1}: {p}")
                    sel = input("Select number to remove (0 cancel): ")
                    if sel != '0':
                        try:
                            idx = int(sel) - 1
                            remove_preference(prefs[idx])
                            print(f"Removed {prefs[idx]} from preferences.")
                        except:
                            print("Invalid selection.")
            elif sub == '3':
                confirm = input("Clear all preferences? (y/n): ")
                if confirm.lower() == 'y':
                    clear_preferences()
                    print("Cleared all preferences.")
            elif sub == '4':
                break
            else:
                print("Invalid choice.")

    elif choice == '6':
        break
