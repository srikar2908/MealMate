document.addEventListener("DOMContentLoaded", function () {
    const searchInput = document.getElementById("searchInput");
    const searchButton = document.getElementById("searchButton");
    const suggestionsList = document.getElementById("suggestions");
    const selectedList = document.getElementById("selectedList");
    const hiddenIngredients = document.getElementById("hiddenIngredients");
    const ingredientsForm = document.getElementById("ingredientsForm");
    const recipeResults = document.getElementById("recipeResults");

    let selectedIngredients = JSON.parse(localStorage.getItem("selectedIngredients")) || [];

    // Fetch ingredient suggestions from Django backend (Edamam API)
    async function fetchIngredientSuggestions(query) {
        try {
            const response = await fetch(`/fetch_ingredients?search_terms=${query}`);
            const data = await response.json();
            return data.hints ? data.hints.map(item => item.food.label) : [];
        } catch (error) {
            console.error("Error fetching ingredient suggestions:", error);
            return [];
        }
    }

    // Display ingredient suggestions
    function displaySuggestions(suggestions) {
        suggestionsList.innerHTML = "";
        if (suggestions.length === 0) {
            suggestionsList.style.display = "none";
            return;
        }
        suggestions.forEach((item) => {
            const li = document.createElement("li");
            li.textContent = item;
            li.addEventListener("click", function () {
                addIngredient(item);
                searchInput.value = "";
                suggestionsList.style.display = "none";
            });
            suggestionsList.appendChild(li);
        });
        suggestionsList.style.display = "block";
    }

    // Handle real-time search input
    searchInput.addEventListener("keyup", async function (e) {
        const query = e.target.value.trim().toLowerCase();
        if (query) {
            const suggestions = await fetchIngredientSuggestions(query);
            displaySuggestions(suggestions);
        } else {
            suggestionsList.style.display = "none";
        }
    });

    // Add ingredient to selected list
    function addIngredient(item) {
        if (!selectedIngredients.includes(item)) {
            selectedIngredients.push(item);
            localStorage.setItem("selectedIngredients", JSON.stringify(selectedIngredients));
            displaySelectedIngredients();
        }
    }

    // Display selected ingredients
    function displaySelectedIngredients() {
        selectedList.innerHTML = "";
        if (selectedIngredients.length === 0) {
            selectedList.innerHTML = "<p>No ingredients selected yet.</p>";
            return;
        }
        selectedIngredients.forEach((item, index) => {
            const li = document.createElement("li");
            li.classList.add("ingredient-pill");
            const span = document.createElement("span");
            span.textContent = item;
            const removeButton = document.createElement("button");
            removeButton.classList.add("remove-btn");
            removeButton.textContent = "×";
            removeButton.addEventListener("click", function () {
                selectedIngredients.splice(index, 1);
                localStorage.setItem("selectedIngredients", JSON.stringify(selectedIngredients));
                displaySelectedIngredients();
            });
            li.appendChild(span);
            li.appendChild(removeButton);
            selectedList.appendChild(li);
        });
    }

    // Submit form with selected ingredients
    ingredientsForm.addEventListener("submit", function (e) {
        hiddenIngredients.value = selectedIngredients.join(",");
    });

    // Fetch recipes from Django backend (Edamam API)
    async function fetchRecipes() {
        if (selectedIngredients.length === 0) {
            alert("Please select at least one ingredient.");
            return;
        }
        try {
            const query = selectedIngredients.join(",");
            const response = await fetch(`/get_recipes?ingredients=${query}`);
            const data = await response.json();
            displayRecipes(data.recipes);
        } catch (error) {
            console.error("Error fetching recipes:", error);
        }
    }

    // Display fetched recipes
    function displayRecipes(recipes) {
        recipeResults.innerHTML = "";
        if (!recipes || recipes.length === 0) {
            recipeResults.innerHTML = "<p>No recipes found. Try different ingredients!</p>";
            return;
        }
        recipes.forEach(recipe => {
            let recipeCard = `
                <div class="recipe-card">
                    <h4>${recipe.label}</h4>
                    <img src="${recipe.image}" alt="${recipe.label}">
                    <p><strong>Calories:</strong> ${Math.round(recipe.calories)} kcal</p>
                    <a href="${recipe.url}" target="_blank" class="btn">View Recipe</a>
                </div>
            `;
            recipeResults.innerHTML += recipeCard;
        });
    }

    // Initial display
    displaySelectedIngredients();
});
