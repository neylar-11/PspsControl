from django import forms

from config.forms import BootstrapMixin, FechaHoraInput, evidencia_obligatoria
from .models import Defecto


class DefectoForm(BootstrapMixin, forms.ModelForm):
    def __init__(self, *args, proyecto=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.proyecto = proyecto
        self.instance.proyecto = proyecto

    class Meta:
        model = Defecto
        fields = ['codigo', 'descripcion', 'severidad', 'estado', 'fecha_reporte', 'responsable',
                  'fecha_cierre', 'verificado_por', 'evidencia']
        widgets = {'fecha_reporte': FechaHoraInput(), 'fecha_cierre': FechaHoraInput(),
                   'descripcion': forms.Textarea(attrs={'rows': 3}), 'evidencia': forms.Textarea(attrs={'rows': 2})}

    def clean_evidencia(self):
        return evidencia_obligatoria(self.cleaned_data.get('evidencia'))

    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo', '').strip()
        if codigo and Defecto.objects.filter(proyecto=self.proyecto, codigo=codigo).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Ya existe un defecto con ese identificador en este proyecto.')
        return codigo

    def clean(self):
        datos = super().clean()
        if datos.get('estado') == 'Cerrado':
            if not datos.get('fecha_cierre'):
                self.add_error('fecha_cierre', 'Un defecto cerrado requiere la fecha del cierre verificado.')
            if not datos.get('verificado_por'):
                self.add_error('verificado_por', 'Indica quién verificó el cierre.')
            if datos.get('fecha_cierre') and datos.get('fecha_reporte') and datos['fecha_cierre'] < datos['fecha_reporte']:
                self.add_error('fecha_cierre', 'El cierre no puede ser anterior al reporte.')
        return datos
