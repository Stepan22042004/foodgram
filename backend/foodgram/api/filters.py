import django_filters

from recipe.models import Ingredient, Recipe


class NameFilter(django_filters.FilterSet):

    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='startswith'
    )

    class Meta:
        model = Ingredient
        fields = []


class NameAuthorFilter(django_filters.FilterSet):

    author = django_filters.NumberFilter(lookup_expr='id__exact')
    tags = django_filters.CharFilter(lookup_expr='slug__exact')
    is_favorited = django_filters.rest_framework.filters.BooleanFilter(
        method='favorited'
    )
    is_in_shopping_cart = django_filters.rest_framework.filters.BooleanFilter(
        method='shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = []

    def favorited(self, queryset, name, value):
        user = self.request.user
        if user.is_anonymous:
            return queryset
        if value:
            return queryset.filter(favorites__user=user)
        return queryset.exclude(favorites__user=user)

    def shopping_cart(self, queryset, name, value):
        user = self.request.user
        if user.is_anonymous:
            return queryset
        if value:
            return queryset.filter(carts__user=user)
        return queryset.exclude(carts__user=user)
