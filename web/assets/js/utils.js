// sets cookie
function setCookie(name, value) {
  document.cookie = name + "=" + (value || "") + "; path=/; max-age=" + 365*24*60*60;
}

// gets cookie
function getCookie(name) {
  name += "=";
  const cookiesDecoded = decodeURIComponent(document.cookie);
  const cookiesArr = cookiesDecoded.split('; ');
  let value;
  cookiesArr.forEach(cookie => {
      if (cookie.indexOf(name) === 0) value = cookie.substring(name.length);
  })
  return value;
}

// disables the cookie alert
function disableCookieAlert() {
  setCookie("dont_show_cookie_alert", "true")
};

// gets object by slug
function getObjectBySlug(objects, slug) {
  if (slug == null) {
    return objects[0]
  };
  return objects.find(obj => obj.slug == slug);
}

// formatting water situation data
function formatSituationsToArray(data) {
  let dates = [];
  let levels = [];
  let inflows = [];
  let outflows = [];
  let spillway = [];
  let avg_inflows = [];

  for (var i in data) {
    dates.push(data[i].date);
    levels.push(data[i].level);
    inflows.push(data[i].inflow);
    outflows.push(data[i].outflow);
    spillway.push(data[i].spillway);
    avg_inflows.push(data[i].avg_inflow);
  };

  return {
    dates: dates,
    levels: levels,
    inflows: inflows,
    outflows: outflows,
    spillway: spillway,
    avg_inflows: avg_inflows
  };
}

// formatting year summary data
function formatYearSummaryToArray(data) {
  let years = [];
  let max_inflows = [];
  let inflow_volumes = [];
  let outflow_volumes = [];
  let spillway_volumes = [];

  for (var i in data) {
    years.push(data[i].year);
    max_inflows.push(data[i].max_inflow);
    inflow_volumes.push(data[i].inflow_volume);
    outflow_volumes.push(data[i].outflow_volume);
    spillway_volumes.push(data[i].spillway_volume);
  };

  return {
    years: years,
    max_inflows: max_inflows,
    inflow_volumes: inflow_volumes,
    outflow_volumes: outflow_volumes,
    spillway_volumes: spillway_volumes
  };
}

function formatForecastToArray(data) {
  let dates = [];
  let inflows = [];
  let facts = [];

  data.forEach((item, index, array) => {
    dates.push(item.date);
    inflows.push(item.inflow);
    facts.push(item.fact);
  });

  return {
    dates: dates,
    inflows: inflows,
    facts: facts
  };
}

// calc a volumes
function calcVolumes(data) {
  let inflowVolume = 0;
  let outflowVolume = 0;
  let spillwayVolume = 0;
  let avgInflowsVolume = 0;

  inflowVolume = data.inflows.map(i=>x+=i, x=0).reverse()[0]
  outflowVolume = data.outflows.map(i=>x+=i, x=0).reverse()[0]
  spillwayVolume = data.spillway.map(i=>x+=i, x=0).reverse()[0]
  avgInflowsVolume = data.avg_inflows.map(i=>x+=i, x=0).reverse()[0]

  inflowVolume = inflowVolume * 864 / 10000000;
  outflowVolume = outflowVolume * 864 / 10000000;
  spillwayVolume = spillwayVolume * 864 / 10000000;
  avgInflowsVolume = avgInflowsVolume * 864 / 10000000;

  return {
    inflow: inflowVolume.toFixed(2),
    outflow: outflowVolume.toFixed(2),
    spillway: spillwayVolume.toFixed(2),
    avgInflow: avgInflowsVolume.toFixed(2)
  };
}

// Render selectReservoir input
const renderSelectReservoir = function (reservoirs) {
  let newInnerHTML = '';
  for (const i in reservoirs) {
    newInnerHTML += `<option id=${reservoirs[i].slug} value=${reservoirs[i].slug}>${reservoirs[i].name}</option>`;
  }
  selectReservoir.innerHTML = newInnerHTML;
};

// Render selectPredictor input
const renderSelectPredictor = function (predictors) {
  let newInnerHTML = '';
  for (const i in predictors) {
    newInnerHTML += `<option value=${predictors[i].id}>${predictors[i].name}</option>`;
  }
  selectPredictor.innerHTML = newInnerHTML;
};

// Update reservoirs select
async function updateReservoirs(has_predictors = false) {
  let url = '/api/v1/reservoirs/';
  if (has_predictors) {
    url += '?has_predictors=true';
  };
  await fetch(url)
    .then(response => response.json())
    .then(data => {
      reservoirs = data;
      renderSelectReservoir(data);
    })
    .catch(error => console.error('Error:', error));
};