(() => {
  const splash = document.getElementById('pageSplash');
  if (!splash) return;

  const closeSplash = () => {
    window.setTimeout(() => {
      splash.classList.add('is-hidden');
      window.setTimeout(() => splash.remove(), 500);
    }, 450);
  };

  if (document.readyState === 'complete') {
    closeSplash();
  } else {
    window.addEventListener('load', closeSplash, { once: true });
  }
})();
