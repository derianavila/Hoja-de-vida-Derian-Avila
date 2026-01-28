import io
import os

from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader, simpleSplit

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

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
# Helpers
# =========================
def _get_perfil_activo():
    # SOLO perfil activo. Si no hay, devuelve None (y el front no debe mostrar nada).
    return Datospersonales.objects.filter(perfilactivo=True).order_by("-idperfil").first()


def _image_reader_from_field(image_field):
    image_field.open("rb")
    try:
        data = image_field.read()
    finally:
        try:
            image_field.close()
        except Exception:
            pass
    return ImageReader(io.BytesIO(data))


def _register_pretty_fonts():
    font_regular = "Helvetica"
    font_bold = "Helvetica-Bold"

    candidates = [
        (r"C:\Windows\Fonts\segoeui.ttf", r"C:\Windows\Fonts\segoeuib.ttf", "SegoeUI", "SegoeUI-Bold"),
        (r"C:\Windows\Fonts\calibri.ttf", r"C:\Windows\Fonts\calibrib.ttf", "Calibri", "Calibri-Bold"),
    ]
    for reg_path, bold_path, reg_name, bold_name in candidates:
        try:
            if os.path.exists(reg_path) and os.path.exists(bold_path):
                pdfmetrics.registerFont(TTFont(reg_name, reg_path))
                pdfmetrics.registerFont(TTFont(bold_name, bold_path))
                font_regular = reg_name
                font_bold = bold_name
                break
        except Exception:
            continue

    return font_regular, font_bold


def _clean(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value)


def _draw_wrapped(c, text, x, y, max_width, font_name, font_size, leading):
    if not text or not str(text).strip():
        return y
    lines = simpleSplit(str(text), font_name, font_size, max_width)
    for ln in lines:
        c.drawString(x, y, ln)
        y -= leading
    return y


def _pairs_from_fields(pairs):
    out = []
    for label, val in pairs:
        val = _clean(val)
        if val:
            out.append((label, val))
    return out


def _collect_images(perfil, cursos, experiencias, prod_acad, prod_lab, reconoc):
    """
    certificados: imágenes tipo certificado (una por hoja)
    normales: imágenes tipo "foto del producto" (en grid)
    """
    certificados = []
    normales = []

    def add_cert(section, label, field):
        if field and getattr(field, "name", None):
            certificados.append({"section": section, "label": label, "field": field})

    def add_normal(section, label, field, kind="Imagen"):
        if field and getattr(field, "name", None):
            normales.append({"section": section, "label": f"{label} — {kind}", "field": field})

    for c_ in cursos:
        base = f'Curso "{c_.nombrecurso or "Sin título"}"'
        add_cert("Cursos", base, c_.certificado_imagen)

    for e in experiencias:
        cargo = e.cargodesempenado or "Sin título"
        emp = f" - {e.nombrempresa}" if e.nombrempresa else ""
        base = f'Experiencia "{cargo}{emp}"'
        add_cert("Experiencia laboral", base, e.certificado_imagen)

    for p in prod_acad:
        base = f'Producto académico "{p.nombreproducto or "Sin título"}"'
        add_normal("Productos académicos", base, p.imagenproducto, "Imagen del producto")
        add_cert("Productos académicos", base, p.certificado_imagen)

    for p in prod_lab:
        base = f'Producto laboral "{p.nombreproducto or "Sin título"}"'
        add_normal("Productos laborales", base, p.imagenproducto, "Imagen del producto")
        add_cert("Productos laborales", base, p.certificado_imagen)

    # ✅ FIX: en tu modelo el campo es entidadpatrocinadora
    for r in reconoc:
        tipo = r.tiporeconocimiento or "Reconocimiento"
        ent = f" - {r.entidadpatrocinadora}" if r.entidadpatrocinadora else ""
        base = f'Reconocimiento "{tipo}{ent}"'
        add_cert("Reconocimientos", base, r.certificado_imagen)

    return certificados, normales


# =========================
# Views web
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
    items = (
        perfil.cursos
        .filter(activarparaqueseveaenfront=True)
        .order_by("-fechafin", "-fechainicio", "-idcursorealizado")
        if perfil else []
    )
    return render(request, "secciones/cursos.html", {"perfil": perfil, "items": items})


def experiencia(request):
    perfil = _get_perfil_activo()
    items = (
        perfil.experiencias
        .filter(activarparaqueseveaenfront=True)
        .order_by("-fechafin", "-fechainicio", "-idexperiencialaboral")
        if perfil else []
    )
    return render(request, "secciones/experiencia.html", {"perfil": perfil, "items": items})


def productos_academicos(request):
    perfil = _get_perfil_activo()
    items = (
        perfil.productos_academicos
        .filter(activarparaqueseveaenfront=True)
        .order_by("-idproductoacademico")
        if perfil else []
    )
    return render(request, "secciones/productos_academicos.html", {"perfil": perfil, "items": items})


def productos_laborales(request):
    perfil = _get_perfil_activo()
    items = (
        perfil.productos_laborales
        .filter(activarparaqueseveaenfront=True)
        .order_by("-fechaproducto", "-idproductolaboral")
        if perfil else []
    )
    return render(request, "secciones/productos_laborales.html", {"perfil": perfil, "items": items})


def reconocimientos(request):
    perfil = _get_perfil_activo()
    items = (
        perfil.reconocimientos
        .filter(activarparaqueseveaenfront=True)
        .order_by("-fechareconocimiento", "-idreconocimiento")
        if perfil else []
    )
    return render(request, "secciones/reconocimientos.html", {"perfil": perfil, "items": items})


def venta_garage(request):
    perfil = _get_perfil_activo()
    items = (
        perfil.venta_garage
        .filter(activarparaqueseveaenfront=True)
        .order_by("-fecha", "-idventagarage")
        if perfil else []
    )
    return render(request, "secciones/venta_garage.html", {"perfil": perfil, "items": items})


# =========================
# PDF (ReportLab)
# =========================
def imprimir_hoja_vida(request):
    perfil = _get_perfil_activo()

    if not perfil:
        return HttpResponse("Perfil no encontrado", status=404)

    if not perfil.permitir_impresion:
        return HttpResponseForbidden("No autorizado", status=403)

    # =============================
    # Selección por parámetros
    # =============================
    keys = ["exp", "cursos", "reconoc", "prod_acad", "prod_lab", "venta"]
    has_any_param = any(k in request.GET for k in keys)

    def on(q):
        if not has_any_param:
            return True
        return request.GET.get(q) == "1"

    exp_qs = list(
        perfil.experiencias
        .filter(activarparaqueseveaenfront=True)
        .order_by("-fechafin", "-fechainicio")
    ) if on("exp") else []

    cursos_qs = list(
        perfil.cursos
        .filter(activarparaqueseveaenfront=True)
        .order_by("-fechafin", "-fechainicio")
    ) if on("cursos") else []

    rec_qs = list(
        perfil.reconocimientos
        .filter(activarparaqueseveaenfront=True)
        .order_by("-fechareconocimiento")
    ) if on("reconoc") else []

    pa_qs = list(
        perfil.productos_academicos
        .filter(activarparaqueseveaenfront=True)
    ) if on("prod_acad") else []

    pl_qs = list(
        perfil.productos_laborales
        .filter(activarparaqueseveaenfront=True)
    ) if on("prod_lab") else []

    vg_qs = list(
        perfil.venta_garage
        .filter(activarparaqueseveaenfront=True)
    ) if on("venta") else []

    FONT, FONT_B = _register_pretty_fonts()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'inline; filename="hoja_de_vida.pdf"'

    c = canvas.Canvas(response, pagesize=A4)
    W, H = A4

    # =============================
    # COLORES
    # =============================
    azul_oscuro = colors.HexColor("#1f2a33")
    azul = colors.HexColor("#2f3e4e")
    gris = colors.HexColor("#6b7280")
    negro = colors.HexColor("#111827")
    blanco = colors.white

    margin = 1.2 * cm
    sidebar_w = 6.0 * cm
    content_x = margin + sidebar_w + 0.8 * cm
    content_w = W - content_x - margin

    # =============================
    # SIDEBAR
    # =============================
    c.setFillColor(azul_oscuro)
    c.rect(0, 0, sidebar_w + margin, H, stroke=0, fill=1)

    y = H - margin

    # Foto
    if perfil.foto_perfil:
        try:
            img = _image_reader_from_field(perfil.foto_perfil)
            c.saveState()
            p = c.beginPath()
            p.circle(margin + 3 * cm, y - 3 * cm, 2 * cm)
            c.clipPath(p, stroke=0)
            c.drawImage(img, margin + 1 * cm, y - 5 * cm, 4 * cm, 4 * cm, mask="auto")
            c.restoreState()
        except Exception:
            pass

    y -= 6 * cm

    # Nombre
    c.setFillColor(blanco)
    c.setFont(FONT_B, 14)
    c.drawCentredString(margin + 3 * cm, y, f"{perfil.nombres} {perfil.apellidos}")

    y -= 1 * cm

    # Datos personales
    c.setFont(FONT, 9)
    datos = [
        perfil.nacionalidad,
        perfil.lugarnacimiento,
        f"Licencia: {perfil.licenciaconducir}" if perfil.licenciaconducir else "",
        perfil.telefonofijo,
        perfil.sitioweb,
    ]
    for d in datos:
        if d:
            c.drawCentredString(margin + 3 * cm, y, str(d))
            y -= 0.5 * cm

    # =============================
    # CONTENIDO
    # =============================
    yR = H - margin

    def titulo(txt):
        nonlocal yR
        c.setFillColor(negro)
        c.setFont(FONT_B, 13)
        c.drawString(content_x, yR, txt)
        yR -= 0.6 * cm

    def item(titulo_txt, subtitulo, desc):
        nonlocal yR
        c.setFont(FONT_B, 11)
        c.drawString(content_x, yR, titulo_txt)
        yR -= 0.4 * cm

        if subtitulo:
            c.setFont(FONT, 9)
            c.setFillColor(gris)
            yR = _draw_wrapped(c, subtitulo, content_x, yR, content_w, FONT, 9, 12)

        if desc:
            yR -= 0.1 * cm
            yR = _draw_wrapped(c, desc, content_x, yR, content_w, FONT, 9, 12)

        yR -= 0.6 * cm
        c.setFillColor(negro)

    # =============================
    # RESUMEN
    # =============================
    resumen = perfil.descripcionperfil or (
        f"{perfil.nombres} {perfil.apellidos}. "
        f"De {perfil.lugarnacimiento}, {perfil.nacionalidad}."
    )

    titulo("RESUMEN PROFESIONAL")
    item("", "", resumen)

    # =============================
    # EXPERIENCIA
    # =============================
    if exp_qs:
        titulo("EXPERIENCIA LABORAL")
        for e in exp_qs:
            item(
                f"{e.cargodesempenado} — {e.nombrempresa}",
                f"{e.fechainicio} → {e.fechafin}",
                e.responsabilidades or e.descripcionfunciones
            )

    # =============================
    # CURSOS
    # =============================
    if cursos_qs:
        titulo("CURSOS / FORMACIÓN")
        for c_ in cursos_qs:
            item(
                c_.nombrecurso,
                f"{c_.fechainicio} → {c_.fechafin} | {c_.entidadpatrocinadora}",
                c_.descripcioncurso
            )

    # =============================
    # RECONOCIMIENTOS
    # =============================
    if rec_qs:
        titulo("RECONOCIMIENTOS")
        for r in rec_qs:
            item(
                r.tiporeconocimiento,
                r.entidadpatrocinadora,
                r.descripcionreconocimiento
            )

    c.showPage()
    c.save()
    return response
