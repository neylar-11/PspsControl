from django.db import models

from config.utils import asignar_codigo
from proyectos.models import Proyecto


class CasoPrueba(models.Model):
    """Caso planificado para una versión del proyecto."""

    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='casos')
    codigo = models.CharField('identificador', max_length=30, blank=True)
    nombre = models.CharField(max_length=160)
    version = models.CharField('versión', max_length=30)
    pasos = models.TextField('entradas o pasos')
    resultado_esperado = models.TextField()
    responsable = models.CharField(max_length=100)
    fecha_prevista = models.DateField()

    class Meta:
        ordering = ['fecha_prevista', 'id']
        verbose_name_plural = 'casos de prueba'
        constraints = [models.UniqueConstraint(fields=['proyecto', 'codigo'], name='caso_codigo_unico')]

    def __str__(self):
        return f'{self.codigo} {self.nombre}'

    def save(self, *args, **kwargs):
        asignar_codigo(self, 'CP')
        super().save(*args, **kwargs)

    def ultimo_resultado(self, al_corte=None):
        resultados = self.resultados.all()
        if al_corte:
            resultados = resultados.filter(fecha_ejecucion__lte=al_corte)
        return resultados.order_by('fecha_ejecucion', 'id').last()


class ResultadoPrueba(models.Model):
    RESULTADOS = [('Aprobada', 'Aprobada'), ('Fallida', 'Fallida')]

    caso = models.ForeignKey(CasoPrueba, on_delete=models.CASCADE, related_name='resultados')
    fecha_ejecucion = models.DateField()
    resultado = models.CharField(max_length=10, choices=RESULTADOS)
    resultado_obtenido = models.TextField()
    ejecutor = models.CharField(max_length=100)
    evidencia = models.TextField(help_text='Captura, log o enlace (obligatoria).')

    class Meta:
        ordering = ['fecha_ejecucion', 'id']
