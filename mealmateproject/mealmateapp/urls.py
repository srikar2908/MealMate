from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),                  # Login/Signup page
    path('home/', views.home, name='home'),                     # Ingredient input page (after login/signup)
    path('meal/', views.meal, name='meal'),                     # Meal/results page
    path('get_recipes/', views.get_recipes, name='get_recipes'),# API: Get recipes
    path('fetch_ingredients/', views.fetch_ingredients, name='fetch_ingredients'),  # API: Ingredient suggestions
]
