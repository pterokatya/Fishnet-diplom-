from django.urls import path
from .views import run_parser

urlpatterns = [
    path('run-parser/', run_parser, name='run-parser'),
]
