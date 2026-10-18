from django.db import models
from django.utils import timezone

from config.utils import asignar_codigo
from proyectos.models import Proyecto


class Actividad(models.Model):
    TIPOS = [('Revisión', 'Revisión'), ('Inspección', 'Inspección'), ('Prueba', 'Prueba')]
    ESTADOS = [('Planeada', 'Planeada'), ('En curso', 'En curso'), ('Terminada', 'Terminada')]

    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='actividades')
    codigo = models.CharField('identificador', max_length=30, blank=True)
    nombre = models.CharField(max_length=160)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    responsable = models.CharField(max_length=100)
    fecha_prevista = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='Planeada')
    fecha_terminada = models.DateField(null=True, blank=True)
    evidencia = models.TextField(help_text='Enlace, archivo o referencia verificable (obligatoria).')

    class Meta:
        ordering = ['fecha_prevista', 'id']
        verbose_name_plural = 'actividades'
        constraints = [models.UniqueConstraint(fields=['proyecto', 'codigo'], name='actividad_codigo_unico')]

    def __str__(self):
        return f'{self.codigo} {self.nombre}'

    def save(self, *args, **kwargs):
        asignar_codigo(self, 'ACT')
        if self.estado == 'Terminada' and not self.fecha_terminada:
            self.fecha_terminada = timezone.localdate()
        if self.estado != 'Terminada':
            self.fecha_terminada = None
        super().save(*args, **kwargs)
