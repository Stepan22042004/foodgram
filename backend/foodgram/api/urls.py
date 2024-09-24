from django.urls import include, path
from rest_framework.routers import DefaultRouter
from api.views import (TagViewSet, IngredientViewSet,
                       UserViewSet, RecipeViewSet, SubscriptionViewSet)

router = DefaultRouter()
router.register('tags', TagViewSet, basename='tag')
router.register('ingredients', IngredientViewSet, basename='ingredient')
router.register(
    'users/subscriptions', SubscriptionViewSet, basename='subscriptions'        
)
router.register('users', UserViewSet, basename='users')
router.register('recipes', RecipeViewSet, basename='recipes')


urlpatterns = [
    path('', include(router.urls)),
    path('r/<str:short_code>/', redirect_to_recipe, name='redirect_to_recipe'),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
