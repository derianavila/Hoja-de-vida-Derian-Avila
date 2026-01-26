from django.contrib import admin
from .models import (
    Datospersonales,
    Cursosrealizados,
    Experiencialaboral,
    Productosacademicos,
    Productoslaborales,
    Reconocimientos,
    Ventagarage,
)

# =========================
# PERSONALIZAR TÍTULOS DEL ADMIN
# =========================
admin.site.site_header = "Panel de Administración"
admin.site.site_title = "Panel Administrativo"
admin.site.index_title = "Gestión del Sistema"


@admin.register(Datospersonales)
class DatospersonalesAdmin(admin.ModelAdmin):
    list_display = ("idperfil", "nombres", "apellidos", "perfilactivo", "permitir_impresion")
    list_editable = ("perfilactivo", "permitir_impresion")
    list_filter = ("perfilactivo", "permitir_impresion")
    search_fields = ("nombres", "apellidos", "numerocedula")


@admin.register(Cursosrealizados)
class CursosrealizadosAdmin(admin.ModelAdmin):
    list_display = (
        "nombrecurso",
        "fechainicio",
        "fechafin",
        "totalhoras",
        "perfil",
        "activarparaqueseveaenfront",
        "certificado_pdf",
        "certificado_imagen",
    )
    list_editable = ("activarparaqueseveaenfront",)
    list_filter = ("activarparaqueseveaenfront",)
    search_fields = ("nombrecurso", "entidadpatrocinadora")


@admin.register(Experiencialaboral)
class ExperiencialaboralAdmin(admin.ModelAdmin):
    list_display = (
        "cargodesempenado",
        "nombrempresa",
        "fechainicio",
        "fechafin",
        "perfil",
        "activarparaqueseveaenfront",
        "certificado_pdf",
        "certificado_imagen",
    )
    list_editable = ("activarparaqueseveaenfront",)
    list_filter = ("activarparaqueseveaenfront",)
    search_fields = ("cargodesempenado", "nombrempresa")


@admin.register(Productosacademicos)
class ProductosacademicosAdmin(admin.ModelAdmin):
    list_display = (
        "nombreproducto",   # ✅ ahora es el importante
        "clasificador",
        "perfil",
        "activarparaqueseveaenfront",
        "imagenproducto",
        "certificado_pdf",
        "certificado_imagen",
    )
    list_editable = ("activarparaqueseveaenfront",)
    list_filter = ("activarparaqueseveaenfront", "clasificador")
    search_fields = ("nombreproducto", "nombrerecurso", "clasificador")


@admin.register(Productoslaborales)
class ProductoslaboralesAdmin(admin.ModelAdmin):
    list_display = (
        "nombreproducto",
        "fechaproducto",
        "perfil",
        "activarparaqueseveaenfront",
        "imagenproducto",
        "certificado_pdf",
        "certificado_imagen",
    )
    list_editable = ("activarparaqueseveaenfront",)
    list_filter = ("activarparaqueseveaenfront",)
    search_fields = ("nombreproducto", "descripcion")


@admin.register(Reconocimientos)
class ReconocimientosAdmin(admin.ModelAdmin):
    list_display = (
        "tiporeconocimiento",
        "fechareconocimiento",
        "entidadpatrocinadora",
        "perfil",
        "activarparaqueseveaenfront",
        "certificado_pdf",
        "certificado_imagen",
    )
    list_editable = ("activarparaqueseveaenfront",)
    list_filter = ("tiporeconocimiento", "activarparaqueseveaenfront")
    search_fields = ("entidadpatrocinadora", "descripcionreconocimiento")


@admin.register(Ventagarage)
class VentagarageAdmin(admin.ModelAdmin):
    list_display = (
        "nombreproducto",
        "estadoproducto",
        "fecha",  # ✅ nuevo campo
        "valordelbien",
        "perfil",
        "activarparaqueseveaenfront",
        "foto_producto",
    )
    list_editable = ("activarparaqueseveaenfront",)
    list_filter = ("estadoproducto", "activarparaqueseveaenfront")
    search_fields = ("nombreproducto", "descripcion")
