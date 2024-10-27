from django.contrib import admin
from recipe.models import (Tag, Recipe, Ingredient,
                           RecipeIngredient, Favorite, ShoppingCart)

admin.site.register(Tag)
admin.site.register(Recipe)
admin.site.register(Ingredient)
admin.site.register(RecipeIngredient)
admin.site.register(Favorite)
admin.site.register(ShoppingCart)
