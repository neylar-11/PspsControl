from django import forms

from config.forms import BootstrapMixin, FechaInput, evidencia_obligatoria
from .models import Actividad


class ActividadForm(BootstrapMixin, forms.ModelForm):
    def __init__(self, *args, proyecto=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.proyecto = proyecto
        self.instance.proyecto = proyecto

    class Meta:
        model = Actividad
        fields = ['codigo', 'nombre', 'tipo', 'responsable', 'fecha_prevista', 'estado', 'fecha_terminada', 'evidencia']
        widgets = {'fecha_prevista': FechaInput(), 'fecha_terminada': FechaInput(),
                   'evidencia': forms.Textarea(attrs={'rows': 2})}

    def clean_evidencia(self):
        return evidencia_obligatoria(self.cleaned_data.get('evidencia'))

    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo', '').strip()
        if codigo and Actividad.objects.filter(proyecto=self.proyecto, codigo=codigo).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Ya existe una actividad con ese identificador en este proyecto.')
        return codigo
