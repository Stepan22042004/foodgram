from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField
from rest_framework.exceptions import ValidationError

from recipe.models import (User, Ingredient, Tag, Subscription, Recipe,
                           RecipeIngredient, Favorite, ShoppingCart)


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'first_name',
            'last_name', 'email', 'is_subscribed', 'avatar'
        )
        read_only_fields = ['avatar']

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and \
           request.user.is_authenticated and Subscription.objects.filter(
                user=request.user, subsсribed_to=obj).exists():
            return True
        else:
            return False


class PutAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True, allow_null=True)

    class Meta:
        model = User
        fields = ('avatar',)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        representation['avatar'] = request.build_absolute_uri(
            instance.avatar.url
        )
        return representation

    def save(self, **kwargs):
        user = self.context['request'].user
        user.avatar = self.validated_data['avatar']
        user.save()


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        lookup_field = 'name'
        fields = ('id', 'name', 'slug')


class RecipesForSubscriptionSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

    def get_image(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.image.url)


class NewSubscribeSerializer(serializers.Serializer):

    def save(self, **kwargs):
        user = self.context.get('request').user
        follower = self.context.get('subscribe_to')
        if user == follower:
            raise ValidationError("Нельзя подписаться на самого себя")
        subscription, created = Subscription.objects.get_or_create(
            user=user,
            subsсribed_to=follower
        )
        if not created:
            raise ValidationError("Подписка уже существует")

        return subscription

    def to_representation(self, instance):
        follower = self.context.get('subscribe_to')
        user_data = UserSerializer(follower, context=self.context).data
        recipes = follower.recipes.all()
        param = self.context.get('request').query_params.get('recipes_limit')
        if param is None:
            pass
        else:
            recipes = recipes[0:int(param)]
        recipes = RecipesForSubscriptionSerializer(
            recipes, many=True, context=self.context
        ).data
        recipes_count = follower.recipes.count()
        user_data['recipes'] = recipes
        user_data['recipes_count'] = recipes_count
        return user_data


class SubscriptionSerializer(serializers.ModelSerializer):
    subsсribed_to = UserSerializer(read_only=True)
    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Subscription
        fields = ('subsсribed_to',)

    def get_recipes(self, obj):
        recipes = obj.subsсribed_to.recipes.all()
        param = self.context.get('request').query_params.get('recipes_limit')
        if param is None:
            pass
        else:
            recipes = recipes[0:int(param)]
        recipes = RecipesForSubscriptionSerializer(
            recipes,
            many=True,
            context=self.context
        ).data
        return recipes

    def get_recipes_count(self, obj):
        return obj.subsсribed_to.recipes.count()

    def to_representation(self, obj):
        user_data = UserSerializer(
            obj.subsсribed_to,
            context=self.context
        ).data
        user_data['recipes'] = self.get_recipes(obj)
        user_data['recipes_count'] = self.get_recipes_count(obj)
        return user_data


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    name = serializers.ReadOnlyField(
        source='ingredient.name'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount',)


class ShowRecipeSerializer(serializers.ModelSerializer):
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    author = UserSerializer()
    tags = TagSerializer(read_only=True, many=True)
    ingredients = IngredientInRecipeSerializer(
        source='ingredients_in_recipe',
        many=True,
        read_only=True
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            "id", "tags", "author", "ingredients", "is_favorited",
            "is_in_shopping_cart",
            "name", "image", "text", "cooking_time"
        )

    def get_is_favorited(self, obj):
        if self.context.get('request').user.is_authenticated and \
            Favorite.objects.filter(
                recipe=obj,
                user=self.context.get('request').user
        ).exists():
            return True
        else:
            return False

    def get_is_in_shopping_cart(self, obj):
        if self.context.get('request').user.is_authenticated and \
            ShoppingCart.objects.filter(
                recipe=obj,
                user=self.context.get('request').user
        ).exists():
            return True
        else:
            return False


class NewRecipeSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    ingredients = IngredientInRecipeSerializer(many=True, required=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('ingredients', 'tags', 'image',
                  'name', 'text', 'cooking_time',)

    def validate(self, data):
        tags = data['tags']
        ingredients = data['ingredients']
        image = data['image']
        list_of_ingredient_names = []

        for i in range(len(ingredients)):
            list_of_ingredient_names.append(ingredients[i]['ingredient'])

        if len(ingredients) == 0:
            raise ValidationError('В рецепте нет инградиентов')

        if len(image) == 0:
            raise ValidationError('Нет картинки')

        if len(tags) == 0:
            raise ValidationError('Нет тегов')

        if len(tags) != len(set(tags)):
            raise ValidationError('Есть одинаковые теги')

        if len(list_of_ingredient_names) != len(set(list_of_ingredient_names)):
            raise ValidationError('Есть одинаковые инградиенты')

        return data

    def create(self, validated_data):
        ingredients_list = validated_data.pop('ingredients')
        author = self.context.get('request').user
        name = validated_data.pop('name')
        text = validated_data.pop('text')
        cooking_time = validated_data.pop('cooking_time')
        tags = validated_data.pop('tags')
        image = validated_data.pop('image')

        recipe = Recipe.objects.create(
            name=name,
            image=image,
            text=text,
            cooking_time=cooking_time,
            author=author
        )
        recipe.tags.set(tags)
        for ingredient in ingredients_list:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount']
            )

        return recipe

    def update(self, instance, validated_data):
        ingredients_list = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        super().update(instance, validated_data)
        instance.ingredient.clear()
        instance.tags.set(tags)
        for ingredient in ingredients_list:
            RecipeIngredient.objects.create(
                recipe=instance,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount']
            )
        return instance

    def to_representation(self, instance):
        return ShowRecipeSerializer(instance, context=self.context).data


class FavoriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def validate(self, data):
        recipe = data.get('recipe')
        user = data.get('user')
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise ValidationError('duplicate')
        return data

    def to_representation(self, instance):
        return RecipesForSubscriptionSerializer(
            instance.recipe,
            context=self.context
        ).data


class CartSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def validate(self, data):
        recipe = data.get('recipe')
        user = data.get('user')
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise ValidationError('duplicate')
        return data

    def to_representation(self, instance):
        return RecipesForSubscriptionSerializer(
            instance.recipe,
            context=self.context
        ).data
