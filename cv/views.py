# cv/views.py
import io
import requests

from django.http import HttpResponse, HttpResponseForbidden, Http404
from django.shortcuts import render, get_object_or_404, redirect

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader, simpleSplit


from django.template.loader import render_to_string
from weasyprint import HTML
from django.conf import settings



# ✅ Para unir PDFs reales al final (tamaño original)
from PyPDF2 import PdfReader, PdfWriter

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
            resp = requests.get(image_field.url, timeout=20)
            resp.raise_for_status()
            return ImageReader(io.BytesIO(resp.content))
        image_field.open("rb")
        return ImageReader(io.BytesIO(image_field.read()))
    except Exception:
        return None
    finally:
        try:
            image_field.close()
        except Exception:
            pass


def _read_pdf_bytes(file_field):
    """Lee un FileField PDF (Cloudinary o local) y devuelve bytes."""
    if not file_field:
        return None
    try:
        # Cloud/remote
        if hasattr(file_field, "url"):
            resp = requests.get(file_field.url, timeout=25)
            resp.raise_for_status()
            return resp.content
        # Local
        file_field.open("rb")
        return file_field.read()
    except Exception:
        return None
    finally:
        try:
            file_field.close()
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


def _draw_image_if_exists(c, image_field, x, y, w=5*cm, h=3.2*cm):
    img = _image_reader_from_field(image_field)
    if img:
        c.drawImage(img, x, y - h, w, h, preserveAspectRatio=True, mask="auto")
        return y - h - 0.35 * cm
    return y


def _collect_pdfs(perfil, show):
    """
    Devuelve lista de bytes de PDFs, SOLO de secciones marcadas (A).
    show: dict con flags booleans.
    """
    pdfs = []

    def add_pdf(field):
        b = _read_pdf_bytes(field)
        if b:
            pdfs.append(b)

    if show.get("cursos"):
        for x in perfil.cursos.filter(activarparaqueseveaenfront=True):
            if x.certificado_pdf:
                add_pdf(x.certificado_pdf)

    if show.get("exp"):
        for x in perfil.experiencias.filter(activarparaqueseveaenfront=True):
            if x.certificado_pdf:
                add_pdf(x.certificado_pdf)

    if show.get("reconoc"):
        for x in perfil.reconocimientos.filter(activarparaqueseveaenfront=True):
            if x.certificado_pdf:
                add_pdf(x.certificado_pdf)

    if show.get("prod_acad"):
        for x in perfil.productos_academicos.filter(activarparaqueseveaenfront=True):
            if x.certificado_pdf:
                add_pdf(x.certificado_pdf)

    if show.get("prod_lab"):
        for x in perfil.productos_laborales.filter(activarparaqueseveaenfront=True):
            if x.certificado_pdf:
                add_pdf(x.certificado_pdf)

    # Ventagarage no tiene certificado_pdf en tu modelo (solo foto_producto)
    return pdfs


def _merge_pdfs(base_pdf_bytes, attachments_bytes_list):
    """Une: CV base + (PDFs adjuntos) como páginas reales."""
    writer = PdfWriter()

    base_reader = PdfReader(io.BytesIO(base_pdf_bytes))
    for p in base_reader.pages:
        writer.add_page(p)

    for pdf_bytes in attachments_bytes_list:
        try:
            r = PdfReader(io.BytesIO(pdf_bytes))
            for p in r.pages:
                writer.add_page(p)
        except Exception:
            # Si un PDF está corrupto o no descargó bien, lo saltamos
            continue

    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


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
# PDF FINAL DEL CV + ADJUNTOS REALES
# =========================
def imprimir_hoja_vida(request):
    perfil = _get_perfil_activo()
    if not perfil or not perfil.permitir_impresion:
        return HttpResponseForbidden()

    qs = request.GET
    show = {
        "exp": "exp" in qs or not qs,
        "cursos": "cursos" in qs or not qs,
        "reconoc": "reconoc" in qs or not qs,
        "prod_acad": "prod_acad" in qs or not qs,
        "prod_lab": "prod_lab" in qs or not qs,
    }

    # 🔹 Renderiza el NUEVO HTML del CV
 html = render_to_string("pdf/cv.html", {
    "perfil": perfil,
    "show": show,
})

    # 🔹 Genera el PDF base (CV)
    base_pdf = HTML(
        string=html,
        base_url=request.build_absolute_uri()
    ).write_pdf()

    # 🔹 Recolecta PDFs adjuntos reales según secciones visibles
    attachments = _collect_pdfs(perfil, show)

    # 🔹 Une CV + adjuntos (si existen)
    if attachments:
        final_pdf = _merge_pdfs(base_pdf, attachments)
    else:
        final_pdf = base_pdf

    response = HttpResponse(final_pdf, content_type="application/pdf")
    response["Content-Disposition"] = 'inline; filename="hoja_de_vida.pdf"'
    return response

    pdf = HTML(string=html, base_url=request.build_absolute_uri()).write_pdf()

    # ⬇️ aquí luego vuelves a unir los PDFs adjuntos (ya lo tienes hecho)
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = 'inline; filename="hoja_de_vida.pdf"'
    return response
# =========================
# VISOR PDF INDIVIDUAL
# =========================
def ver_certificado_pdf(request, tipo, obj_id):
    MAP = {
        "curso": (Cursosrealizados, "idcursorealizado"),
        "experiencia": (Experiencialaboral, "idexperiencialaboral"),
        "reconocimiento": (Reconocimientos, "idreconocimiento"),
        "prod_acad": (Productosacademicos, "idproductoacademico"),
        "prod_lab": (Productoslaborales, "idproductolaboral"),
    }

    if tipo not in MAP:
        raise Http404("Tipo de certificado inválido")

    model, field = MAP[tipo]

    obj = get_object_or_404(model, **{field: obj_id})

    if not getattr(obj, "certificado_pdf", None):
        raise Http404("Este registro no tiene PDF")

    return redirect(obj.certificado_pdf.url)

