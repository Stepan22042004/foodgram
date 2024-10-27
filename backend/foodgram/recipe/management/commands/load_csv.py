import csv

from django.core.management import BaseCommand
from recipe.models import Ingredient

STATIC_DATA_PATH = 'static/data/'


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        self.import_ingredients()

    def import_ingredients(self):
        with open(
            STATIC_DATA_PATH + 'ingredients.csv',
            'r',
            encoding='utf-8'
        ) as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                Ingredient.objects.get_or_create(
                    name=row[0],
                    measurement_unit=row[1]
                )
