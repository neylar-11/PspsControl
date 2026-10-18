from django.db import models

from proyectos.models import Proyecto


class Corte(models.Model):
    """Medición completa de un proyecto a una fecha de corte (se conserva con sus umbrales)."""

    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='cortes')
    fecha_corte = models.DateField()
    estado_general = models.CharField(max_length=10)
    motivo_general = models.CharField(max_length=200, blank=True)
    umbrales = models.JSONField(default=dict)
    detalle = models.JSONField(default=dict, help_text='Pendientes y evidencias al corte.')
    calculado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha_corte']
        constraints = [models.UniqueConstraint(fields=['proyecto', 'fecha_corte'], name='corte_unico_por_fecha')]

    def __str__(self):
        return f'{self.proyecto.nombre} @ {self.fecha_corte}'


class Medicion(models.Model):
    corte = models.ForeignKey(Corte, on_delete=models.CASCADE, related_name='mediciones')
    clave = models.CharField(max_length=40)
    nombre = models.CharField(max_length=80)
    valor = models.FloatField(null=True, blank=True)
    unidad = models.CharField(max_length=10, blank=True)
    estado = models.CharField(max_length=10)
    motivo = models.CharField(max_length=200, blank=True)
    numerador = models.FloatField(null=True, blank=True)
    denominador = models.FloatField(null=True, blank=True)
    regla = models.CharField('umbrales usados', max_length=200)
    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['orden']

    @property
    def etiqueta(self):
        return {'verde': 'Verde', 'amarillo': 'Amarillo', 'rojo': 'Rojo', 'gris': 'Sin datos',
                'no_aplica': 'No aplica'}[self.estado]
