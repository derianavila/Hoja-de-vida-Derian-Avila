from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),

    # Secciones (para que no falle el {% url %} del template)
    path("datos-personales/", views.datos_personales, name="datos_personales"),
    path("cursos/", views.cursos, name="cursos"),
    path("experiencia/", views.experiencia, name="experiencia"),
    path("productos-academicos/", views.productos_academicos, name="productos_academicos"),
    path("productos-laborales/", views.productos_laborales, name="productos_laborales"),
    path("reconocimientos/", views.reconocimientos, name="reconocimientos"),
    path("venta-garage/", views.venta_garage, name="venta_garage"),

    # PDF final
    path("imprimir/", views.imprimir_hoja_vida, name="imprimir_hoja_vida"),
]
