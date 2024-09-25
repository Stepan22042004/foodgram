import csv

from django.core.management import BaseCommand
from recipe.models import Ingredient


class Command(BaseCommand):
    def handle(self, *args, **options):
        with open('/data/ingredients.csv', 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                name = row[0]
                measurement_unit = row[1]
                ingredient = Ingredient(
                    name=name, measurement_unit=measurement_unit
                )
                ingredient.save()
