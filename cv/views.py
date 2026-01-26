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
    # no tiene fecha, lo dejamos por id
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

    # ✅ Orden por fecha en todas las secciones (más reciente -> más antigua)
    cursos_qs = list(
        perfil.cursos
        .filter(activarparaqueseveaenfront=True)
        .order_by("-fechafin", "-fechainicio", "-idcursorealizado")
    )
    exp_qs = list(
        perfil.experiencias
        .filter(activarparaqueseveaenfront=True)
        .order_by("-fechafin", "-fechainicio", "-idexperiencialaboral")
    )
    rec_qs = list(
        perfil.reconocimientos
        .filter(activarparaqueseveaenfront=True)
        .order_by("-fechareconocimiento", "-idreconocimiento")
    )
    pa_qs = list(
        perfil.productos_academicos
        .filter(activarparaqueseveaenfront=True)
        .order_by("-idproductoacademico")
    )
    pl_qs = list(
        perfil.productos_laborales
        .filter(activarparaqueseveaenfront=True)
        .order_by("-fechaproducto", "-idproductolaboral")
    )
    vg_qs = list(
        perfil.venta_garage
        .filter(activarparaqueseveaenfront=True)
        .order_by("-fecha", "-idventagarage")
    )

    cert_imgs, normal_imgs = _collect_images(perfil, cursos_qs, exp_qs, pa_qs, pl_qs, rec_qs)

    FONT, FONT_B = _register_pretty_fonts()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'inline; filename="hoja_de_vida.pdf"'

    c = canvas.Canvas(response, pagesize=A4)
    W, H = A4

    # Colores
    navy = colors.HexColor("#0b2a57")
    navy2 = colors.HexColor("#0a2347")
    white = colors.white
    text = colors.HexColor("#0f172a")
    muted = colors.HexColor("#475569")
    border = colors.HexColor("#dbe4f5")
    chip = colors.HexColor("#e9f0ff")

    # Layout
    margin = 1.2 * cm
    sidebar_w = 5.7 * cm
    gap = 0.8 * cm

    sidebar_w_total = margin + sidebar_w + gap / 2
    content_x = margin + sidebar_w + gap
    content_w = W - content_x - margin

    lead_small = 12.5

    def draw_sidebar_background():
        c.setFillColor(navy)
        c.rect(0, 0, sidebar_w_total, H, stroke=0, fill=1)

    def draw_circle_image(image_reader, cx, cy, r):
        c.saveState()
        p = c.beginPath()
        p.circle(cx, cy, r)
        c.clipPath(p, stroke=0, fill=0)
        c.drawImage(image_reader, cx - r, cy - r, width=2 * r, height=2 * r, preserveAspectRatio=True, mask="auto")
        c.restoreState()

    def hr_sidebar(y):
        c.setStrokeColor(colors.HexColor("#2a4a7d"))
        c.setLineWidth(1)
        c.line(margin, y, margin + sidebar_w - 0.2 * cm, y)

    def draw_sidebar_content():
        top_y = H - margin - 0.4 * cm

        if perfil.foto_perfil and getattr(perfil.foto_perfil, "name", None):
            try:
                img_reader = _image_reader_from_field(perfil.foto_perfil)
                draw_circle_image(img_reader, margin + 2.0 * cm, top_y - 1.85 * cm, 1.55 * cm)
            except Exception:
                pass

        nombre = f"{(perfil.nombres or '').strip()} {(perfil.apellidos or '').strip()}".strip() or "Perfil"
        c.setFillColor(white)
        c.setFont(FONT_B, 14.2)
        c.drawString(margin, top_y - 4.05 * cm, nombre[:28])

        desc_local = _clean(perfil.descripcionperfil)
        if desc_local:
            c.setFillColor(colors.HexColor("#d7e6ff"))
            c.setFont(FONT, 9.6)
            _draw_wrapped(c, desc_local, margin, top_y - 4.65 * cm, sidebar_w - 0.2 * cm, FONT, 9.6, 12)

        yL = top_y - 5.9 * cm
        hr_sidebar(yL + 0.45 * cm)
        c.setFillColor(colors.HexColor("#d7e6ff"))
        c.setFont(FONT_B, 10)
        c.drawString(margin, yL, "DATOS PERSONALES")
        yL -= 0.65 * cm

        dp_pairs = _pairs_from_fields([
            ("Cédula", perfil.numerocedula),
            ("Sexo", perfil.sexo),
            ("Estado civil", perfil.estadocivil),
            ("Fecha nac.", perfil.fechanacimiento),
            ("Nacionalidad", perfil.nacionalidad),
            ("Lugar nac.", perfil.lugarnacimiento),
            ("Licencia", perfil.licenciaconducir),
            ("Teléfono", perfil.telefonofijo),
            ("Convencional", perfil.telefonoconvencional),
            ("Dirección dom.", perfil.direcciondomiciliaria),
            ("Dirección trab.", perfil.direcciontrabajo),
            ("Sitio web", perfil.sitioweb),
        ])

        for label, val in dp_pairs:
            c.setFillColor(colors.HexColor("#d7e6ff"))
            c.setFont(FONT_B, 9.1)
            c.drawString(margin, yL, f"{label}:")
            yL -= 0.35 * cm
            c.setFillColor(white)
            c.setFont(FONT, 9.5)
            yL = _draw_wrapped(c, val, margin, yL, sidebar_w - 0.2 * cm, FONT, 9.5, 11.5)
            yL -= 0.2 * cm
            if yL < 1.6 * cm:
                break

    def new_page(with_sidebar=True):
        c.showPage()
        if with_sidebar:
            draw_sidebar_background()
            draw_sidebar_content()

    def content_title(y, s):
        c.setFillColor(text)
        c.setFont(FONT_B, 13.8)
        c.drawString(content_x, y, s)
        c.setStrokeColor(border)
        c.setLineWidth(1)
        c.line(content_x, y - 0.25 * cm, content_x + content_w, y - 0.25 * cm)
        return y - 0.85 * cm

    def content_card(y, title_s, pairs, notes=None):
        pairs = _pairs_from_fields(pairs)
        notes = _clean(notes)

        if not pairs and not notes:
            return y

        if y < 4.0 * cm:
            new_page(with_sidebar=True)
            y = H - margin - 0.6 * cm

        inner_x = content_x
        inner_w = content_w

        c.setFillColor(navy2)
        c.setFont(FONT_B, 11.6)
        c.drawString(inner_x, y - 0.2 * cm, (title_s or "")[:92])

        yy = y - 0.75 * cm

        for label, val in pairs:
            c.setFillColor(text)
            c.setFont(FONT_B, 9.8)
            c.drawString(inner_x, yy, f"{label}:")
            c.setFillColor(muted)
            c.setFont(FONT, 9.8)
            yy = _draw_wrapped(c, val, inner_x + 3.25 * cm, yy, inner_w - 3.25 * cm, FONT, 9.8, lead_small)
            yy -= 2

            if yy < 2.2 * cm:
                new_page(with_sidebar=True)
                y = H - margin - 0.6 * cm
                yy = y - 0.9 * cm

        if notes:
            yy -= 6
            c.setFillColor(text)
            c.setFont(FONT_B, 9.8)
            c.drawString(inner_x, yy, "Descripción:")
            yy -= lead_small
            c.setFillColor(muted)
            c.setFont(FONT, 9.8)
            yy = _draw_wrapped(c, notes, inner_x, yy, inner_w, FONT, 9.8, lead_small)

        yy -= 0.25 * cm
        c.setStrokeColor(border)
        c.setLineWidth(0.7)
        c.line(content_x, yy, content_x + content_w, yy)

        return yy - 0.45 * cm

    # ========== Página CV ==========
    draw_sidebar_background()
    draw_sidebar_content()

    desc = _clean(perfil.descripcionperfil)
    yR = H - margin - 0.6 * cm

    if desc:
        yR = content_title(yR, "Perfil profesional")
        yR = content_card(yR, "Resumen", [], desc)
        yR -= 0.2 * cm

    def section(title_name, items, draw_item):
        nonlocal yR
        if not items:
            return

        if yR < 4.0 * cm:
            new_page(with_sidebar=True)
            yR = H - margin - 0.6 * cm

        yR = content_title(yR, title_name)

        for it in items:
            if yR < 3.2 * cm:
                new_page(with_sidebar=True)
                yR = H - margin - 0.6 * cm
                yR = content_title(yR, title_name)

            yR = draw_item(it)
            yR -= 0.10 * cm

        yR -= 0.25 * cm

    section("Experiencia laboral", exp_qs, lambda it: content_card(
        yR,
        ((it.cargodesempenado or "Experiencia") + (f" — {it.nombrempresa}" if it.nombrempresa else "")).strip(),
        [
            ("Inicio", it.fechainicio),
            ("Fin", it.fechafin),
            ("Lugar", it.lugarempresa),
            ("Dirección", it.direccionempresa),
            ("Sitio web", it.sitiowebempresa),
            ("Email", it.emailempresa),
            ("Teléfono", it.telefonoempresa),
            ("Contacto", it.nombrecontactoempresarial),
            ("Tel. contacto", it.telefonocontactoempresarial),
            ("Funciones", it.descripcionfunciones),
        ],
        it.responsabilidades
    ))

    section("Cursos realizados", cursos_qs, lambda it: content_card(
        yR,
        it.nombrecurso or "Curso",
        [
            ("Inicio", it.fechainicio),
            ("Fin", it.fechafin),
            ("Total horas", it.totalhoras),
            ("Entidad", it.entidadpatrocinadora),
            ("Contacto", it.nombrecontactoauspicia),
            ("Tel. contacto", it.telefonocontactoauspicia),
            ("Email entidad", it.emailempresapatrocinadora),
        ],
        it.descripcioncurso
    ))

    section("Productos académicos", pa_qs, lambda it: content_card(
        yR,
        it.nombreproducto or "Producto académico",
        [("Clasificador", it.clasificador)],
        it.descripcion
    ))

    section("Productos laborales", pl_qs, lambda it: content_card(
        yR,
        it.nombreproducto or "Producto laboral",
        [("Fecha", it.fechaproducto)],
        it.descripcion
    ))

    section("Reconocimientos", rec_qs, lambda it: content_card(
        yR,
        ((it.tiporeconocimiento or "Reconocimiento") + (f" — {it.entidadpatrocinadora}" if it.entidadpatrocinadora else "")).strip(),
        [
            ("Fecha", it.fechareconocimiento),
            ("Tipo", it.tiporeconocimiento),
            ("Entidad", it.entidadpatrocinadora),
        ],
        it.descripcionreconocimiento
    ))

    section("Venta garage", vg_qs, lambda it: content_card(
        yR,
        it.nombreproducto or "Producto",
        [
            ("Fecha", it.fecha),
            ("Estado", it.estadoproducto),
            ("Valor", f"${it.valordelbien}" if it.valordelbien is not None else ""),
        ],
        it.descripcion
    ))

    # ========== Certificados full page - sin sidebar ==========
    if cert_imgs:
        for ev in cert_imgs:
            new_page(with_sidebar=False)

            c.setFillColor(navy2)
            c.rect(0, H - 2.0 * cm, W, 2.0 * cm, stroke=0, fill=1)
            c.setFillColor(white)
            c.setFont(FONT_B, 13.5)
            c.drawString(margin, H - 1.3 * cm, f'{ev["section"]} | {ev["label"]}'[:100])

            top = H - 2.35 * cm
            bottom = margin
            left = margin
            right = W - margin
            box_w = right - left
            box_h = top - bottom

            c.setFillColor(colors.white)
            c.setStrokeColor(border)
            c.roundRect(left, bottom, box_w, box_h, 10, stroke=1, fill=1)

            try:
                img_reader = _image_reader_from_field(ev["field"])
                c.drawImage(
                    img_reader,
                    left + 0.25 * cm,
                    bottom + 0.25 * cm,
                    width=box_w - 0.5 * cm,
                    height=box_h - 0.5 * cm,
                    preserveAspectRatio=True,
                    anchor="c",
                    mask="auto"
                )
            except Exception:
                c.setFillColor(colors.red)
                c.setFont(FONT, 11)
                c.drawString(left + 0.6 * cm, top - 1.0 * cm, "No se pudo cargar la imagen del certificado.")

    # ========== Imágenes normales grid (al final) - sin sidebar ==========
    if normal_imgs:
        new_page(with_sidebar=False)

        c.setFillColor(navy2)
        c.rect(0, H - 2.0 * cm, W, 2.0 * cm, stroke=0, fill=1)
        c.setFillColor(white)
        c.setFont(FONT_B, 16)
        c.drawString(margin, H - 1.3 * cm, "Imágenes")

        y_ev = H - 2.55 * cm

        col_w = (W - 2 * margin - 0.55 * cm) / 2
        img_h = 6.0 * cm
        caption_h = 1.05 * cm
        block_h = img_h + caption_h + 0.5 * cm

        x1 = margin
        x2 = margin + col_w + 0.55 * cm

        i = 0
        while i < len(normal_imgs):
            if y_ev - block_h < 1.6 * cm:
                new_page(with_sidebar=False)
                y_ev = H - margin

            for x in (x1, x2):
                if i >= len(normal_imgs):
                    break
                ev = normal_imgs[i]
                i += 1

                c.setStrokeColor(border)
                c.setFillColor(colors.white)
                c.roundRect(x, y_ev - img_h, col_w, img_h, 10, stroke=1, fill=1)

                try:
                    img_reader = _image_reader_from_field(ev["field"])
                    c.drawImage(
                        img_reader,
                        x + 0.2 * cm, y_ev - img_h + 0.2 * cm,
                        width=col_w - 0.4 * cm, height=img_h - 0.4 * cm,
                        preserveAspectRatio=True,
                        anchor="sw",
                        mask="auto"
                    )
                except Exception:
                    c.setFillColor(colors.red)
                    c.setFont(FONT, 9.5)
                    c.drawString(x + 0.25 * cm, y_ev - 0.7 * cm, "No se pudo cargar la imagen.")

                c.setFillColor(chip)
                c.setStrokeColor(border)
                c.roundRect(x, y_ev - img_h - caption_h, col_w, caption_h, 9, stroke=1, fill=1)

                c.setFillColor(navy)
                c.setFont(FONT_B, 9.2)
                c.drawString(x + 0.25 * cm, y_ev - img_h - 0.5 * cm, (ev["section"] or "")[:30])

                c.setFillColor(text)
                c.setFont(FONT, 9.1)
                cap_y = y_ev - img_h - 0.83 * cm
                _draw_wrapped(c, ev["label"] or "", x + 2.1 * cm, cap_y, col_w - 2.35 * cm, FONT, 9.1, 11.0)

            y_ev -= block_h

    c.showPage()
    c.save()
    return response
