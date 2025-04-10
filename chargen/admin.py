from django.contrib import admin
# chargen/admin.py
from django.contrib import admin
from .models import Race, CharacterClass, Character

admin.site.register(Race)
admin.site.register(CharacterClass)
admin.site.register(Character)
# Register your models here.
