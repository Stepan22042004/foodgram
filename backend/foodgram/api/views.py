from recipe.models import (Tag, Recipe, Ingredient,
                           User, Favorite, ShoppingCart, Subscription)
from api.serializers import (TagSerializer, IngredientSerializer,
                             RecipeReadSerializer, RecipeWriteSerializer,
                             FavoriteSerializer,
                             SubscriptionSerializer, ShoppingCartSerializer)
from rest_framework import status, viewsets
from rest_framework.response import Response
from .serializers import UserSerializer, UserAvatarPutSerializer
from rest_framework.pagination import PageNumberPagination
from django.http import HttpResponse
from django.db.models import Sum
from rest_framework.permissions import IsAuthenticated
from djoser.views import UserViewSet
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from api.permissions import IsAuthorOrReadOnly
from api.filters import RecipeFilter, IngredientFilter


class UserViewSet(UserViewSet):
    serializer_class = UserSerializer
    pagination_class = LimitOffsetPagination
    queryset = User.objects.all()

    @action(
        detail=False,
        methods=['put'],
        url_path='me/avatar',
        permission_classes=(IsAuthenticated,)
    )
    def avatar(self, request, pk=None):
        user = request.user
        serializer = UserAvatarPutSerializer(
            user, data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @avatar.mapping.delete
    def delete_avatar(self, request, pk=None):
        user = request.user
        user.avatar = None
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post'],
        url_path='subscribe',
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id=None):
        """
        Создает подписку на другого пользователя.
        """
        subscribed_to = get_object_or_404(User, id=id)

        data = {'subscribed_to': subscribed_to.id}

        serializer = SubscribeSerializer(
            data=data, context={'request': request}
        )

        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id=None):
        """
        Удаляет подписку на другого пользователя.
        """
        current_user = request.user
        subscribed_to_user = get_object_or_404(User, id=id)
        delete_cnt, _ = Subscription.objects.filter(
            user=current_user, subscribed_to=subscribed_to_user
        ).delete()

        if not delete_cnt:
            return Response(
                {"detail": "Вы не подписаны на этого пользователя."},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(status=status.HTTP_204_NO_CONTENT)	


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Представление для управления отзывами."""
    serializer_class = TagSerializer
    pagination_class = None
    queryset = Tag.objects.all()


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Представление для управления отзывами."""

    serializer_class = IngredientSerializer
    pagination_class = None
    queryset = Ingredient.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    """
    Вьюсет для управления рецептами.
    """
    queryset = Recipe.objects.all().order_by('-id')
    pagination_class = PageNumberPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    permission_classes = [IsAuthorOrReadOnly]

    def get_serializer_class(self):
        """
        Возвращает сериализатор в зависимости от действия.
        """
        if self.action in ['create', 'partial_update']:
            return RecipeWriteSerializer
        return RecipeReadSerializer

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        """
        Возвращает короткую ссылку на рецепт.
        """
        recipe = self.get_object()
        link = request.build_absolute_uri(f'/api/r/{recipe.short_url}')
        return Response({'short-link': link})

    @action(
        detail=True, methods=['post'],
        url_path='favorite', permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk=None):
        """
        Добавляет рецепт в избранное.
        """
        recipe = self.get_object()

        data = {'recipe': recipe.id}

        serializer = FavoriteSerializer(
            data=data, context={'request': request}
        )

        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        """
        Удаляет рецепт из избранного.
        """
        recipe = self.get_object()
        current_user = request.user
        delete_cnt, _ = Favorite.objects.filter(
            user=current_user, recipe=recipe
        ).delete()

        if not delete_cnt:
            return Response(
                {"detail": "Данный рецепт не добавлен в избранное."},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True, methods=['post'], url_path='shopping_cart',
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk=None):
        """
        Добавляет рецепт в корзину покупок.
        """
        recipe = self.get_object()

        data = {'recipe': recipe.id}

        serializer = ShoppingCartSerializer(
            data=data, context={'request': request}
        )

        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        """
        Удаляет рецепт из корзины покупок.
        """
        recipe = self.get_object()
        current_user = request.user
        delete_cnt, _ = ShoppingCart.objects.filter(
            user=current_user, recipe=recipe
        ).delete()

        if not delete_cnt:
            return Response(
                {"detail": "Данный рецепт не добавлен в корзину."},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False, methods=['get'],
        url_path='download_shopping_cart',
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        """
        Создает и возвращает текстовый файл со списком покупок
        для текущего пользователя.
        """
        ingredients = Ingredient.objects.filter(
            recipeingredient__recipe__shopping_carts__user=request.user
        ).values('name', 'measurement_unit').annotate(
            total_amount=Sum('recipeingredient__amount')
        )

        content = 'Список покупок:\n\n'
        for item in ingredients:
            content += (
                f"{item['name']} ({item['measurement_unit']}): "
                f"{item['total_amount']}\n"
            )

        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )

        return response


class SubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Вьюсет для отображения подписок текущего пользователя.
    """
    serializer_class = SubscriptionSerializer
    pagination_class = LimitOffsetPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Возвращает список подписок текущего пользователя.
        """
        return Subscription.objects.filter(user=self.request.user)
