// Comportamiento del navbar: sombra al hacer scroll + toggle de buscador
document.addEventListener('DOMContentLoaded', () => {
  const navbar = document.querySelector('.navbar-remsa');
  if (navbar) {
    window.addEventListener('scroll', () => {
      navbar.classList.toggle('shadow', window.scrollY > 10);
    });
  }

  const buscadorToggle = document.getElementById('buscadorToggle');
  const buscadorBox = document.getElementById('buscadorBox');
  if (buscadorToggle && buscadorBox) {
    buscadorToggle.addEventListener('click', () => {
      buscadorBox.classList.toggle('d-none');
      if (!buscadorBox.classList.contains('d-none')) {
        buscadorBox.querySelector('input')?.focus();
      }
    });
  }
});
