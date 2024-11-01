from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404, redirect
from djoser.views import UserViewSet
from rest_framework.pagination import LimitOffsetPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.db.models import Sum
from rest_framework.permissions import IsAuthenticated

from api.permissions import IsAuthorOrReadOnly
from api.filters import NameFilter, NameAuthorFilter
from recipe.models import (User, Tag, Ingredient,
                           Subscription, Recipe, Favorite, ShoppingCart)
from api.serializers import (UserSerializer, TagSerializer,
                             IngredientSerializer,
                             PutAvatarSerializer, NewSubscribeSerializer,
                             SubscriptionSerializer, ShowRecipeSerializer,
                             NewRecipeSerializer,
                             FavoriteSerializer, CartSerializer)


class UserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = LimitOffsetPagination

    @action(
        methods=['put', 'delete'],
        permission_classes=(IsAuthenticated,),
        detail=False,
        url_path='me/avatar'
    )
    def upload_avatar(self, request, pk=None):
        if request.method == 'PUT':
            serializer = PutAvatarSerializer(
                request.user,
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            user = request.user
            user.avatar = None
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['post', 'delete'],
        detail=True,
        url_path='subscribe',
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id=None):
        if request.method == 'POST':
            subscribe_to = get_object_or_404(User, id=id)
            serializer = NewSubscribeSerializer(
                data={},
                context={'request': request, 'subscribe_to': subscribe_to}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            subscribed_to_user = get_object_or_404(User, id=id)
            subscription = get_object_or_404(
                Subscription,
                user=request.user,
                subsсribed_to=subscribed_to_user
            )
            subscription.delete()
            return Response(
                {'detail': 'Успешная отписка'},
                status=status.HTTP_204_NO_CONTENT
            )


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [
        DjangoFilterBackend,
    ]
    filterset_class = NameFilter


class SubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = SubscriptionSerializer
    pagination_class = LimitOffsetPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = [
        DjangoFilterBackend,
    ]
    filterset_class = NameAuthorFilter
    permission_classes = [IsAuthorOrReadOnly]

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'partial_update':
            return NewRecipeSerializer
        else:
            return ShowRecipeSerializer

    @action(
        methods=['post', 'delete'],
        detail=True, url_path='favorite',
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk=None):
        if request.method == 'POST':
            recipe = get_object_or_404(Recipe, pk=pk)
            data = {'user': request.user.id, 'recipe': recipe.id}
            serializer = FavoriteSerializer(
                data=data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            recipe = get_object_or_404(Recipe, pk=pk)
            favorite = get_object_or_404(
                Favorite,
                user=request.user,
                recipe=recipe
            )
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['post', 'delete'],
        detail=True,
        url_path='shopping_cart',
        permission_classes=(IsAuthenticated,)
    )
    def cart(self, request, pk=None):
        if request.method == 'POST':
            recipe = get_object_or_404(Recipe, pk=pk)
            data = {'user': request.user.id, 'recipe': recipe.id}
            serializer = CartSerializer(
                data=data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            recipe = get_object_or_404(Recipe, pk=pk)
            cart = get_object_or_404(
                ShoppingCart,
                user=request.user,
                recipe=recipe
            )
            cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['get'],
        detail=False,
        url_path='download_shopping_cart',
        permission_classes=(IsAuthenticated,)
    )
    def download(self, request, pk=None):
        ingredients = Ingredient.objects.filter(
            recipe_ingredient__recipe__carts__user=request.user
        ).annotate(
            total=Sum('recipe_ingredient__amount'))
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = ('attachment; filename'
                                           '="list_of_ingredients.txt"')
        for ingredient in ingredients:
            response.write(
                (f"{ingredient.name}, кол-во"
                 f" {ingredient.total} {ingredient.measurement_unit}")
            )
        return response

    @action(methods=['get'], detail=True, url_path='get-link')
    def short(self, request, pk=None):
        short = get_object_or_404(Recipe, pk=pk).short
        short = request.build_absolute_uri(f'/api/s/{short}')
        return Response({'short-link': short})


def url(request, short):
    recipe = get_object_or_404(Recipe, short=short)
    return redirect(f'/recipes/{recipe.id}')
