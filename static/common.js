// Reload the page when Firefox (or any browser) restores it from bfcache,
// so that the displayed data is always fresh after back/forward navigation.
window.addEventListener("pageshow", function (event) {
  if (event.persisted) {
    window.location.reload();
  }
});