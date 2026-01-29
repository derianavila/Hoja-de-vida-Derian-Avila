import io
import requests

from django.http import HttpResponse, HttpResponseForbidden, Http404
from django.shortcuts import render, get_object_or_404, redirect

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader, simpleSplit

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
# HELPERS
# =========================
def _get_perfil_activo():
    return Datospersonales.objects.filter(perfilactivo=True).order_by("-idperfil").first()


def _image_reader_from_field(image_field):
    """Compatible con Local y Cloudinary"""
    if not image_field:
        return None
    try:
        if hasattr(image_field, "url"):
            resp = requests.get(image_field.url, timeout=15)
            resp.raise_for_status()
            return ImageReader(io.BytesIO(resp.content))
        image_field.open("rb")
        return ImageReader(io.BytesIO(image_field.read()))
    except Exception as e:
        print("❌ Error cargando imagen en PDF:", e)
        return None
    finally:
        try:
            image_field.close()
        except Exception:
            pass


def _register_fonts():
    return "Helvetica", "Helvetica-Bold"


def _draw_wrapped(c, text, x, y, max_width, font, size, leading):
    if not text:
        return y
    lines = simpleSplit(str(text), font, size, max_width)
    for ln in lines:
        c.drawString(x, y, ln)
        y -= leading
    return y


# =========================
# VIEWS WEB
# =========================
def home(request):
    perfil = _get_perfil_activo()
    permitir_impresion = bool(perfil and perfil.permitir_impresion)

    counts = {
        "cursos": perfil.cursos.filter(activarparaqueseveaenfront=True).count() if perfil else 0,
        "experiencias": perfil.experiencias.filter(activarparaqueseveaenfront=True).count() if perfil else 0,
        "prod_acad": perfil.productos_academicos.filter(activarparaqueseveaenfront=True).count() if perfil else 0,
        "prod_lab": perfil.productos_laborales.filter(activarparaqueseveaenfront=True).count() if perfil else 0,
        "reconoc": perfil.reconocimientos.filter(activarparaqueseveaenfront=True).count() if perfil else 0,
        "venta": perfil.venta_garage.filter(activarparaqueseveaenfront=True).count() if perfil else 0,
    }

    return render(request, "home.html", {
        "perfil": perfil,
        "permitir_impresion": permitir_impresion,
        "counts": counts,
    })


def datos_personales(request):
    perfil = _get_perfil_activo()
    return render(request, "secciones/datos_personales.html", {"perfil": perfil})


def cursos(request):
    perfil = _get_perfil_activo()
    items = perfil.cursos.filter(activarparaqueseveaenfront=True).order_by("-fechafin", "-fechainicio") if perfil else []
    return render(request, "secciones/cursos.html", {"perfil": perfil, "items": items})


def experiencia(request):
    perfil = _get_perfil_activo()
    items = perfil.experiencias.filter(activarparaqueseveaenfront=True).order_by("-fechafin", "-fechainicio") if perfil else []
    return render(request, "secciones/experiencia.html", {"perfil": perfil, "items": items})


def productos_academicos(request):
    perfil = _get_perfil_activo()
    items = perfil.productos_academicos.filter(activarparaqueseveaenfront=True) if perfil else []
    return render(request, "secciones/productos_academicos.html", {"perfil": perfil, "items": items})


def productos_laborales(request):
    perfil = _get_perfil_activo()
    items = perfil.productos_laborales.filter(activarparaqueseveaenfront=True) if perfil else []
    return render(request, "secciones/productos_laborales.html", {"perfil": perfil, "items": items})


def reconocimientos(request):
    perfil = _get_perfil_activo()
    items = perfil.reconocimientos.filter(activarparaqueseveaenfront=True) if perfil else []
    return render(request, "secciones/reconocimientos.html", {"perfil": perfil, "items": items})


def venta_garage(request):
    perfil = _get_perfil_activo()
    items = perfil.venta_garage.filter(activarparaqueseveaenfront=True) if perfil else []
    return render(request, "secciones/venta_garage.html", {"perfil": perfil, "items": items})


# =========================
# PDF CERTIFICADO (CORREGIDO)
# =========================
def ver_certificado_pdf(request, curso_id):
    """
    Redirige directamente al PDF usando la URL real del FileField.
    SIN raw, SIN authenticated, SIN firmas.
    """
    curso = get_object_or_404(Cursosrealizados, idcursorealizado=curso_id)

    if not curso.certificado_pdf:
        raise Http404("Archivo no encontrado")

    return redirect(curso.certificado_pdf.url)
