// Revela elementos con clase .reveal cuando entran al viewport
document.addEventListener('DOMContentLoaded', () => {
  const elementos = document.querySelectorAll('.reveal');
  if (!('IntersectionObserver' in window) || elementos.length === 0) {
    elementos.forEach(el => el.classList.add('is-visible'));
    return;
  }
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15 });
  elementos.forEach(el => observer.observe(el));
});
