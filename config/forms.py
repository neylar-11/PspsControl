"""Utilidades de formularios compartidas por todos los módulos."""
from django import forms


class FechaInput(forms.DateInput):
    input_type = 'date'

    def __init__(self, attrs=None):
        super().__init__(attrs=attrs, format='%Y-%m-%d')


class FechaHoraInput(forms.DateTimeInput):
    input_type = 'datetime-local'

    def __init__(self, attrs=None):
        super().__init__(attrs=attrs, format='%Y-%m-%dT%H:%M')


class BootstrapMixin:
    """Agrega las clases de Bootstrap 5 a todos los campos."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            clase = 'form-select' if isinstance(campo.widget, forms.Select) else 'form-control'
            campo.widget.attrs['class'] = (campo.widget.attrs.get('class', '') + ' ' + clase).strip()


def evidencia_obligatoria(valor):
    valor = (valor or '').strip()
    if not valor:
        raise forms.ValidationError('La evidencia es obligatoria: indica un enlace, archivo o referencia.')
    return valor
