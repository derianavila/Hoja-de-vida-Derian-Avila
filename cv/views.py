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
# PDF – HOJA DE VIDA
# =========================
def imprimir_hoja_vida(request):
    perfil = _get_perfil_activo()

    if not perfil:
        return HttpResponse("Perfil no encontrado", status=404)
    if not perfil.permitir_impresion:
        return HttpResponseForbidden("No autorizado", status=403)

    FONT, FONT_B = _register_fonts()
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'inline; filename="hoja_de_vida.pdf"'

    c = canvas.Canvas(response, pagesize=A4)
    W, H = A4

    azul_oscuro = colors.HexColor("#1f2a33")
    gris = colors.HexColor("#6b7280")
    negro = colors.HexColor("#111827")
    blanco = colors.white

    margin = 1.2 * cm
    sidebar_w = 6 * cm
    content_x = margin + sidebar_w + 0.8 * cm
    content_w = W - content_x - margin

    # SIDEBAR
    c.setFillColor(azul_oscuro)
    c.rect(0, 0, sidebar_w + margin, H, stroke=0, fill=1)

    y = H - margin

    # FOTO
    img = _image_reader_from_field(perfil.foto_perfil)
    if img:
        c.saveState()
        p = c.beginPath()
        p.circle(margin + 3 * cm, y - 3 * cm, 2 * cm)
        c.clipPath(p, stroke=0)
        c.drawImage(img, margin + 1 * cm, y - 5 * cm, 4 * cm, 4 * cm, mask="auto")
        c.restoreState()

    y -= 6 * cm

    c.setFillColor(blanco)
    c.setFont(FONT_B, 14)
    c.drawCentredString(margin + 3 * cm, y, f"{perfil.nombres} {perfil.apellidos}")

    yR = H - margin

    def titulo(txt):
        nonlocal yR
        c.setFillColor(negro)
        c.setFont(FONT_B, 13)
        c.drawString(content_x, yR, txt)
        yR -= 0.6 * cm

    def item(t, sub, desc):
        nonlocal yR
        c.setFont(FONT_B, 11)
        c.drawString(content_x, yR, t)
        yR -= 0.4 * cm

        if sub:
            c.setFont(FONT, 9)
            c.setFillColor(gris)
            yR = _draw_wrapped(c, sub, content_x, yR, content_w, FONT, 9, 12)
        if desc:
            yR -= 0.1 * cm
            yR = _draw_wrapped(c, desc, content_x, yR, content_w, FONT, 9, 12)
        yR -= 0.6 * cm
        c.setFillColor(negro)

    # RESUMEN
    titulo("RESUMEN PROFESIONAL")
    item("", "", perfil.descripcionperfil or " ")

    # EXPERIENCIA
    for e in perfil.experiencias.filter(activarparaqueseveaenfront=True):
        titulo("EXPERIENCIA LABORAL")
        item(f"{e.cargodesempenado} — {e.nombrempresa}",
             f"{e.fechainicio} → {e.fechafin}",
             e.responsabilidades or e.descripcionfunciones)

    # CURSOS
    for c_ in perfil.cursos.filter(activarparaqueseveaenfront=True):
        titulo("CURSOS / FORMACIÓN")
        item(c_.nombrecurso,
             f"{c_.fechainicio} → {c_.fechafin} | {c_.entidadpatrocinadora}",
             c_.descripcioncurso)

    # RECONOCIMIENTOS
    for r in perfil.reconocimientos.filter(activarparaqueseveaenfront=True):
        titulo("RECONOCIMIENTOS")
        item(r.tiporeconocimiento,
             r.entidadpatrocinadora,
             r.descripcionreconocimiento)

    c.showPage()
    c.save()
    return response


# =========================
# PDF CERTIFICADO (CLOUDINARY)
# =========================
def ver_certificado_pdf(request, curso_id):
    curso = get_object_or_404(Cursosrealizados, idcursorealizado=curso_id)

    if not curso.certificado_pdf:
        raise Http404("Archivo no encontrado")

    # REDIRECT a Cloudinary
    return redirect(curso.certificado_pdf.url)
