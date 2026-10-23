(() => {
  const GOOGLE_TRANSLATE_TIMEOUT = 15000;
  let googleTranslateReady = null;
  let resolveGoogleTranslate;
  googleTranslateReady = new Promise((resolve) => {
    resolveGoogleTranslate = resolve;
  });

  const languageOptions = ['es', 'en'];
  const normalizeLanguage = (value) => languageOptions.includes(value) ? value : 'es';

  const readSavedLanguage = () => {
    try {
      const saved = window.localStorage.getItem('remsa-language');
      if (languageOptions.includes(saved)) return saved;
    } catch (error) {
      console.warn('No se pudo leer el idioma guardado.', error);
    }

    const translateCookie = document.cookie
      .split(';')
      .map((cookie) => cookie.trim())
      .find((cookie) => cookie.startsWith('googtrans='));
    if (!translateCookie) return 'es';

    try {
      const match = decodeURIComponent(translateCookie.slice('googtrans='.length))
        .match(/^\/es\/(en|es)(?:$|\/)/);
      return match ? match[1] : 'es';
    } catch (error) {
      console.warn('No se pudo interpretar el idioma guardado por el traductor.', error);
      return 'es';
    }
  };

  const updateLanguageControl = (language) => {
    const normalized = normalizeLanguage(language);
    const label = document.querySelector('[data-language-label]');
    if (label) label.textContent = normalized === 'en' ? 'EN' : 'ES-MX';

    document.querySelectorAll('.idioma-opcion').forEach((option) => {
      const isActive = option.dataset.language === normalized;
      option.classList.toggle('active', isActive);
      option.setAttribute('aria-pressed', String(isActive));
    });
  };

  const setLanguageStatus = (message) => {
    const status = document.getElementById('languageStatus');
    if (status) status.textContent = message;
  };

  const waitForGoogleSelect = () => new Promise((resolve) => {
    const findSelect = () => {
      const select = document.querySelector('.goog-te-combo');
      if (select && Array.from(select.options).some((option) => option.value === 'en')) {
        observer.disconnect();
        window.clearTimeout(timeoutId);
        resolve(select);
        return true;
      }
      return false;
    };

    const observer = new MutationObserver(findSelect);
    const translateElement = document.getElementById('google_translate_element');
    if (translateElement) {
      observer.observe(translateElement, { childList: true, subtree: true });
    }
    const timeoutId = window.setTimeout(() => {
      observer.disconnect();
      resolve(null);
    }, GOOGLE_TRANSLATE_TIMEOUT);
    findSelect();
  });

  const applyLanguage = async (requestedLanguage, reloadAfterApply = false) => {
    const language = normalizeLanguage(requestedLanguage);
    updateLanguageControl(language);
    setLanguageStatus(language === 'es'
      ? 'Restaurando español de México...'
      : 'Cambiando a inglés...');

    document.documentElement.lang = language === 'es' ? 'es-MX' : 'en';

    try {
      window.localStorage.setItem('remsa-language', language);
    } catch (error) {
      console.warn('No se pudo guardar el idioma seleccionado.', error);
    }

    const translateTarget = language === 'es' ? 'es' : 'en';
    document.cookie = `googtrans=/es/${translateTarget};path=/;max-age=31536000;SameSite=Lax`;

    if (reloadAfterApply) {
      googleTranslateReady.then((select) => {
        if (select) {
          select.value = language === 'es' ? '' : 'en';
          select.dispatchEvent(new Event('change', { bubbles: true }));
        }
      });
      window.setTimeout(() => window.location.reload(), 250);
      return true;
    }

    const select = await Promise.race([
      googleTranslateReady,
      new Promise((resolve) => window.setTimeout(() => resolve(null), GOOGLE_TRANSLATE_TIMEOUT))
    ]);
    if (select) {
      select.value = language === 'es' ? '' : 'en';
      select.dispatchEvent(new Event('change', { bubbles: true }));
    }
    return true;
  };

  window.googleTranslateElementInit = () => {
    if (!window.google?.translate?.TranslateElement) {
      setLanguageStatus('No se pudo iniciar el traductor. Intenta nuevamente.');
      resolveGoogleTranslate(null);
      return;
    }

    new window.google.translate.TranslateElement({
      pageLanguage: 'es',
      includedLanguages: 'en,es',
      autoDisplay: false
    }, 'google_translate_element');

    waitForGoogleSelect().then((select) => {
      resolveGoogleTranslate(select);
      if (!select) {
        setLanguageStatus('El traductor no está disponible en este momento.');
        return;
      }
      applyLanguage(readSavedLanguage());
    });
  };

  document.addEventListener('DOMContentLoaded', () => {
    updateLanguageControl(readSavedLanguage());
    document.querySelectorAll('.idioma-opcion').forEach((option) => {
      option.addEventListener('click', () => {
        applyLanguage(option.dataset.language, true);
      });
    });
  });

  const googleScript = document.querySelector('script[src*="translate_a/element.js"]');
  googleScript?.addEventListener('error', () => {
    resolveGoogleTranslate(null);
    setLanguageStatus('No se pudo cargar el traductor de idiomas.');
  });
})();
