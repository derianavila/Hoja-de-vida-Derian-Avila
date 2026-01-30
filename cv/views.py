# cv/views.py
import io
import requests

from django.http import HttpResponse, HttpResponseForbidden, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.conf import settings

from weasyprint import HTML

# ✅ Para unir PDFs reales al final
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


def _read_pdf_bytes(file_field):
    if not file_field:
        return None
    try:
        if hasattr(file_field, "url"):
            resp = requests.get(file_field.url, timeout=25)
            resp.raise_for_status()
            return resp.content
        file_field.open("rb")
        return file_field.read()
    except Exception:
        return None
    finally:
        try:
            file_field.close()
        except Exception:
            pass


def _collect_pdfs(perfil, show):
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

    return pdfs


def _merge_pdfs(base_pdf_bytes, attachments_bytes_list):
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
    items = perfil.cursos.filter(activarparaqueseveaenfront=True) if perfil else []
    return render(request, "secciones/cursos.html", {"perfil": perfil, "items": items})


def experiencia(request):
    perfil = _get_perfil_activo()
    items = perfil.experiencias.filter(activarparaqueseveaenfront=True) if perfil else []
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
# PDF FINAL DEL CV + ADJUNTOS
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

    html = render_to_string(
        "pdf/cv.html",
        {
            "perfil": perfil,
            "show": show,
        }
    )

    base_pdf = HTML(
        string=html,
        base_url=request.build_absolute_uri()
    ).write_pdf()

    attachments = _collect_pdfs(perfil, show)

    final_pdf = _merge_pdfs(base_pdf, attachments) if attachments else base_pdf

    response = HttpResponse(final_pdf, content_type="application/pdf")
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
