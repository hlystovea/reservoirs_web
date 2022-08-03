// sets cookie
function setCookie(name, value) {
  document.cookie = name + "=" + (value || "") + "; path=/; max-age=86400";
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
  let max_levels = [];
  let inflow_volumes = [];
  let outflow_volumes = [];
  let spillway_volumes = [];

  for (var i in data) {
    years.push(data[i].year);
    max_levels.push(data[i].max_level);
    inflow_volumes.push(data[i].inflow_volume);
    outflow_volumes.push(data[i].outflow_volume);
    spillway_volumes.push(data[i].spillway_volume);
  };

  return {
    years: years,
    max_levels: max_levels,
    inflow_volumes: inflow_volumes,
    outflow_volumes: outflow_volumes,
    spillway_volumes: spillway_volumes
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
