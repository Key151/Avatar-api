"""Rotas do app personagens."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.lista_personagens, name="lista-personagens"),
]
