// Auto-envio del formulario de filtros del catalogo al cambiar categoria/material
document.addEventListener('DOMContentLoaded', () => {
  const formFiltros = document.getElementById('formFiltrosCatalogo');
  if (!formFiltros) return;
  formFiltros.querySelectorAll('select').forEach((select) => {
    select.addEventListener('change', () => formFiltros.submit());
  });
});
