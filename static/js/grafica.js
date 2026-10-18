(function () {
  const datos = JSON.parse(document.getElementById('datos-grafica').textContent);
  const nombres = { pruebas_aprobadas: 'Pruebas aprobadas', avance_ejecucion: 'Avance de ejecución', cumplimiento_sqa: 'Cumplimiento SQA' };
  const colores = { pruebas_aprobadas: '#198754', avance_ejecucion: '#0d6efd', cumplimiento_sqa: '#fd7e14' };
  new Chart(document.getElementById('grafica'), {
    type: 'line',
    data: {
      labels: datos.fechas,
      datasets: Object.keys(datos.series).map((k) => ({
        label: nombres[k], data: datos.series[k], borderColor: colores[k], backgroundColor: colores[k],
        spanGaps: true, tension: 0.2,
      })),
    },
    options: { scales: { y: { min: 0, max: 100, title: { display: true, text: '%' } } } },
  });
})();
