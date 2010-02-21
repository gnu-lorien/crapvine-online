from django.db import models

# Create your models here.

class Trait(models.Model):
    name = models.CharField()
    note = models.CharField()

class Sheet(models.Model):
    name = models.CharField()
    traits = models.ManyToManyField(Trait, through='TraitCategory')

class TraitCategory(models.Model):
    sheet = models.ForeignKey(Sheet)
    trait = models.ForeignKey(Trait)
    name = models.SmallIntegerField(choices=((1, 'Physical'), (2, 'Social'))
    order = models.IntegerField()
    sorted = models.BooleanField()
