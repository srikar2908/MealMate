from django.shortcuts import render,redirect
from django.http import JsonResponse
from django.conf import settings
from . models import UserRegistration
import requests



def index(request):
    if request.method == 'POST':
        if 'signup_submit' in request.POST:
            # Handle signup
            name = request.POST.get('name')
            email = request.POST.get('email')
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')
            if password != confirm_password:
                return render(request, 'index.html', {'error': "Passwords do not match."})
            if UserRegistration.objects.filter(email=email).exists():
                return render(request, 'index.html', {'error': "Email already registered."})
            UserRegistration.objects.create(name=name, email=email, password=password)
            return redirect('home')
        elif 'login_submit' in request.POST:
            # Handle login (demo, not secure)
            email = request.POST.get('login_email')
            password = request.POST.get('login_password')
            if UserRegistration.objects.filter(email=email, password=password).exists():
                return redirect('home')
            else:
                return render(request, 'index.html', {'login_error': "Invalid credentials."})
    return render(request, 'index.html')



def home(request):
    return render(request, 'home.html')





def get_recipes(request):
    ingredients = request.GET.get("ingredients", "")
    recipes = get_recipes_data(ingredients)
    return JsonResponse({"recipes": recipes})

def get_recipes_data(ingredients):
    if not ingredients:
        return []
    try:
        response = requests.get(
            "https://api.spoonacular.com/recipes/findByIngredients",
            params={
                "ingredients": ingredients,
                "number": 10,
                "ranking": 1,
                "apiKey": settings.SPOONACULAR_API_KEY
            },
            timeout=15
        )
        response.raise_for_status()
        recipes = response.json()
        formatted_recipes = []
        for recipe in recipes:
            try:
                info_response = requests.get(
                    f"https://api.spoonacular.com/recipes/{recipe['id']}/information",
                    params={"includeNutrition": True, "apiKey": settings.SPOONACULAR_API_KEY},
                    timeout=15
                )
                info_response.raise_for_status()
                info_data = info_response.json()

                # Extract detailed nutrition
                nutrition = extract_nutrition(info_data)

                formatted_recipes.append({
                    "label": recipe.get("title", "Untitled Recipe"),
                    "image": recipe.get("image", ""),
                    "calories": nutrition["calories"],
                    "protein": nutrition["protein"],
                    "fat": nutrition["fat"],
                    "carbs": nutrition["carbs"],
                    "fiber": nutrition["fiber"],
                    "url": info_data.get("sourceUrl", f"https://spoonacular.com/recipes/{recipe['id']}")
                })
            except Exception as e:
                print(f"Error processing recipe {recipe.get('id')}: {str(e)}")
                continue
        return formatted_recipes
    except Exception as e:
        print(f"Recipe search error: {str(e)}")
        return []


def fetch_ingredients(request):
    query = request.GET.get("search_terms", "").strip()
    if not query:
        return JsonResponse({"error": "No search terms provided"}, status=400)

    try:
        response = requests.get(
            "https://api.spoonacular.com/food/ingredients/autocomplete",
            params={
                "query": query,
                "number": 10,
                "apiKey": settings.SPOONACULAR_API_KEY
            },
            timeout=15
        )
        response.raise_for_status()
        
        suggestions = [
            {"food": {"label": item["name"]}}
            for item in response.json()
            if isinstance(item, dict) and "name" in item
        ]
        
        return JsonResponse({"hints": suggestions})
    
    except requests.exceptions.RequestException as e:
        return JsonResponse(
            {"error": f"Spoonacular API error: {str(e)}"},
            status=500 if e.response is None else e.response.status_code
        )


# views.py
def get_nutrition_data(ingredients):
    nutrition_summary = {
        "calories": 0,
        "protein": 0,
        "carbs": 0,
        "fat": 0,
        "fiber": 0,
    }
    
    for ingredient in ingredients:
        try:
            # Get ingredient ID
            auto_url = "https://api.spoonacular.com/food/ingredients/autocomplete"
            auto_params = {
                "query": ingredient,
                "number": 1,
                "apiKey": settings.SPOONACULAR_API_KEY
            }
            auto_resp = requests.get(auto_url, params=auto_params, timeout=10)
            auto_resp.raise_for_status()
            auto_data = auto_resp.json()
            
            if not auto_data:
                continue
                
            ingredient_id = auto_data[0]['id']
            
            # Get nutrition data
            info_url = f"https://api.spoonacular.com/food/ingredients/{ingredient_id}/information"
            info_params = {
                "amount": 100,
                "unit": "g",
                "apiKey": settings.SPOONACULAR_API_KEY
            }
            info_resp = requests.get(info_url, params=info_params, timeout=10)
            info_resp.raise_for_status()
            info_data = info_resp.json()
            
            # Parse nutrients
            nutrients = info_data.get("nutrition", {}).get("nutrients", [])
            for nutrient in nutrients:
                name = nutrient.get("name", "").lower()
                amount = nutrient.get("amount", 0)
                
                if "calories" in name:
                    nutrition_summary["calories"] += amount
                elif "protein" in name:
                    nutrition_summary["protein"] += amount
                elif "carbohydrate" in name:
                    nutrition_summary["carbs"] += amount
                elif "fat" in name and "saturated" not in name:
                    nutrition_summary["fat"] += amount
                elif "fiber" in name:
                    nutrition_summary["fiber"] += amount
                    
        except Exception as e:
            print(f"Error fetching data for {ingredient}: {str(e)}")
    
    # Round values
    for key in nutrition_summary:
        nutrition_summary[key] = round(nutrition_summary[key], 2)
    
    return nutrition_summary

def meal(request):
    ingredients = request.GET.get("ingredients", "")
    ingredients_list = [ing.strip() for ing in ingredients.split(',') if ing.strip()]
    
    context = {
        "ingredients": ingredients_list,
        "nutrition_data": get_nutrition_data(ingredients_list) if ingredients_list else None,
        "recipes": get_recipes_data(ingredients) if ingredients_list else []
    }
    return render(request, 'meal.html', context)


def extract_nutrition(info_data):
    nutrition = {
        "calories": 0,
        "protein": 0,
        "fat": 0,
        "carbs": 0,
        "fiber": 0
    }
    nutrients = info_data.get("nutrition", {}).get("nutrients", [])
    for nutrient in nutrients:
        name = nutrient.get("name", "").lower()
        amount = nutrient.get("amount", 0)
        if "calorie" in name:
            nutrition["calories"] = round(amount, 2)
        elif "protein" in name:
            nutrition["protein"] = round(amount, 2)
        elif "fat" in name and "saturated" not in name:
            nutrition["fat"] = round(amount, 2)
        elif "carbohydrate" in name:
            nutrition["carbs"] = round(amount, 2)
        elif "fiber" in name:
            nutrition["fiber"] = round(amount, 2)
    return nutrition
