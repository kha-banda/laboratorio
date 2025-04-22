// Inicializa la gráfica cuando el documento está listo
document.addEventListener('DOMContentLoaded', function () {
    // Obtén el contenedor para la gráfica
    var myChart = echarts.init(document.getElementById('grafica-ingresos'));
  
    // Datos ficticios en lugar de cargar desde un archivo JSON
    var _rawData = [
      { "Year": 1950, "Country": "Finland", "Income": 3000 },
      { "Year": 1950, "Country": "France", "Income": 5000 },
      { "Year": 1960, "Country": "Finland", "Income": 3500 },
      { "Year": 1960, "Country": "France", "Income": 5500 },
      { "Year": 1970, "Country": "Finland", "Income": 4000 },
      { "Year": 1970, "Country": "France", "Income": 6000 },
      { "Year": 1980, "Country": "Finland", "Income": 4500 },
      { "Year": 1980, "Country": "France", "Income": 6500 },
      { "Year": 1990, "Country": "Finland", "Income": 5000 },
      { "Year": 1990, "Country": "France", "Income": 7000 },
      { "Year": 2000, "Country": "Finland", "Income": 5500 },
      { "Year": 2000, "Country": "France", "Income": 7500 },
      // Agrega más datos ficticios según sea necesario
    ];
  
    function run(_rawData) {
      const countries = [
        'Finland',
        'France',
        'Germany',
        'Iceland',
        'Norway',
        'Poland',
        'Russia',
        'United Kingdom'
      ];
      const datasetWithFilters = [];
      const seriesList = [];
      
      // Crea datasets y series para cada país
      echarts.util.each(countries, function (country) {
        var datasetId = 'dataset_' + country;
        datasetWithFilters.push({
          id: datasetId,
          fromDatasetId: 'dataset_raw',
          transform: {
            type: 'filter',
            config: {
              and: [
                { dimension: 'Year', gte: 1950 },
                { dimension: 'Country', '=': country }
              ]
            }
          }
        });
        seriesList.push({
          type: 'line',
          datasetId: datasetId,
          showSymbol: false,
          name: country,
          endLabel: {
            show: true,
            formatter: function (params) {
              return params.value[3] + ': ' + params.value[0];
            }
          },
          labelLayout: {
            moveOverlap: 'shiftY'
          },
          emphasis: {
            focus: 'series'
          },
          encode: {
            x: 'Year',
            y: 'Income',
            label: ['Country', 'Income'],
            itemName: 'Year',
            tooltip: ['Income']
          }
        });
      });
  
      // Configura la opción de la gráfica
      var option = {
        animationDuration: 10000,
        dataset: [
          {
            id: 'dataset_raw',
            source: _rawData
          },
          ...datasetWithFilters
        ],
        title: {
          left: 'center',
          text: 'Gráfica de Ingresos'
        },
        tooltip: {
          order: 'valueDesc',
          trigger: 'axis'
        },
        xAxis: {
          type: 'category',
          nameLocation: 'middle'
        },
        yAxis: {
          name: 'Income'
        },
        grid: {
          right: 140
        },
        series: seriesList
      };
  
      // Aplica la opción a la gráfica
      myChart.setOption(option);
    }
  
    // Ejecuta la función con los datos ficticios
    run(_rawData);
  });
  