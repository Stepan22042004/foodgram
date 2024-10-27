# Generated by Django 3.2.3 on 2024-10-21 19:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0003_alter_user_avatar'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipeingredient',
            name='recipe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ingredients_in_exact_recipe', to='recipe.recipe'),
        ),
    ]
