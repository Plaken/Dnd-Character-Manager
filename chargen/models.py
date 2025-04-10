# chargen/models.py
from django.db import models
import random

STAT_METHOD_CHOICES = [
    ('roll', 'Roll (4d6 drop lowest)'),
    ('standard', 'Standard Array (15,14,13,12,10,8)'),
]
STANDARD_ARRAY = [15, 14, 13, 12, 10, 8]

# Helper function for rolling ability scores (4d6 drop lowest)
def roll_4d6_drop_lowest():
    rolls = sorted([random.randint(1, 6) for _ in range(4)], reverse=True)
    return sum(rolls[:3]) # Sum the top 3

class Race(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    # Add more fields later: ability score increases, traits, etc.

    def __str__(self):
        return self.name

class CharacterClass(models.Model): # Renamed from Class to avoid python keyword clash
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    hit_die = models.PositiveIntegerField(default=8) # e.g., d8
    # Add more fields later: proficiencies, starting equipment, features, etc.

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Character Classes" # Nicer name in admin

class Character(models.Model):
    name = models.CharField(max_length=100)
    race = models.ForeignKey(Race, on_delete=models.SET_NULL, null=True)
    character_class = models.ForeignKey(CharacterClass, on_delete=models.SET_NULL, null=True) # Renamed field
    level = models.PositiveIntegerField(default=1)
    stat_method = models.CharField(max_length=10, choices=STAT_METHOD_CHOICES, default='roll')
    # Ability Scores
    # Ability Scores - Keep these as the final destination
    strength = models.PositiveIntegerField(default=10)
    dexterity = models.PositiveIntegerField(default=10)
    constitution = models.PositiveIntegerField(default=10)
    intelligence = models.PositiveIntegerField(default=10)
    wisdom = models.PositiveIntegerField(default=10)
    charisma = models.PositiveIntegerField(default=10)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        # Handle potential None values for race/class gracefully
        race_name = self.race.name if self.race else "No Race"
        class_name = self.character_class.name if self.character_class else "No Class"
        return f"{self.name} (Level {self.level} {race_name} {class_name})"


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Add more fields later: background, alignment, skills, hp, inventory, spells etc.

    def __str__(self):
        return f"{self.name} (Level {self.level} {self.race} {self.character_class})"

    def roll_stats(self):
        """Sets random stats using 4d6 drop lowest"""
        self.strength = roll_4d6_drop_lowest()
        self.dexterity = roll_4d6_drop_lowest()
        self.constitution = roll_4d6_drop_lowest()
        self.intelligence = roll_4d6_drop_lowest()
        self.wisdom = roll_4d6_drop_lowest()
        self.charisma = roll_4d6_drop_lowest()
        # Note: This method needs to be explicitly called, typically before saving a new character.
        # We will call this from the view during creation.


    def assign_stats(self, stat_values: dict):
        """
        Assigns stats from a dictionary like:
        {
            'strength': 15,
            'dexterity': 14,
            'constitution': 13,
            'intelligence': 12,
            'wisdom': 10,
            'charisma': 8
        }
        """
        fields = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']

        # Check that all stats are present and not None
        missing = [k for k in fields if stat_values.get(k) is None]
        if missing:
            raise ValueError(f"Missing or empty stat values: {', '.join(missing)}")

        # Optional: Check that the values match the standard array
        if sorted(stat_values.values(), reverse=True) != sorted(STANDARD_ARRAY, reverse=True):
            raise ValueError("Stat values must match the standard array.")

        for field, value in stat_values.items():
            setattr(self, field, value)

