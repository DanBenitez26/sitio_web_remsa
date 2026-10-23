document.addEventListener('DOMContentLoaded', () => {
  const widget = document.getElementById('chatbotWidget');
  const toggle = document.getElementById('chatbotToggle');
  const closeButton = document.getElementById('chatbotClose');
  const closeSuccessButton = document.getElementById('chatbotSuccessClose');
  const newInquiryButton = document.getElementById('chatbotNewInquiry');
  const panel = document.getElementById('chatbotPanel');
  const body = document.getElementById('chatbotBody');
  const messageForm = document.getElementById('chatbotForm');
  const input = document.getElementById('chatbotInput');
  const leadForm = document.getElementById('chatbotLeadForm');
  const leadSubmit = document.getElementById('chatbotLeadSubmit');
  const submissionId = document.getElementById('chatbotSubmissionId');
  const phoneInput = document.getElementById('chatbotPhone');
  const formStatus = document.getElementById('chatbotFormStatus');
  const successActions = document.getElementById('chatbotSuccessActions');

  if (
    !widget || !toggle || !panel || !body || !messageForm || !input
    || !leadForm || !leadSubmit || !submissionId || !phoneInput
    || !formStatus || !successActions
  ) return;

  const welcomeText = '¡Hola! 👋 Bienvenido a REMSA Plásticos. ¿En qué podemos ayudarte?';
  const quickReplies = [
    'Quiero información',
    'Quiero una cotización',
    'Ver productos',
    'Hablar con un asesor'
  ];
  const thanksText = '¡Gracias por contactar a REMSA Plásticos! Hemos recibido tus datos. Un asesor comercial dará seguimiento a tu solicitud.';
  const messageSubmit = messageForm.querySelector('button[type="submit"]');
  const csrfToken = messageForm.querySelector('[name="csrfmiddlewaretoken"]')?.value || '';
  let sendingMessage = false;
  let sendingLead = false;

  const createSubmissionId = () => (
    window.crypto?.randomUUID
      ? window.crypto.randomUUID()
      : 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (character) => {
        const random = Math.floor(Math.random() * 16);
        return (character === 'x' ? random : (random & 0x3) | 0x8).toString(16);
      })
  );

  const scrollConversation = () => {
    body.scrollTop = body.scrollHeight;
  };

  const addMessage = (text, sender = 'bot') => {
    const message = document.createElement('div');
    message.className = `message ${sender}`;
    message.textContent = text;
    body.insertBefore(message, leadForm);
    scrollConversation();
    return message;
  };

  const renderQuickReplies = () => {
    const replies = document.createElement('div');
    replies.className = 'chatbot-quick-replies';
    replies.id = 'chatbotQuickReplies';
    replies.setAttribute('aria-label', 'Respuestas rápidas');
    quickReplies.forEach((text) => {
      const button = document.createElement('button');
      button.type = 'button';
      button.dataset.message = text;
      button.textContent = text;
      replies.appendChild(button);
    });
    return replies;
  };

  const showWelcome = () => {
    const welcome = document.createElement('div');
    welcome.className = 'message bot';
    welcome.textContent = welcomeText;
    body.replaceChildren(welcome, renderQuickReplies(), formStatus, leadForm, successActions);
    leadForm.reset();
    formStatus.hidden = true;
    leadForm.hidden = true;
    successActions.hidden = true;
    messageForm.hidden = false;
    submissionId.value = createSubmissionId();
  };

  submissionId.value = createSubmissionId();

  const openChatModal = () => {
    widget.classList.add('modal-mode');
    setPanelOpen(true);
    window.setTimeout(() => input.focus(), 120);
  };

  const setPanelOpen = (open) => {
    widget.classList.toggle('open', open);
    panel.hidden = !open;
    toggle.setAttribute('aria-expanded', String(open));
    if (!open) {
      widget.classList.remove('modal-mode');
      toggle.focus();
      return;
    }
    widget.classList.add('modal-mode');
    window.setTimeout(() => input.focus(), 100);
  };

  const addCatalogueLink = (url) => {
    if (!url) return;
    const catalogueUrl = new URL(url, window.location.origin);
    if (catalogueUrl.origin !== window.location.origin) return;

    const link = document.createElement('a');
    link.className = 'chatbot-catalogue-link';
    link.href = catalogueUrl.href;
    link.textContent = 'Ver catálogo de productos';
    link.setAttribute('aria-label', 'Ver catálogo de productos REMSA');
    body.insertBefore(link, leadForm);
    scrollConversation();
  };

  const setMessageBusy = (busy) => {
    input.disabled = busy;
    if (messageSubmit) messageSubmit.disabled = busy;
    body.querySelectorAll('.chatbot-quick-replies button').forEach((button) => {
      button.disabled = busy;
    });
  };

  const sendMessage = async (value) => {
    const message = value.trim();
    if (!message || sendingMessage || sendingLead) return;

    sendingMessage = true;
    setMessageBusy(true);
    addMessage(message, 'user');
    const typing = addMessage('Un momento, por favor…');

    try {
      const response = await fetch(panel.dataset.endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ message })
      });
      const data = await response.json();
      typing.remove();

      if (!response.ok) {
        addMessage(data.reply || 'No pudimos procesar tu mensaje. Inténtalo de nuevo.');
        return;
      }

      addMessage(data.reply);
      addCatalogueLink(data.catalogue_url);
      if (data.show_form) {
        leadForm.hidden = false;
        const quickReplyBlock = document.getElementById('chatbotQuickReplies');
        if (quickReplyBlock) quickReplyBlock.hidden = true;
        scrollConversation();
      }
    } catch {
      typing.remove();
      addMessage('No pudimos conectar con el asistente. Inténtalo de nuevo en un momento.');
    } finally {
      sendingMessage = false;
      setMessageBusy(false);
      input.focus();
    }
  };

  const showFieldErrors = (errors) => {
    if (!errors || typeof errors !== 'object') return;
    const labels = {
      nombre: 'Nombre',
      empresa: 'Empresa',
      telefono: 'Teléfono o WhatsApp',
      correo: 'Correo electrónico',
      producto: 'Producto de interés',
      mensaje: 'Mensaje'
    };
    const messages = Object.entries(errors).map(([field, details]) => {
      const detail = Array.isArray(details) ? details[0]?.message : '';
      return `${labels[field] || 'Formulario'}: ${detail || 'revisa este dato.'}`;
    });
    if (messages.length) formStatus.textContent = messages.join(' ');
  };

  leadForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (sendingLead || sendingMessage) return;

    const phoneDigits = phoneInput.value.replace(/\D/g, '');
    phoneInput.setCustomValidity(
      phoneDigits.length >= 10 && phoneDigits.length <= 15
        ? ''
        : 'Ingresa un teléfono de 10 a 15 dígitos.'
    );
    if (!leadForm.reportValidity()) return;

    sendingLead = true;
    leadSubmit.disabled = true;
    formStatus.hidden = true;
    formStatus.textContent = '';
    try {
      const response = await fetch(leadForm.action, {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrfToken,
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: new FormData(leadForm)
      });
      const data = await response.json();
      if (!response.ok || !data.success) {
        formStatus.textContent = data.message || 'No pudimos guardar tu solicitud. Inténtalo de nuevo.';
        showFieldErrors(data.errors);
        formStatus.hidden = false;
        return;
      }

      leadForm.hidden = true;
      formStatus.hidden = true;
      messageForm.hidden = true;
      addMessage(data.message || thanksText);
      successActions.hidden = false;
      scrollConversation();
    } catch {
      formStatus.textContent = 'No pudimos enviar tu solicitud. Revisa tu conexión e inténtalo de nuevo.';
      formStatus.hidden = false;
    } finally {
      sendingLead = false;
      leadSubmit.disabled = false;
    }
  });

  body.addEventListener('click', (event) => {
    const button = event.target.closest('[data-message]');
    if (!button || sendingMessage || sendingLead) return;
    input.value = '';
    sendMessage(button.dataset.message || '');
  });

  messageForm.addEventListener('submit', (event) => {
    event.preventDefault();
    const value = input.value;
    if (!value.trim() || sendingMessage || sendingLead) return;
    input.value = '';
    sendMessage(value);
  });

  toggle.addEventListener('click', () => setPanelOpen(panel.hidden));
  closeButton?.addEventListener('click', () => setPanelOpen(false));
  closeSuccessButton?.addEventListener('click', () => setPanelOpen(false));
  document.querySelectorAll('[data-open-chat-modal]').forEach((trigger) => {
    trigger.addEventListener('click', (event) => {
      event.preventDefault();
      event.stopPropagation();
      const parentModal = trigger.closest('.modal.show');
      const modalInstance = parentModal && window.bootstrap?.Modal?.getInstance(parentModal);
      if (!modalInstance) {
        openChatModal();
        return;
      }
      // El modal de Bootstrap bloquea el foco y tapa el chat; se cierra antes de abrirlo.
      parentModal.addEventListener('hidden.bs.modal', openChatModal, { once: true });
      modalInstance.hide();
    });
  });

  document.addEventListener('click', (event) => {
    const trigger = event.target.closest('[data-open-chat-modal]');
    if (trigger) return;
    if (!panel.hidden && !panel.contains(event.target) && !toggle.contains(event.target)) {
      setPanelOpen(false);
    }
  });
  newInquiryButton?.addEventListener('click', () => {
    showWelcome();
    input.focus();
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && !panel.hidden) setPanelOpen(false);
  });
});
