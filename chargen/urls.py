# chargen/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.CharacterListView.as_view(), name='character_list'),
    path('character/<int:pk>/', views.CharacterDetailView.as_view(), name='character_detail'),
    path('character/new/', views.CharacterCreateView.as_view(), name='character_create'),
    path('character/<int:character_id>/delete/', views.delete_character, name='delete_character')
    # Add URLs for update/delete later
]