from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (UserViewSet, TagViewSet, IngredientViewSet,
                       SubscriptionViewSet, RecipeViewSet, url)

router = DefaultRouter()

router.register('ingredients', IngredientViewSet)
router.register('tags', TagViewSet)
router.register(
    'users/subscriptions',
    SubscriptionViewSet,
    basename='subscriptions')
router.register('users', UserViewSet)
router.register('recipes', RecipeViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('s/<str:short>/', url)
]
