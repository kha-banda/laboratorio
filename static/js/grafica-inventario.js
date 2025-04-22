document.addEventListener('DOMContentLoaded', function () {
  // Inicializa la gráfica en el contenedor
  var myChart = echarts.init(document.getElementById('grafica-inventario'));

  var option = {
    color: ['#56A3F1', '#FF917C', '#67F9D8', '#FFE434'],
    title: {
      text: 'Gráfica de Inventario',
      textAlign: 'center',
      left: 'center',
      top: 'top'
    },
    legend: {
      orient: 'horizontal',
      bottom: 10,
      left: 'center'
    },
    radar: [
      {
        indicator: [
          { text: 'A', max: 150 },
          { text: 'B', max: 150 },
          { text: 'C', max: 150 },
          { text: 'D', max: 120 },
          { text: 'E', max: 108 },
          { text: 'F', max: 72 }
        ],
        center: ['50%', '50%'],
        radius: 120,
        axisName: {
          color: '#fff',
          backgroundColor: '#666',
          borderRadius: 3,
          padding: [3, 5]
        }
      }
    ],
    series: [
      {
        type: 'radar',
        radarIndex: 0,
        data: [
          {
            value: [120, 118, 130, 100, 99, 70],
            name: 'Data A',
            symbol: 'rect',
            symbolSize: 12,
            lineStyle: {
              type: 'dashed'
            },
            label: {
              show: true,
              formatter: function (params) {
                return params.value;
              }
            }
          },
          {
            value: [100, 93, 50, 90, 70, 60],
            name: 'Data B',
            areaStyle: {
              color: new echarts.graphic.RadialGradient(0.1, 0.6, 1, [
                {
                  color: 'rgba(255, 145, 124, 0.1)',
                  offset: 0
                },
                {
                  color: 'rgba(255, 145, 124, 0.9)',
                  offset: 1
                }
              ])
            }
          }
        ]
      }
    ]
  };

  // Establece la opción configurada en la gráfica
  myChart.setOption(option);
});
