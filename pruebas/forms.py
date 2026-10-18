from django import forms

from config.forms import BootstrapMixin, FechaInput, evidencia_obligatoria
from .models import CasoPrueba, ResultadoPrueba


class CasoForm(BootstrapMixin, forms.ModelForm):
    def __init__(self, *args, proyecto=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.proyecto = proyecto
        self.instance.proyecto = proyecto

    class Meta:
        model = CasoPrueba
        fields = ['codigo', 'nombre', 'version', 'pasos', 'resultado_esperado', 'responsable', 'fecha_prevista']
        widgets = {'fecha_prevista': FechaInput(), 'pasos': forms.Textarea(attrs={'rows': 3}),
                   'resultado_esperado': forms.Textarea(attrs={'rows': 2})}

    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo', '').strip()
        if codigo and CasoPrueba.objects.filter(proyecto=self.proyecto, codigo=codigo).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Ya existe un caso con ese identificador en este proyecto.')
        return codigo


class ResultadoForm(BootstrapMixin, forms.ModelForm):
    def __init__(self, *args, proyecto=None, caso=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.caso = caso

    class Meta:
        model = ResultadoPrueba
        fields = ['fecha_ejecucion', 'resultado', 'resultado_obtenido', 'ejecutor', 'evidencia']
        widgets = {'fecha_ejecucion': FechaInput(), 'resultado_obtenido': forms.Textarea(attrs={'rows': 2}),
                   'evidencia': forms.Textarea(attrs={'rows': 2})}

    def clean_evidencia(self):
        return evidencia_obligatoria(self.cleaned_data.get('evidencia'))
