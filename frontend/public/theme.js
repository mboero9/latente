try {
  document.documentElement.dataset.theme =
    localStorage.getItem("latente-theme") ||
    (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
} catch (_) {
  document.documentElement.dataset.theme = "light";
}
