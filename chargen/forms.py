# chargen/forms.py
from django import forms
from .models import Character, Race, CharacterClass, STANDARD_ARRAY


# Define ability score keys for easier iteration
ABILITY_SCORES = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']

class CharacterCreateForm(forms.ModelForm):
    # Make sure Race and Class dropdowns are populated correctly
    race = forms.ModelChoiceField(queryset=Race.objects.all(), empty_label="-- Select Race --")
    character_class = forms.ModelChoiceField(queryset=CharacterClass.objects.all(), empty_label="-- Select Class --")

    # Hidden field to store the generated/standard stats between POST requests
    generated_stats = forms.CharField(widget=forms.HiddenInput(), required=False)
    # Fields for assigning the stats - these will be ChoiceFields,
    strength_assignment = forms.ChoiceField(required=False, label="Assign to Strength")
    dexterity_assignment = forms.ChoiceField(required=False, label="Assign to Dexterity")
    constitution_assignment = forms.ChoiceField(required=False, label="Assign to Constitution")
    intelligence_assignment = forms.ChoiceField(required=False, label="Assign to Intelligence")
    wisdom_assignment = forms.ChoiceField(required=False, label="Assign to Wisdom")
    charisma_assignment = forms.ChoiceField(required=False, label="Assign to Charisma")

    class Meta:
        model = Character
        fields = ['name', 'race', 'character_class', 'stat_method']  # Initial fields

    def __init__(self, *args, **kwargs):
        # Pop available stats if they are passed during form instantiation (from the view)
        available_stats = kwargs.pop('available_stats', None)
        super().__init__(*args, **kwargs)

        if available_stats:
            # Prepare choices for the assignment dropdowns
            # Ensure choices are strings for the ChoiceField
            stat_choices = [(str(stat), str(stat)) for stat in sorted(available_stats, reverse=True)]
            # Add an empty choice
            stat_choices.insert(0, ('', '-- Select Stat --'))

            # Set the choices for all assignment fields
            for ability in ABILITY_SCORES:
                field_name = f'{ability}_assignment'
                self.fields[field_name].choices = stat_choices
                self.fields[field_name].required = True  # Make them required once stats are generated

        else:
            # If no stats available yet (initial form load), remove assignment fields visually
            # (they still exist in the form class, just won't render if not in fields list)
            # Or, alternatively (and perhaps better), keep them but let the template hide them
            # Let's keep them and handle visibility in the template.
            for ability in ABILITY_SCORES:
                field_name = f'{ability}_assignment'
                # Ensure they don't have choices initially to avoid errors
                self.fields[field_name].choices = [('', '-- Select Stat --')]
                self.fields[field_name].required = False

    def clean(self):
        cleaned_data = super().clean()
        generated_stats_str = cleaned_data.get('generated_stats')

        # This validation runs only when assignment fields are expected (stage 2)
        if generated_stats_str:
            try:
                # Parse the hidden field back into a list of integers
                expected_stats = sorted([int(s) for s in generated_stats_str.split(',')], reverse=True)
            except (ValueError, TypeError):
                raise forms.ValidationError("Invalid generated stats data.")

            assigned_stats_values = []
            assigned_stats_fields = []

            for ability in ABILITY_SCORES:
                field_name = f'{ability}_assignment'
                assigned_value_str = cleaned_data.get(field_name)
                if not assigned_value_str:
                    # This should ideally be caught by required=True, but double-check
                    self.add_error(field_name, "This field is required.")
                    continue  # Skip if missing, though form should catch it

                try:
                    assigned_value = int(assigned_value_str)
                    assigned_stats_values.append(assigned_value)
                    assigned_stats_fields.append(assigned_value)  # Keep track for duplicate check
                except (ValueError, TypeError):
                    # This shouldn't happen with a ChoiceField, but good practice
                    self.add_error(field_name, "Invalid stat value selected.")

            # Check if all assignment fields were found (basic check)
            if len(assigned_stats_values) != len(ABILITY_SCORES):
                # This indicates a bigger problem, likely caught by individual field requirements
                raise forms.ValidationError("All ability scores must be assigned.")

            # --- Core Validation ---
            # 1. Check if the set of assigned stats matches the set of expected stats
            if sorted(assigned_stats_values, reverse=True) != expected_stats:
                raise forms.ValidationError(
                    f"The assigned stats {sorted(assigned_stats_values, reverse=True)} must exactly match the available stats {expected_stats}."
                )

            # 2. Check if any stat value was assigned more than once
            if len(assigned_stats_values) != len(set(assigned_stats_values)):
                raise forms.ValidationError("Each available stat can only be assigned to one ability score.")

        return cleaned_data