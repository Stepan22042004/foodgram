from rest_framework import serializers
from recipe.models import (Tag, Ingredient, RecipeIngredient,
                           Recipe, Favorite, ShoppingCart, Subscription)
from recipe.models import User
from drf_extra_fields.fields import Base64ImageField


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id', 'username', 'first_name', 'last_name',
            'email', 'avatar'
        )
        read_only_fields = ('avatar',)


class UserAvatarPutSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True, allow_null=True)

    class Meta:
        model = User
        fields = ('avatar',)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        avatar_url = request.build_absolute_uri(instance.avatar.url)
        representation['avatar'] = avatar_url
        return representation


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        lookup_field = 'name'
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        lookup_field = 'name'
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount',)


class RecipeSimpleSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

    def get_image(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.image.url)


class RecipeReadSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = TagSerializer(read_only=True, many=True)
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients', read_only=True, many=True
    )
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'image', 'text', 'cooking_time', 'author', 'tags',
            'ingredients', 'is_favorited', 'is_in_shopping_cart'
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and request.user.favorites.filter(recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and request.user.shopping_carts.filter(
                user=request.user, recipe=obj
            ).exists()
        )


class RecipeWriteSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    ingredients = RecipeIngredientSerializer(many=True)
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'image', 'name', 'text', 'cooking_time'
        )

    def validate(self, data):
        tags = data.get('tags')
        ingredients = data.get('ingredients')
        image = data.get('image')

        if not tags:
            raise serializers.ValidationError(
                "Нужно добавить хотя бы один тег."
            )
        if not ingredients:
            raise serializers.ValidationError(
                "Нужно добавить хотя бы один ингредиент."
            )
        if not image:
            raise serializers.ValidationError(
                "Нужно добавить изображение рецепта."
            )

        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                "Теги не должны дублироваться."
            )

        ingredient_ids = [item['ingredient'].id for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                "Ингредиенты не должны дублироваться."
            )

        return data

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')

        request = self.context.get('request')
        validated_data['author'] = request.user

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)

        self.create_ingredients(recipe, ingredients_data)

        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')

        super().update(instance, validated_data)

        instance.tags.set(tags_data)

        instance.ingredients.clear()
        self.create_ingredients(instance, ingredients_data)

        return instance

    @staticmethod
    def create_ingredients(recipe, ingredients_data):
        recipe_ingredients = []
        for ingredient_data in ingredients_data:
            recipe_ingredient = RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient_data['ingredient'],
                amount=ingredient_data['amount']
            )
            recipe_ingredients.append(recipe_ingredient)

        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('recipe',)

    def validate(self, data):
        recipe = data.get('recipe')
        user = self.context['request'].user
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                "Вы уже добавили этот рецепт в избранное"
            )
        data['user'] = user
        return data

    def to_representation(self, instance):
        return RecipeSimpleSerializer(
            instance.recipe, context=self.context
        ).data


class ShoppingCartSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShoppingCart
        fields = ('recipe',)

    def validate(self, data):
        recipe = data.get('recipe')
        user = self.context['request'].user
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                "Вы уже добавили этот рецепт в корзину"
            )
        data['user'] = user
        return data

    def to_representation(self, instance):
        return RecipeSimpleSerializer(
            instance.recipe, context=self.context
        ).data


class SubscriptionSerializer(serializers.ModelSerializer):
    follower = UserSerializer(
        source='subscribed_to', read_only=True
    )
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Subscription
        fields = ('follower', 'recipes', 'recipes_count')

    def get_recipes(self, obj):
        recipes = obj.subscribed_to.recipes.all()
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')

        if recipes_limit is not None:
            try:
                recipes_limit = int(recipes_limit)
                recipes = recipes[:recipes_limit]
            except ValueError:
                pass

        return RecipeSimpleSerializer(
            recipes, many=True, context=self.context
        ).data

    def get_recipes_count(self, obj):
        return obj.subscribed_to.recipes.count()

    def to_representation(self, instance):
        user_data = UserSerializer(
            instance.subscribed_to, context=self.context
        ).data
        recipes = self.get_recipes(instance)
        user_data['recipes'] = recipes
        user_data['recipes_count'] = self.get_recipes_count(instance)
        return user_data


class SubscribeSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = ('recipes', 'subscribed_to')

    def validate(self, data):
        subscribed_to_user = data.get('subscribed_to')
        current_user = self.context['request'].user
        if Subscription.objects.filter(
            user=current_user, subscribed_to=subscribed_to_user
        ).exists():
            raise serializers.ValidationError(
                "Вы уже подписаны на этого пользователя."
            )
        if current_user == subscribed_to_user:
            raise serializers.ValidationError(
                "Нельзя подписаться на самого себя."
            )
        data['user'] = current_user
        return data

    def to_representation(self, instance):
        return SubscriptionSerializer(instance, context=self.context).data
