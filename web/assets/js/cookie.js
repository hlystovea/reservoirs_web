// sets cookie
function setCookie(name, value) {
  document.cookie = name + "=" + (value || "") + "; path=/";
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
