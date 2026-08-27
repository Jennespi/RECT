// Marca en el submenú de "Etapa 1" el enlace de la sección abierta.
// La navegación real la resuelve Flask (una ruta por sección); este script
// solo refuerza el estado activo si la clase no viene ya del servidor.
const path = window.location.pathname;

document.querySelectorAll(".toc a").forEach((link) => {
  if (link.getAttribute("href") === path) {
    link.classList.add("is-active");
    link.setAttribute("aria-current", "page");
  }
});
