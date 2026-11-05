from datetime import date, timedelta

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UsernameField

from .models import Habitacion, Huesped, Reserva
from .validators import normalizar_rut, normalizar_telefono, validar_rut, validar_telefono


# Formulario Habitacion
class HabitacionForm(forms.ModelForm):
    class Meta:
        model = Habitacion
        fields = ["numero", "tipo", "precio", "disponible"]
        error_messages = {
            "numero": {
                "required": "El número de habitación es obligatorio.",
                "invalid": "El número de habitación debe ser un número entero.",
                "unique": "Ya existe una habitación con ese número.",
            },
            "tipo": {
                "required": "El tipo de habitación es obligatorio.",
            },
            "precio": {
                "required": "El precio por noche es obligatorio.",
                "invalid": "El precio debe ser un número entero.",
            },
        }

    def clean_tipo(self):
        return " ".join(self.cleaned_data["tipo"].split())


# Lista de errores
def lista_de_errores(form):
    errores = []
    for campo, mensajes in form.errors.items():
        for mensaje in mensajes:
            if campo == "__all__":
                errores.append(mensaje)
            else:
                errores.append(f"{form.fields[campo].label}: {mensaje}")
    return errores


# Login
class LoginForm(AuthenticationForm):
    username = UsernameField(
        label="Usuario",
        max_length=30,
        error_messages={"required": "El usuario es obligatorio."},
    )
    password = forms.CharField(
        label="Contraseña",
        strip=False,
        max_length=30,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
        error_messages={"required": "La contraseña es obligatoria."},
    )


# Formulario Huesped
class HuespedForm(forms.ModelForm):
    rut = forms.CharField(
        label="RUT", max_length=12, validators=[validar_rut],
        error_messages={"required": "El RUT es obligatorio.", "max_length": "El RUT es demasiado largo."},
    )
    telefono = forms.CharField(
        label="Teléfono", max_length=16, validators=[validar_telefono],
        error_messages={"required": "El teléfono es obligatorio."},
    )

    class Meta:
        model = Huesped
        fields = ["nombre", "apellido", "rut", "email", "telefono"]
        error_messages = {
            "nombre": {"required": "El nombre es obligatorio."},
            "apellido": {"required": "El apellido es obligatorio."},
            "email": {"required": "El correo es obligatorio.", "invalid": "Ingresa un correo válido. Ejemplo: nombre@correo.cl"},
            "rut": {"unique": "Ya existe un huésped con ese RUT."},
        }

    def clean_nombre(self):
        return " ".join(self.cleaned_data["nombre"].split())

    def clean_apellido(self):
        return " ".join(self.cleaned_data["apellido"].split())

    def clean_rut(self):
        return normalizar_rut(self.cleaned_data["rut"])

    def clean_telefono(self):
        return normalizar_telefono(self.cleaned_data["telefono"])

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()


# Formulario Reserva
class ReservaForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = ["habitacion", "huesped", "fecha_entrada", "fecha_salida", "personas", "estado", "observaciones"]
        widgets = {
            "fecha_entrada": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "fecha_salida": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
        }
        error_messages = {
            "habitacion": {"required": "Debes elegir una habitación.", "invalid_choice": "Habitación no válida."},
            "huesped": {"required": "Debes elegir un huésped.", "invalid_choice": "Huésped no válido."},
            "fecha_entrada": {"required": "La fecha de entrada es obligatoria.", "invalid": "Fecha de entrada no válida."},
            "fecha_salida": {"required": "La fecha de salida es obligatoria.", "invalid": "Fecha de salida no válida."},
            "personas": {"required": "Indica la cantidad de personas.", "invalid": "La cantidad de personas debe ser un número entero."},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        editando = bool(self.instance and self.instance.pk)
        habitaciones = Habitacion.objects.filter(disponible=True)
        if editando:
            habitaciones = Habitacion.objects.filter(disponible=True) | Habitacion.objects.filter(pk=self.instance.habitacion_id)
            posibles = [self.instance.estado] + Reserva.TRANSICIONES[self.instance.estado]
            self.fields["estado"].choices = [(v, e) for v, e in Reserva.ESTADOS if v in posibles]
        else:
            # el estado solo se elige al editar
            del self.fields["estado"]
        self.fields["habitacion"].queryset = habitaciones.distinct().order_by("numero")
        self.fields["habitacion"].empty_label = "— Elige una habitación —"
        self.fields["habitacion"].label_from_instance = lambda h: f"Habitación {h.numero} · {h.tipo} · ${h.precio:,}".replace(",", ".")
        self.fields["huesped"].empty_label = "— Elige un huésped —"
        self.fields["huesped"].label_from_instance = lambda h: f"{h.nombre_completo} · {h.rut_formateado}"
        self.fields["observaciones"].required = False
        if not editando:
            hoy = date.today()
            self.fields["fecha_entrada"].widget.attrs["min"] = hoy.isoformat()
            self.fields["fecha_entrada"].widget.attrs["max"] = (hoy + timedelta(days=Reserva.MAX_ANTICIPACION_DIAS)).isoformat()

    def clean_observaciones(self):
        return " ".join(self.cleaned_data.get("observaciones", "").split())
