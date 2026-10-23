(() => {
  const form = document.getElementById('ca-form');
  if (!form) return;

  const alertBox = document.getElementById('ca-alert');
  const button = document.getElementById('ca-submit');
  const spinner = button.querySelector('.spinner-border');
  const label = button.querySelector('.ca-submit-text');
  const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  const showAlert = (type, text) => {
    alertBox.className = `alert alert-${type}`;
    alertBox.textContent = text;
    alertBox.focus();
  };

  const setError = (field, message) => {
    field.classList.toggle('is-invalid', Boolean(message));
    const feedback = field.parentElement.querySelector('.invalid-feedback');
    if (feedback) feedback.textContent = message || '';
  };

  const validate = () => {
    let valid = true;
    const rules = {
      nombre: (v) => v.length >= 2 || 'Ingresa tu nombre completo.',
      empresa: (v) => v.length >= 2 || 'Ingresa el nombre de tu empresa.',
      correo: (v) => EMAIL_RE.test(v) || 'Ingresa un correo válido.',
      telefono: (v) => {
        const digits = v.replace(/\D/g, '').length;
        return (digits >= 8 && digits <= 15 && /^[\d\s+()\-.]+$/.test(v)) || 'Ingresa un teléfono válido de 8 a 15 dígitos.';
      },
      asunto: (v) => v.length >= 3 || 'Ingresa el asunto de tu consulta.',
      mensaje: (v) => v.length >= 10 || 'El mensaje debe tener al menos 10 caracteres.',
    };
    Object.entries(rules).forEach(([name, rule]) => {
      const field = form.elements[name];
      const result = rule(field.value.trim());
      setError(field, result === true ? '' : result);
      if (result !== true) valid = false;
    });
    const privacy = form.elements.acepta_privacidad;
    setError(privacy, privacy.checked ? '' : 'Debes aceptar el aviso de privacidad.');
    if (!privacy.checked) valid = false;
    return valid;
  };

  const setLoading = (loading) => {
    button.disabled = loading;
    spinner.classList.toggle('d-none', !loading);
    label.textContent = loading ? 'Enviando…' : 'Enviar mensaje';
  };

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    alertBox.className = 'alert d-none';
    if (!validate()) {
      showAlert('danger', 'Revisa los campos marcados e inténtalo de nuevo.');
      return;
    }
    if (form.dataset.recaptchaEnabled === 'true' && !(window.grecaptcha && window.grecaptcha.getResponse())) {
      showAlert('danger', 'Completa la validación de seguridad.');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(form.action, {
        method: 'POST',
        body: new FormData(form),
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        credentials: 'same-origin',
      });
      const data = await response.json().catch(() => ({}));
      if (response.ok && data.success) {
        form.reset();
        showAlert('success', data.message);
        if (window.grecaptcha && form.dataset.recaptchaEnabled === 'true') window.grecaptcha.reset();
        return;
      }
      Object.entries(data.errors || {}).forEach(([name, errors]) => {
        const field = form.elements[name];
        if (field && errors[0]) setError(field, errors[0].message);
      });
      showAlert('danger', data.message || 'No pudimos enviar tu mensaje. Inténtalo nuevamente.');
    } catch (error) {
      showAlert('danger', 'Error de conexión. Verifica tu red e inténtalo nuevamente.');
    } finally {
      setLoading(false);
    }
  });
})();
