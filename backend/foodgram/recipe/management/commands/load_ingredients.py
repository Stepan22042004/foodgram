import csv
from os import path

from django.core.management import BaseCommand
from recipe.models import Ingredient

ALREADY_LOADED_ERROR_MESSAGE = """
Если вам нужно перезагрузить данные об ингредиентах из CSV файла,
сначала удалите файл db.sqlite3, чтобы уничтожить базу данных.
Затем выполните команду `python manage.py migrate`, чтобы создать
новую пустую базу данных с таблицами.
"""


class Command(BaseCommand):
    """
    Команда для загрузки данных из файла data/ingredients.csv
    в модель Ingredient.
    """
    help = "Загружает данные из data/ingredients.csv"

    def handle(self, *args, **options):
        """
        Выполняет загрузку данных из CSV файла в базу данных.
        """
        if Ingredient.objects.exists():
            print('Данные об ингредиентах уже загружены... выход.')
            print(ALREADY_LOADED_ERROR_MESSAGE)
            return

        print("Загрузка данных об ингредиентах")

        with open('data/ingredients.csv', 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                name = row[0]
                measurement_unit = row[1]

                ingredient = Ingredient(
                    name=name, measurement_unit=measurement_unit
                )
                ingredient.save()

        print("Данные успешно загружены.")
