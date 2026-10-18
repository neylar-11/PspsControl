from datetime import timedelta

from django.db import models
from django.urls import reverse


class Proyecto(models.Model):
    """Un proyecto por intervalo de registro: al abrir otro intervalo se crea otro proyecto."""

    nombre = models.CharField(max_length=140)
    descripcion = models.TextField(blank=True)
    responsable = models.CharField(max_length=100)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    duracion_dias = models.PositiveIntegerField(default=14, help_text='Duración del intervalo en días.')
    objetivo_resolucion_horas = models.PositiveIntegerField(
        default=72, help_text='T: objetivo de resolución de defectos (horas naturales).')
    registro_defectos_confirmado = models.BooleanField(
        default=False,
        help_text='Confirma que el registro de defectos está completo; sin esto, "cero defectos" se trata como falta de datos.')
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_inicio', 'nombre']
        constraints = [models.UniqueConstraint(fields=['nombre', 'fecha_inicio'], name='proyecto_unico_por_intervalo')]

    def __str__(self):
        return f'{self.nombre} ({self.fecha_inicio:%d/%m/%Y} – {self.fecha_fin:%d/%m/%Y})'

    def get_absolute_url(self):
        return reverse('metricas:dashboard', args=[self.pk])

    @staticmethod
    def calcular_fin(inicio, duracion_dias):
        return inicio + timedelta(days=duracion_dias)
