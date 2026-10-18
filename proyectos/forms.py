from django import forms

from config.forms import BootstrapMixin, FechaInput
from .models import Proyecto


class ProyectoForm(BootstrapMixin, forms.ModelForm):
    fecha_fin = forms.DateField(required=False, widget=FechaInput(),
                                help_text='Si la dejas vacía se calcula con la duración.')

    class Meta:
        model = Proyecto
        fields = ['nombre', 'descripcion', 'responsable', 'fecha_inicio', 'fecha_fin',
                  'duracion_dias', 'objetivo_resolucion_horas']
        widgets = {'fecha_inicio': FechaInput(), 'descripcion': forms.Textarea(attrs={'rows': 3})}

    def clean(self):
        datos = super().clean()
        inicio, fin, dias = datos.get('fecha_inicio'), datos.get('fecha_fin'), datos.get('duracion_dias')
        if inicio and not fin and dias:
            datos['fecha_fin'] = Proyecto.calcular_fin(inicio, dias)
        elif inicio and fin and fin < inicio:
            self.add_error('fecha_fin', 'La fecha de fin no puede ser anterior a la de inicio.')
        if dias is not None and dias < 1:
            self.add_error('duracion_dias', 'La duración debe ser de al menos 1 día.')
        if datos.get('objetivo_resolucion_horas') == 0:
            self.add_error('objetivo_resolucion_horas', 'El objetivo T debe ser mayor que cero.')
        return datos
