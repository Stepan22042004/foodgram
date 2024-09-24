from django.urls import include, path
from rest_framework.routers import DefaultRouter
from api.views import (TagViewSet, IngredientViewSet,
                       UserViewSet, RecipeViewSet, SubscriptionViewSet)

router = DefaultRouter()
router.register('tags', TagViewSet, basename='tag')
router.register('ingredients', IngredientViewSet, basename='ingredient')
router.register('users', UserViewSet, basename='users')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register(
    'users/subscriptions', SubscriptionViewSet, basename='subscriptions'
)

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
    path('', include('djoser.urls')),
]
