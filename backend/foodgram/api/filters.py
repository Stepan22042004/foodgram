import django_filters
from django_filters.rest_framework import filters
from recipe.models import Ingredient, Recipe


class RecipeFilter(django_filters.FilterSet):
    """Фильтр для модели Recipe."""
    author = django_filters.NumberFilter(field_name='author__id')
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = django_filters.rest_framework.filters.BooleanFilter(
        method='filter_is_favorited'
    )
    is_in_shopping_cart = django_filters.rest_framework.filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def filter_is_favorited(self, queryset, name, value):
        """Фильтрует рецепты по статусу 'в избранном'."""
        user = self.request.user
        if user.is_anonymous:
            return queryset
        if value:
            return queryset.filter(favorites__user=user)
        return queryset.exclude(favorites__user=user)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Фильтрует рецепты по статусу 'в корзине покупок'."""
        user = self.request.user
        if user.is_anonymous:
            return queryset
        if value:
            return queryset.filter(shopping_carts__user=user)
        return queryset.exclude(shopping_carts__user=user)


class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name='name', lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredient
        fields = ('name',)
