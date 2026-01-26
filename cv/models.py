from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import (
    FileExtensionValidator,
    RegexValidator,
    MinValueValidator,
    MaxValueValidator,
    EmailValidator,
)
from django.db import models


# =========================
# VALIDADORES
# =========================
cedula_10_digitos = RegexValidator(
    regex=r"^\d{10}$",
    message="La cédula debe tener exactamente 10 dígitos.",
)

telefono_basico = RegexValidator(
    regex=r"^[0-9+\-\s()]{7,20}$",
    message="Teléfono inválido (solo números y símbolos básicos).",
)

# ✅ NUEVO: solo letras (incluye tildes/ñ) y espacios
solo_letras_espacios = RegexValidator(
    regex=r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ\s]+$",
    message="Solo se permiten letras y espacios.",
)


def validar_fecha_desde_2000(value):
    if value and value.year < 2000:
        raise ValidationError("La fecha debe ser desde el año 2000 en adelante.")


def validar_fecha_no_futura(value):
    if value and value > date.today():
        raise ValidationError("La fecha no puede ser mayor a la fecha actual.")


def validar_pdf(archivo):
    if archivo and not archivo.name.lower().endswith(".pdf"):
        raise ValidationError("Solo se permiten archivos PDF.")


def validar_rango_inicio_fin(inicio, fin, field_fin="fechafin"):
    if inicio and fin and fin < inicio:
        raise ValidationError({field_fin: "La fecha fin no puede ser menor que la fecha inicio."})


def validar_no_antes_de_nacimiento(perfil, fecha, field_name):
    """
    Evita fechas anteriores a la fecha de nacimiento del perfil.
    """
    if fecha and perfil and perfil.fechanacimiento and fecha < perfil.fechanacimiento:
        raise ValidationError({field_name: "La fecha no puede ser anterior a tu fecha de nacimiento."})


def validar_inicio_fin_obligatorios_juntos(inicio, fin, field_inicio="fechainicio", field_fin="fechafin"):
    """
    Si hay inicio debe haber fin y viceversa.
    """
    if inicio and not fin:
        raise ValidationError({field_fin: "Si ingresas fecha de inicio, también debes ingresar fecha de fin."})
    if fin and not inicio:
        raise ValidationError({field_inicio: "Si ingresas fecha de fin, también debes ingresar fecha de inicio."})


# =========================
# CHOICES
# =========================
CLASIFICADOR_ACADEMICO_CHOICES = [
    ("ARTICULO", "Artículo"),
    ("TESIS", "Tesis"),
    ("INVESTIGACION", "Investigación"),
    ("PROYECTO", "Proyecto"),
    ("PONENCIA", "Ponencia"),
    ("POSTER", "Póster"),
    ("LIBRO", "Libro / Capítulo"),
    ("ENSAYO", "Ensayo"),
    ("INFORME", "Informe"),
    ("OTRO", "Otro"),
]


# =========================
# DATOS PERSONALES
# =========================
class Datospersonales(models.Model):
    SEXO_CHOICES = [
        ("H", "H"),
        ("M", "M"),
    ]

    ESTADO_CIVIL_CHOICES = [
        ("SOLTERO", "Soltero/a"),
        ("CASADO", "Casado/a"),
        ("DIVORCIADO", "Divorciado/a"),
        ("VIUDO", "Viudo/a"),
        ("UNION_LIBRE", "Unión libre"),
    ]

    LICENCIA_CHOICES = [
        ("A", "Tipo A"),
        ("A1", "Tipo A1"),
        ("B", "Tipo B"),
        ("C", "Tipo C"),
        ("C1", "Tipo C1"),
        ("D", "Tipo D"),
        ("E", "Tipo E"),
        ("F", "Tipo F"),
        ("G", "Tipo G"),
    ]

    idperfil = models.AutoField(primary_key=True)

    descripcionperfil = models.CharField(max_length=200, blank=True, null=True)
    foto_perfil = models.ImageField(upload_to="perfiles/", blank=True, null=True)

    perfilactivo = models.BooleanField(default=False)
    permitir_impresion = models.BooleanField(default=False)

    # ✅ ESTRICTO + SOLO LETRAS/ESPACIOS
    apellidos = models.CharField(max_length=60, blank=False, null=False, validators=[solo_letras_espacios])
    nombres = models.CharField(max_length=60, blank=False, null=False, validators=[solo_letras_espacios])

    nacionalidad = models.CharField(max_length=50, blank=True, null=True)
    lugarnacimiento = models.CharField(max_length=100, blank=True, null=True)

    # ✅ OBLIGATORIA
    fechanacimiento = models.DateField(
        blank=False,
        null=False,
        validators=[validar_fecha_no_futura],
    )

    # ✅ OBLIGATORIA + ÚNICA GLOBAL (NO SE REPITE) + 10 DÍGITOS
    numerocedula = models.CharField(
        unique=True,
        max_length=10,
        blank=False,
        null=False,
        validators=[cedula_10_digitos],
    )

    sexo = models.CharField(max_length=1, blank=True, null=True, choices=SEXO_CHOICES)

    estadocivil = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        choices=ESTADO_CIVIL_CHOICES,
    )

    licenciaconducir = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        choices=LICENCIA_CHOICES,
    )

    telefonoconvencional = models.CharField(max_length=20, blank=True, null=True, validators=[telefono_basico])
    telefonofijo = models.CharField(max_length=20, blank=True, null=True, validators=[telefono_basico])
    direcciontrabajo = models.CharField(max_length=120, blank=True, null=True)
    direcciondomiciliaria = models.CharField(max_length=120, blank=True, null=True)

    # ✅ URL real
    sitioweb = models.URLField(max_length=200, blank=True, null=True)

    class Meta:
        db_table = "DATOSPERSONALES"

    def clean(self):
        super().clean()

        if self.fechanacimiento > date.today():
            raise ValidationError({"fechanacimiento": "La fecha de nacimiento no puede ser futura."})

        edad = date.today().year - self.fechanacimiento.year - (
            (date.today().month, date.today().day) < (self.fechanacimiento.month, self.fechanacimiento.day)
        )

        # ✅ MÍNIMO 18
        if edad < 18:
            raise ValidationError({"fechanacimiento": "Debes tener mínimo 18 años."})

        # ✅ MÁXIMO 65
        if edad > 65:
            raise ValidationError({"fechanacimiento": "La edad no puede ser mayor a 65 años."})

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.perfilactivo:
            Datospersonales.objects.exclude(pk=self.pk).update(perfilactivo=False)

    def __str__(self):
        return f"{self.nombres or ''} {self.apellidos or ''}".strip() or f"Perfil {self.idperfil}"


# =========================
# MIXIN PARA CERTIFICADOS
# =========================
class CertificadoMixin(models.Model):
    certificado_pdf = models.FileField(
        upload_to="certificados/",
        blank=True,
        null=True,
        validators=[validar_pdf, FileExtensionValidator(["pdf"])],
    )
    certificado_imagen = models.ImageField(upload_to="certificados/imagenes/", blank=True, null=True)

    class Meta:
        abstract = True


# =========================
# CURSOS REALIZADOS
# =========================
class Cursosrealizados(CertificadoMixin, models.Model):
    idcursorealizado = models.AutoField(primary_key=True)

    perfil = models.ForeignKey(
        Datospersonales,
        on_delete=models.CASCADE,
        related_name="cursos",
        db_column="idperfilconqueestaactivo",
    )

    # ✅ ESTRICTO
    nombrecurso = models.CharField(max_length=120, blank=False, null=False)

    # ✅ ESTRICTO: inicio y fin obligatorios
    fechainicio = models.DateField(
        blank=False,
        null=False,
        validators=[validar_fecha_desde_2000, validar_fecha_no_futura],
    )
    fechafin = models.DateField(
        blank=False,
        null=False,
        validators=[validar_fecha_desde_2000, validar_fecha_no_futura],
    )

    totalhoras = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(1)])
    descripcioncurso = models.CharField(max_length=200, blank=True, null=True)

    entidadpatrocinadora = models.CharField(max_length=120, blank=True, null=True)
    nombrecontactoauspicia = models.CharField(max_length=120, blank=True, null=True)
    telefonocontactoauspicia = models.CharField(max_length=40, blank=True, null=True, validators=[telefono_basico])
    emailempresapatrocinadora = models.CharField(max_length=120, blank=True, null=True, validators=[EmailValidator()])

    activarparaqueseveaenfront = models.BooleanField(default=True)
    rutacertificado = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        db_table = "CURSOSREALIZADOS"
        constraints = [
            models.UniqueConstraint(
                fields=["perfil", "nombrecurso", "fechainicio", "fechafin"],
                name="uq_curso_perfil_nombre_fechas",
            )
        ]

    def clean(self):
        super().clean()
        validar_inicio_fin_obligatorios_juntos(self.fechainicio, self.fechafin, "fechainicio", "fechafin")
        validar_rango_inicio_fin(self.fechainicio, self.fechafin, "fechafin")
        validar_no_antes_de_nacimiento(self.perfil, self.fechainicio, "fechainicio")
        validar_no_antes_de_nacimiento(self.perfil, self.fechafin, "fechafin")


# =========================
# EXPERIENCIA LABORAL
# =========================
class Experiencialaboral(CertificadoMixin, models.Model):
    idexperiencialaboral = models.AutoField(primary_key=True)

    perfil = models.ForeignKey(
        Datospersonales,
        on_delete=models.CASCADE,
        related_name="experiencias",
        db_column="idperfilconqueestaactivo",
    )

    # ✅ ESTRICTO
    nombrempresa = models.CharField(max_length=120, blank=False, null=False)
    cargodesempenado = models.CharField(max_length=120, blank=False, null=False)

    # ✅ ESTRICTO: inicio y fin obligatorios
    fechainicio = models.DateField(
        blank=False,
        null=False,
        validators=[validar_fecha_desde_2000, validar_fecha_no_futura],
    )
    fechafin = models.DateField(
        blank=False,
        null=False,
        validators=[validar_fecha_desde_2000, validar_fecha_no_futura],
    )

    responsabilidades = models.TextField(blank=True, null=True)
    direccionempresa = models.CharField(max_length=150, blank=True, null=True)
    telefonoempresa = models.CharField(max_length=40, blank=True, null=True, validators=[telefono_basico])
    emailempresa = models.CharField(max_length=120, blank=True, null=True, validators=[EmailValidator()])

    activarparaqueseveaenfront = models.BooleanField(default=True)
    rutacertificado = models.CharField(max_length=200, blank=True, null=True)

    lugarempresa = models.CharField(max_length=50, blank=True, null=True)

    # ✅ URL real
    sitiowebempresa = models.URLField(max_length=200, blank=True, null=True)

    nombrecontactoempresarial = models.CharField(max_length=100, blank=True, null=True)
    telefonocontactoempresarial = models.CharField(max_length=60, blank=True, null=True, validators=[telefono_basico])
    descripcionfunciones = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = "EXPERIENCIALABORAL"
        constraints = [
            models.UniqueConstraint(
                fields=["perfil", "nombrempresa", "cargodesempenado", "fechainicio", "fechafin"],
                name="uq_exp_perfil_empresa_cargo_fechas",
            )
        ]

    def clean(self):
        super().clean()
        validar_inicio_fin_obligatorios_juntos(self.fechainicio, self.fechafin, "fechainicio", "fechafin")
        validar_rango_inicio_fin(self.fechainicio, self.fechafin, "fechafin")
        validar_no_antes_de_nacimiento(self.perfil, self.fechainicio, "fechainicio")
        validar_no_antes_de_nacimiento(self.perfil, self.fechafin, "fechafin")


# =========================
# PRODUCTOS ACADÉMICOS
# =========================
class Productosacademicos(CertificadoMixin, models.Model):
    idproductoacademico = models.AutoField(primary_key=True)

    perfil = models.ForeignKey(
        Datospersonales,
        on_delete=models.CASCADE,
        related_name="productos_academicos",
        db_column="idperfilconqueestaactivo",
    )

    # ✅ ESTRICTO
    nombreproducto = models.CharField(max_length=120, blank=False, null=False)

    # ✅ ESTRICTO
    clasificador = models.CharField(
        max_length=20,
        blank=False,
        null=False,
        choices=CLASIFICADOR_ACADEMICO_CHOICES,
    )

    descripcion = models.TextField(blank=True, null=True)
    activarparaqueseveaenfront = models.BooleanField(default=True)

    imagenproducto = models.ImageField(upload_to="productos/academicos/", blank=True, null=True)
    rutaimagen = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        db_table = "PRODUCTOSACADEMICOS"
        constraints = [
            models.UniqueConstraint(
                fields=["perfil", "nombreproducto", "clasificador"],
                name="uq_prodacad_perfil_nombre_clasif",
            )
        ]


# =========================
# PRODUCTOS LABORALES
# =========================
class Productoslaborales(CertificadoMixin, models.Model):
    idproductolaboral = models.AutoField(primary_key=True)

    perfil = models.ForeignKey(
        Datospersonales,
        on_delete=models.CASCADE,
        related_name="productos_laborales",
        db_column="idperfilconqueestaactivo",
    )

    # ✅ ESTRICTO
    nombreproducto = models.CharField(max_length=120, blank=False, null=False)

    # ✅ ESTRICTO
    fechaproducto = models.DateField(
        blank=False,
        null=False,
        validators=[validar_fecha_desde_2000, validar_fecha_no_futura],
    )

    descripcion = models.TextField(blank=True, null=True)
    activarparaqueseveaenfront = models.BooleanField(default=True)

    imagenproducto = models.ImageField(upload_to="productos/laborales/", blank=True, null=True)
    rutaimagen = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        db_table = "PRODUCTOSLABORALES"
        constraints = [
            models.UniqueConstraint(
                fields=["perfil", "nombreproducto", "fechaproducto"],
                name="uq_prodlab_perfil_nombre_fecha",
            )
        ]

    def clean(self):
        super().clean()
        validar_no_antes_de_nacimiento(self.perfil, self.fechaproducto, "fechaproducto")


# =========================
# RECONOCIMIENTOS
# =========================
class Reconocimientos(CertificadoMixin, models.Model):
    TIPO_CHOICES = [
        ("Académico", "Académico"),
        ("Público", "Público"),
        ("Privado", "Privado"),
    ]

    idreconocimiento = models.AutoField(primary_key=True)

    perfil = models.ForeignKey(
        Datospersonales,
        on_delete=models.CASCADE,
        related_name="reconocimientos",
        db_column="idperfilconqueestaactivo",
    )

    tiporeconocimiento = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
    )

    fechareconocimiento = models.DateField(
        blank=False,
        null=False,
        validators=[validar_fecha_desde_2000, validar_fecha_no_futura],
    )

    descripcionreconocimiento = models.CharField(max_length=100, blank=True, null=True)

    # ✅ ESTRICTO
    entidadpatrocinadora = models.CharField(max_length=100, blank=False, null=False)

    nombrecontactoauspicia = models.CharField(max_length=100, blank=True, null=True)
    telefonocontactoauspicia = models.CharField(max_length=60, blank=True, null=True, validators=[telefono_basico])

    activarparaqueseveaenfront = models.BooleanField(default=True)

    rutacertificado = models.URLField(max_length=200, blank=True, null=True)

    class Meta:
        db_table = "RECONOCIMIENTOS"
        constraints = [
            models.UniqueConstraint(
                fields=["perfil", "tiporeconocimiento", "fechareconocimiento", "entidadpatrocinadora"],
                name="uq_recon_perfil_tipo_fecha_entidad",
            )
        ]

    def clean(self):
        super().clean()
        validar_no_antes_de_nacimiento(self.perfil, self.fechareconocimiento, "fechareconocimiento")

    def __str__(self):
        return f"{self.tiporeconocimiento} - {self.entidadpatrocinadora or ''}".strip()


# =========================
# VENTA GARAGE
# =========================
class Ventagarage(models.Model):
    ESTADO_CHOICES = [
        ("Bueno", "Bueno"),
        ("Regular", "Regular"),
    ]

    idventagarage = models.AutoField(primary_key=True)

    perfil = models.ForeignKey(
        Datospersonales,
        on_delete=models.CASCADE,
        related_name="venta_garage",
        db_column="idperfilconqueestaactivo",
    )

    # ✅ ESTRICTO
    nombreproducto = models.CharField(max_length=120, blank=False, null=False)

    # ✅ ESTRICTO
    estadoproducto = models.CharField(max_length=40, blank=False, null=False, choices=ESTADO_CHOICES)

    descripcion = models.TextField(blank=True, null=True)

    # ✅ ESTRICTO
    fecha = models.DateField(
        blank=False,
        null=False,
        validators=[validar_fecha_no_futura],
    )

    # ✅ mínimo 0.01 (si lo pones)
    valordelbien = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal("0.01")), MaxValueValidator(Decimal("99999.99"))],
    )

    activarparaqueseveaenfront = models.BooleanField(default=True)
    foto_producto = models.ImageField(upload_to="venta_garage/", blank=True, null=True)

    class Meta:
        db_table = "VENTAGARAGE"
        constraints = [
            models.UniqueConstraint(
                fields=["perfil", "nombreproducto", "fecha"],
                name="uq_venta_perfil_producto_fecha",
            )
        ]

    def clean(self):
        super().clean()
        validar_no_antes_de_nacimiento(self.perfil, self.fecha, "fecha")
