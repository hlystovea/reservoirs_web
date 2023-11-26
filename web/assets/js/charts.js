const chartOptions = {
  scales: {
    y: {
        beginAtZero: false
    }
  },
  elements: {
    point: {
      radius: 0
    }
  },
  plugins: {
    legend: {
      display: true,
      position: "bottom",
      labels: {
          boxHeight: 0
      }
    }
  },
};

const levelsData = {
  labels: [],
  datasets: [{
    label: "УВБ, м",
    data: [],
    backgroundColor: "rgba(255, 159, 64, 0.2)",
    borderColor: "rgba(255, 159, 64, 1)",
    borderWidth: 1,
    fill: true,
  }]
};

const levelsConfig = {
  type: "line",
  data: levelsData,
  options: chartOptions
};

const flowsData = {
  labels: [],
  datasets: [{
    label: "Приток, м\u00B3/с",
    data: [],
    backgroundColor: "rgba(255, 99, 132, 0.2)",
    borderColor: "rgba(255, 99, 132, 1)",
    borderWidth: 1,
    fill: true,
  },
  {
    label: "Сброс, м\u00B3/с",
    data: [],
    backgroundColor: "rgba(54, 162, 235, 0.2)",
    borderColor: "rgba(54, 162, 235, 1)",
    borderWidth: 1,
    fill: true,
  },
  {
    label: "Холостой сброс, м\u00B3/с",
    data: [],
    backgroundColor: "rgba(153, 102, 255, 0.2)",
    borderColor: "rgba(153, 102, 255, 1)",
    borderWidth: 1,
    fill: true,
  },
  {
    label: "Приток сред. многолетний, м\u00B3/с",
    data: [],
    backgroundColor: "rgba(201, 203, 207, 0.2)",
    borderColor: "rgba(201, 203, 207, 1)",
    borderWidth: 1,
    fill: true,
  }]
};

const flowsConfig = {
  type: "line",
  data: flowsData,
  options: chartOptions
};

const yearSummaryData = {
  labels: [],
  datasets: [{
    label: "Максимум притока, м\u00B3/с",
    data: [],
    backgroundColor: "rgba(54, 162, 235, 0.2)",
    borderColor: "rgba(54, 162, 235, 1)",
    borderWidth: 1.5,
    yAxisID: 'y1',
    type: "line"
  },
  {
    label: "Годовой объём притока, км\u00B3",
    data: [],
    backgroundColor: "rgba(255, 99, 132, 0.2)",
    borderColor: "rgba(255, 99, 132, 1)",
    borderWidth: 1,
    fill: true,
    yAxisID: 'y'
  },
  {
    label: "Годовой объём холостых сбросов, км\u00B3",
    data: [],
    backgroundColor: "rgba(153, 102, 255, 0.2)",
    borderColor: "rgba(153, 102, 255, 1)",
    borderWidth: 1,
    fill: true,
    yAxisID: 'y'
  }]
};

const yearSummaryConfig = {
  type: "bar",
  data: yearSummaryData,
  options: {
    scales: {
      y: {
        type: 'linear',
        display: true,
        position: 'left',
      },
      y1: {
        type: 'linear',
        display: true,
        position: 'right',
        grid: {
          drawOnChartArea: false,
        }
      }
    },
    elements: {
      point: {
        radius: 0
      }
    },
    plugins: {
      legend: {
        display: true,
        position: "bottom",
        labels: {
            boxHeight: 0
        }
      }
    }
  }
};

const forecastData = {
  labels: [],
  datasets: [{
    label: "Прогноз притока, м\u00B3/с",
    data: [],
    backgroundColor: "rgba(255, 99, 132, 0.2)",
    borderColor: "rgba(255, 99, 132, 1)",
    borderWidth: 1,
    fill: true,
  },
  {
    label: "Фактический приток, м\u00B3/с",
    data: [],
    backgroundColor: "rgba(201, 203, 207, 0.2)",
    borderColor: "rgba(201, 203, 207, 1)",
    borderWidth: 1,
    fill: true,
  }]
};

const forecastConfig = {
  type: "line",
  data: forecastData,
  options: {
    scales: {
      y: {
          beginAtZero: false
      }
    },
    elements: {
      point: {
        radius: 0
      }
    },
    plugins: {
      legend: {
        display: true,
        position: "bottom",
        labels: {
            boxHeight: 0
        }
      }
    },
  }
};

function setLevelsChart(chart, data) {
  chart.data.labels = data.dates;
  chart.data.datasets[0].data = data.levels;
  chart.update();
}

function setFlowsChart(chart, data) {
  chart.data.labels = data.dates;
  chart.data.datasets[0].data = data.inflows;
  chart.data.datasets[1].data = data.outflows;
  chart.data.datasets[2].data = data.spillway;
  chart.data.datasets[3].data = data.avg_inflows;
  chart.update();
}

function setYearSummaryChart(chart, data) {
  chart.data.labels = data.years;
  chart.data.datasets[0].data = data.max_inflows;
  chart.data.datasets[1].data = data.inflow_volumes;
  chart.data.datasets[2].data = data.spillway_volumes;
  chart.update();
}

function setForecastChart(chart, data) {
  chart.data.labels = data.dates;
  chart.data.datasets[0].data = data.inflows;
  chart.data.datasets[1].data = data.facts;
  chart.update();
}
