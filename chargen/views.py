from django.shortcuts import render
# chargen/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView
from .models import Character, Race, CharacterClass, STANDARD_ARRAY, roll_4d6_drop_lowest # Import new items
from .forms import CharacterCreateForm, ABILITY_SCORES

class CharacterListView(ListView):
    model = Character
    template_name = 'chargen/character_list.html' # Specify our template
    context_object_name = 'characters' # Nicer variable name in template

class CharacterDetailView(DetailView):
    model = Character
    template_name = 'chargen/character_detail.html'
    context_object_name = 'character'

class CharacterCreateView(CreateView):
    model = Character
    form_class = CharacterCreateForm
    template_name = 'chargen/character_form.html'

    def get_form_kwargs(self):
        """Pass available stats to the form if they exist in context."""
        kwargs = super().get_form_kwargs()
        # Check if we are re-rendering the form with generated stats
        if 'available_stats' in self.kwargs:
            kwargs['available_stats'] = self.kwargs['available_stats']
        # Or if they were passed via POST (less common for GET, but safety)
        elif self.request.method == 'POST' and self.request.POST.get('generated_stats'):
            try:
                stats_str = self.request.POST.get('generated_stats')
                kwargs['available_stats'] = [int(s) for s in stats_str.split(',')]
            except (ValueError, TypeError):
                pass  # Let form validation handle bad data
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Create New Character"
        # Pass ability score keys to template for easier rendering
        context['ability_scores'] = ABILITY_SCORES

        # If we are re-rendering with generated stats, pass them for display
        if 'available_stats' in self.kwargs:
            context['available_stats'] = sorted(self.kwargs['available_stats'], reverse=True)
            context['show_assignment'] = True  # Flag for template
        # Check form instance passed in context if validation failed on stage 2
        elif isinstance(context.get('form'), CharacterCreateForm) and context['form'].data.get('generated_stats'):
            try:
                stats_str = context['form'].data.get('generated_stats')
                context['available_stats'] = sorted([int(s) for s in stats_str.split(',')], reverse=True)
                context['show_assignment'] = True
            except (ValueError, TypeError):
                context['show_assignment'] = False  # Error state
        else:
            context['show_assignment'] = False

        return context

    def post(self, request, *args, **kwargs):
        """
        Handles both stages of form submission:
        1. Initial POST with name, race, class, method. Generates stats.
        2. Second POST with assignments. Validates and saves.
        """
        # Determine if this POST includes stat assignments (Stage 2)
        # Check if 'strength_assignment' (or any other assignment field) is present in POST data.
        # A more robust check is the presence of our hidden 'generated_stats' field value.
        self.object = None
        is_assignment_stage = 'generated_stats' in request.POST and request.POST['generated_stats']

        if not is_assignment_stage:
            # --- Stage 1: Generate Stats ---
            form = self.get_form(self.form_class)  # Get unbound form to check initial data
            form.data = request.POST  # Bind POST data manually to check it
            form._is_bound = True  # Mark as bound

            # Basic validation for initial fields
            if form.is_valid():
                method = form.cleaned_data['stat_generation_method']
                available_stats = []

                if method == 'roll':
                    available_stats = [roll_4d6_drop_lowest() for _ in range(6)]
                elif method == 'standard':
                    available_stats = STANDARD_ARRAY[:]  # Use a copy

                if available_stats:
                    # Convert stats to string for hidden field
                    generated_stats_str = ",".join(map(str, available_stats))

                    # Prepare initial data for the form to be re-rendered
                    initial_data = form.cleaned_data.copy()  # Use cleaned data from valid form
                    initial_data['generated_stats'] = generated_stats_str

                    # Create a *new* form instance with initial data and available stats
                    # This form will have the assignment dropdowns populated correctly
                    new_form = self.form_class(initial=initial_data, available_stats=available_stats)

                    # Re-render the template with the new form and context
                    self.kwargs['available_stats'] = available_stats  # Pass stats for get_context_data
                    context = self.get_context_data(form=new_form)
                    return self.render_to_response(context)
                else:
                    # Method selected but didn't generate stats (e.g., invalid method value?)
                    form.add_error('stat_generation_method', 'Could not generate stats for this method.')
                    # Fall through to render form with errors

            # If initial form is invalid, render it back with errors
            context = self.get_context_data(form=form)
            return self.render_to_response(context)

        else:
            # --- Stage 2: Process Assignments and Save ---
            # Get the form populated with POST data, including assignments
            form = self.get_form(self.form_class)

            if form.is_valid():
                # Form.clean() has already validated that assignments match generated_stats
                # Create the character instance but don't save yet
                self.object = form.save(commit=False)

                # Assign stats from the cleaned assignment fields
                self.object.strength = int(form.cleaned_data['strength_assignment'])
                self.object.dexterity = int(form.cleaned_data['dexterity_assignment'])
                self.object.constitution = int(form.cleaned_data['constitution_assignment'])
                self.object.intelligence = int(form.cleaned_data['intelligence_assignment'])
                self.object.wisdom = int(form.cleaned_data['wisdom_assignment'])
                self.object.charisma = int(form.cleaned_data['charisma_assignment'])

                # --- TODO: Apply Racial Bonuses ---
                # Example (add this logic later):
                # if self.object.race:
                #     # Look up race bonuses (you'll need to add these fields to Race model)
                #     self.object.strength += self.object.race.strength_bonus
                #     self.object.dexterity += self.object.race.dexterity_bonus
                #     # ... etc ...

                # Save the complete character object
                self.object.save()

                # Redirect to the detail view
                return redirect(reverse('character_detail', kwargs={'pk': self.object.pk}))
            else:
                # Form is invalid (likely assignment mismatch caught by form.clean)
                # Re-render the form with errors. Need to pass available_stats again.
                try:
                    stats_str = form.data.get('generated_stats', '')
                    available_stats = [int(s) for s in stats_str.split(',')]
                    self.kwargs['available_stats'] = available_stats
                except (ValueError, TypeError):
                    # Handle case where generated_stats was somehow invalid in POST
                    pass  # Let the template handle the lack of available_stats if needed

                context = self.get_context_data(form=form)
                return self.render_to_response(context)

    def form_valid(self, form):
        # This method is now less relevant as the main logic is in post()
        # We handle saving and redirecting within the post() method's Stage 2.
        # We could potentially move the saving logic here, but keeping it
        # in post() makes the two-stage flow clearer.
        # For now, let's prevent the default CreateView behavior.
        # Returning the redirect from post() bypasses this.
        # If post() were to return super().form_valid(), this would run.
        pass

def delete_character(request, character_id):
    character = get_object_or_404(Character, id=character_id)
    if request.method == "POST":
        character.delete()
        return redirect('character_list')  # or wherever your list is
        return redirect('character_list')