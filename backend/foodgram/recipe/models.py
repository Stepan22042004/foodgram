from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils.crypto import get_random_string



class User(AbstractUser):
    """Кастомная модель пользователя, наследуемая от AbstractUser."""
    username = models.CharField(max_length=50, unique=True, verbose_name='Имя пользователя')
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    avatar = models.ImageField(
        upload_to='users/avatars/',
        verbose_name='аватар',
        blank=True,
        null=True
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('first_name', 'last_name', 'username',)


    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=100)
    measurement_unit = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    name = models.CharField(
        max_length=1000,
        verbose_name='Название'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='recipes',
    )
    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to='recipe/images')
    text = models.TextField()
    ingredients = models.ManyToManyField(Ingredient, through='RecipeIngredient', related_name='recipes',)
    tags = models.ManyToManyField(Tag)
    cooking_time = models.PositiveIntegerField()
    short_url = models.CharField(
        max_length=200,
        unique=True,
        blank=True,
        null=True,
        verbose_name='Короткий url'
    )

    def __str__(self):
        return self.title

    def generate_short_url(self):
        """Генерирует уникальный короткий код."""
        while True:
            short_url = get_random_string(length=10)
            if not Recipe.objects.filter(short_url=short_url).exists():
                return short_url

    def save(self, *args, **kwargs):
        """Переопределяем метод save для генерации короткого кода."""
        if not self.short_url:
            self.short_url = self.generate_short_url()
        super().save(*args, **kwargs)


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='recipe_ingredients',)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.amount} of {self.ingredient.name} in {self.recipe.title}"


class UserRecipeBase(models.Model):
    """
    Базовая модель для связи пользователя с рецептом.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='пользователь'
    )
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        verbose_name='рецепт'
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_user_recipe'
            )
        ]

    def __str__(self):
        return f'{self.user} связан с {self.recipe.name}'


class Favorite(UserRecipeBase):
    """
    Модель избранного.
    """

    class Meta(UserRecipeBase.Meta):
        default_related_name = 'favorites'
        verbose_name = 'избранное'
        verbose_name_plural = 'Избранные'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return f'{self.user} добавил в избранное {self.recipe.name}'


class ShoppingCart(UserRecipeBase):
    """
    Модель корзины покупок.
    """

    class Meta(UserRecipeBase.Meta):
        default_related_name = 'shopping_carts'
        verbose_name = 'корзина покупок'
        verbose_name_plural = 'Корзина покупок'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_shopping_cart'
            )
        ]

    def __str__(self):
        return f'{self.user} добавил в корзину {self.recipe.name}'


class Subscription(models.Model):
    """
    Модель подписки.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='пользователь'
    )
    subscribed_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers',
        verbose_name='автор, на которого подписались'
    )

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'subscribed_to'),
                name='unique_subscription'
            ),
        ]

    def __str__(self):
        return f'{self.user} подписан на {self.subscribed_to}'
