// Confirma antes de eliminar un item del carrito de cotizacion
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.btn-eliminar-item').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      if (!confirm('¿Quitar este producto de tu solicitud de cotización?')) {
        e.preventDefault();
      }
    });
  });

  // Actualiza cantidad automaticamente al cambiar el input (submit del formulario padre)
  document.querySelectorAll('.input-cantidad-carrito').forEach((input) => {
    input.addEventListener('change', () => {
      input.closest('form')?.submit();
    });
  });
});
