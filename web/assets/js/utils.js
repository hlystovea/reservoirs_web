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
function formatToArray(data) {
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