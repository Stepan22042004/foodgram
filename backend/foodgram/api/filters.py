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
    tags = django_filters.NumberFilter(lookup_expr='slug__exact')

    class Meta:
        model = Recipe
        fields = []
