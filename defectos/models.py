from django.db import models
from django.utils import timezone

from config.utils import asignar_codigo
from proyectos.models import Proyecto


class Defecto(models.Model):
    SEVERIDADES = [('Crítica', 'Crítica'), ('Alta', 'Alta'), ('Media', 'Media'), ('Baja', 'Baja')]
    ESTADOS = [('Abierto', 'Abierto'), ('En corrección', 'En corrección'),
               ('Corregido', 'Corregido (pendiente de verificar)'), ('Cerrado', 'Cerrado (verificado)')]

    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='defectos')
    codigo = models.CharField('identificador', max_length=30, blank=True)
    descripcion = models.TextField()
    severidad = models.CharField(max_length=10, choices=SEVERIDADES)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='Abierto')
    fecha_reporte = models.DateTimeField(default=timezone.now)
    responsable = models.CharField(max_length=100)
    fecha_cierre = models.DateTimeField('cierre verificado el', null=True, blank=True)
    verificado_por = models.CharField(max_length=100, blank=True)
    evidencia = models.TextField(help_text='Captura, log o enlace (obligatoria).')

    class Meta:
        ordering = ['-fecha_reporte', '-id']
        constraints = [models.UniqueConstraint(fields=['proyecto', 'codigo'], name='defecto_codigo_unico')]

    def __str__(self):
        return f'{self.codigo} {self.descripcion[:40]}'

    def save(self, *args, **kwargs):
        asignar_codigo(self, 'DEF')
        if self.estado != 'Cerrado':
            self.fecha_cierre = None
        super().save(*args, **kwargs)

    @property
    def horas_resolucion(self):
        if self.estado == 'Cerrado' and self.fecha_cierre:
            return (self.fecha_cierre - self.fecha_reporte).total_seconds() / 3600
        return None
