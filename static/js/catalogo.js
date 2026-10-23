document.addEventListener('DOMContentLoaded', () => {
  const filterForm = document.getElementById('filtrosCatalogo');
  const searchInput = document.getElementById('busquedaCatalogo');
  const categoryInput = filterForm?.querySelector('input[name="categoria"]');

  if (searchInput && filterForm) {
    let searchTimer;
    searchInput.addEventListener('input', () => {
      window.clearTimeout(searchTimer);
      searchTimer = window.setTimeout(() => filterForm.requestSubmit(), 350);
    });

    filterForm.querySelectorAll('select').forEach((select) => {
      select.addEventListener('change', () => filterForm.requestSubmit());
    });

    filterForm.addEventListener('reset', (event) => {
      event.preventDefault();
      const destination = new URL(window.location.pathname, window.location.origin);
      if (categoryInput?.value) {
        destination.searchParams.set('categoria', categoryInput.value);
      }
      window.location.assign(destination.toString());
    });
  }

  const detailModal = document.getElementById('modalDetalleProducto');
  detailModal?.addEventListener('show.bs.modal', (event) => {
    const trigger = event.relatedTarget;
    if (!trigger) return;

    const detailTemplate = document.getElementById(trigger.dataset.productDetail);
    if (!detailTemplate) return;

    document.getElementById('modalDetalleProductoTitulo').textContent =
      trigger.dataset.productName || '';
    document.getElementById('modalDetalleProductoContenido').replaceChildren(
      detailTemplate.content.cloneNode(true),
    );
    const pdfLink = document.getElementById('modalFichaPdf');
    if (pdfLink) pdfLink.href = trigger.dataset.productPdf || '#';
    const quoteButton = document.getElementById('modalCotizarForm');
    if (quoteButton) quoteButton.action = trigger.dataset.productQuote || '';
  });

  const categoryModal = document.getElementById('modalDetalleCategoria');
  const fichaContainer = document.getElementById('modalDetalleCategoriaFicha');
  const productSelect = document.getElementById('modalDetalleCategoriaProducto');
  const NO_DATA = 'No especificado';
  let categoryProducts = [];
  let categoryRequest = 0;

  const el = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  };

  const fichaBlock = (title, content) => {
    const block = el('section', 'catalogo-ficha-bloque');
    block.append(el('h4', null, title), content);
    return block;
  };

  const valueList = (values) => {
    if (!values || !values.length) return el('p', 'catalogo-ficha-vacio', NO_DATA);
    const list = el('ul', 'catalogo-ficha-lista');
    values.forEach((value) => list.append(el('li', null, value)));
    return list;
  };

  const fichaItem = (label, value) => {
    const item = el('div', 'catalogo-ficha-dato');
    item.append(
      el('span', 'catalogo-ficha-etiqueta', label),
      el('strong', value ? '' : 'catalogo-ficha-vacio', value || NO_DATA),
    );
    return item;
  };

  const isSafeUrl = (url) => {
    try {
      return ['http:', 'https:'].includes(new URL(url, window.location.origin).protocol);
    } catch {
      return false;
    }
  };

  const COLOR_HEX = {
    transparente: '#e8f1f8', natural: '#efe6cf', cristal: '#e8f1f8', blanco: '#ffffff',
    negro: '#1b1b1b', azul: '#1f5fbf', 'azul marino': '#0b2a5a', rojo: '#c62828',
    verde: '#2e8b57', amarillo: '#f5c518', naranja: '#f7941d', gris: '#8a949e',
    plata: '#c0c4c8', cafe: '#6b4226', ambar: '#b5651d', morado: '#6a3d9a',
    rosa: '#e886b4', celeste: '#7dc4ec', beige: '#d9c7a1',
  };

  const plainText = (text) => text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();

  const colorChips = (values) => {
    if (!values || !values.length) return el('p', 'catalogo-ficha-vacio', NO_DATA);
    const list = el('ul', 'catalogo-ficha-colores');
    values.forEach((value) => {
      const chip = el('li', 'catalogo-ficha-color');
      const hex = COLOR_HEX[plainText(value)];
      if (hex) {
        const swatch = el('span', 'catalogo-ficha-muestra');
        swatch.style.background = hex;
        swatch.setAttribute('aria-hidden', 'true');
        chip.append(swatch);
      }
      chip.append(document.createTextNode(value));
      list.append(chip);
    });
    return list;
  };

  const hasValue = (value) => Array.isArray(value) ? value.length > 0 : Boolean(value);

  const modalImage = document.getElementById('modalDetalleCategoriaImagen');
  let categoryImage = '';

  const showProductImage = (product) => {
    if (!modalImage) return;
    const url = product?.imagen_principal;
    modalImage.src = url && isSafeUrl(url) ? url : categoryImage;
    modalImage.alt = product?.nombre || modalImage.alt;
  };

  const renderFicha = (product) => {
    showProductImage(product);
    const ficha = product?.ficha_tecnica;
    fichaContainer.replaceChildren();
    if (!ficha) {
      fichaContainer.append(el('p', 'catalogo-ficha-vacio', 'No hay especificaciones disponibles.'));
      return;
    }

    const isCap = /^tapas?$/i.test(ficha.categoria || '');
    const blocks = [];

    const general = ficha.general || {};
    const generalBody = el('div');
    [
      ['Producto', product.nombre], ['Modelo', general.modelo], ['Material', general.material],
      ['Peso', general.peso], ['Tipo de boca', general.boca],
      ['Altura', general.alto], ['Ancho', general.ancho],
    ]
      .filter(([, value]) => hasValue(value))
      .forEach(([label, value]) => {
        const row = el('p', 'catalogo-ficha-fila');
        row.append(el('span', 'catalogo-ficha-etiqueta', `${label}: `), document.createTextNode(value));
        generalBody.append(row);
      });
    if (general.descripcion) generalBody.append(el('p', 'catalogo-ficha-texto', general.descripcion));
    if (hasValue(general.caracteristicas)) generalBody.append(valueList(general.caracteristicas));
    if (generalBody.childElementCount) blocks.push(fichaBlock('Información general', generalBody));

    if (!isCap && general.capacidad) {
      const capacidades = el('div', 'catalogo-ficha-grid catalogo-ficha-grid--2');
      capacidades.append(fichaItem('Capacidad', general.capacidad));
      blocks.push(fichaBlock('Capacidad', capacidades));
    }

    blocks.push(fichaBlock('Colores disponibles', colorChips(ficha.colores)));

    const pack = ficha.empaque || {};
    const packItems = [
      ['Tipo de empaque', pack.tipo], ['Contenido por empaque', pack.contenido],
      ['Peso del producto', pack.peso], ['Altura del empaque', pack.alto],
      ['Largo del empaque', pack.largo], ['Ancho del empaque', pack.ancho],
    ].filter(([, value]) => hasValue(value));
    if (packItems.length) {
      const grid = el('div', 'catalogo-ficha-grid');
      packItems.forEach(([label, value]) => grid.append(fichaItem(label, value)));
      blocks.push(fichaBlock('Información de empaque', grid));
    }

    fichaContainer.append(...blocks);
  };

  productSelect?.addEventListener('change', () => {
    renderFicha(categoryProducts[Number(productSelect.value)]);
  });

  const loadCategoryProducts = async (slug, title) => {
    const request = ++categoryRequest;
    categoryProducts = [];
    productSelect.hidden = true;
    productSelect.replaceChildren();
    fichaContainer.replaceChildren(el('p', 'catalogo-ficha-vacio', 'Cargando especificaciones…'));
    try {
      const response = await fetch(
        `/api/catalogo/productos/?categoria=${encodeURIComponent(slug)}`,
        {headers: {Accept: 'application/json'}, credentials: 'same-origin'},
      );
      if (!response.ok) throw new Error(response.status);
      const data = await response.json();
      if (request !== categoryRequest) return;
      categoryProducts = Array.isArray(data) ? data : data.results || [];
    } catch {
      if (request !== categoryRequest) return;
      fichaContainer.replaceChildren(
        el('p', 'catalogo-ficha-vacio', 'No pudimos cargar las especificaciones. Inténtalo de nuevo.'),
      );
      return;
    }

    if (!categoryProducts.length) {
      fichaContainer.replaceChildren(
        el('p', 'catalogo-ficha-vacio', 'No hay productos disponibles en esta categoría.'),
      );
      return;
    }
    categoryProducts.forEach((product, index) => {
      productSelect.append(new Option(product.nombre, String(index)));
    });
    productSelect.hidden = false;
    renderFicha(categoryProducts[0]);
  };

  categoryModal?.addEventListener('show.bs.modal', (event) => {
    const trigger = event.relatedTarget;
    if (!trigger) return;

    const titleText = trigger.dataset.categoryTitle || 'Categoría';
    document.getElementById('modalDetalleCategoriaTitulo').textContent = titleText;
    const image = document.getElementById('modalDetalleCategoriaImagen');
    categoryImage = trigger.dataset.categoryImage || '';
    image.src = categoryImage;
    image.alt = titleText;
    loadCategoryProducts(trigger.dataset.categorySlug || '', titleText);
  });

  document.querySelectorAll('[data-category-detail]').forEach((trigger) => {
    trigger.addEventListener('click', (event) => {
      event.preventDefault();
      event.stopPropagation();
      if (!categoryModal) return;
      window.bootstrap?.Modal.getOrCreateInstance(categoryModal).show(trigger);
    });
  });

  const requestModalElement = document.getElementById('modalSolicitudCatalogo');
  const requestForm = document.getElementById('solicitarCatalogoForm');
  const requestError = document.getElementById('catalogoSolicitudError');
  const requestSuccess = document.getElementById('catalogoSolicitudExito');
  const selectedProduct = document.getElementById('catalogoProductoSeleccionado');
  const productField = document.getElementById('solicitudProducto');
  const visibleProductField = document.getElementById('solicitudProductoVisible');
  const pageField = document.getElementById('solicitudPagina');
  const sendButton = document.getElementById('catalogoSolicitudEnviar');

  if (!requestModalElement || !requestForm || !window.bootstrap?.Modal) return;

  const requestModal = window.bootstrap.Modal.getOrCreateInstance(requestModalElement);
  const resetRequestState = () => {
    requestForm.reset();
    requestForm.classList.remove('d-none');
    requestSuccess?.classList.add('d-none');
    requestError?.classList.add('d-none');
    requestError.textContent = '';
    requestForm.querySelectorAll('[aria-invalid="true"]').forEach((field) => {
      field.removeAttribute('aria-invalid');
    });
    const recaptcha = window.grecaptcha;
    if (recaptcha && requestModalElement.querySelector('.g-recaptcha')) {
      recaptcha.reset();
    }
  };

  document.querySelectorAll('[data-catalog-request]').forEach((trigger) => {
    trigger.addEventListener('click', () => {
      resetRequestState();
      const productName = trigger.dataset.productName || 'Catálogo completo REMSA';
      productField.value = productName;
      visibleProductField.value = productName;
      selectedProduct.textContent = productName;
      pageField.value = `${window.location.pathname}${window.location.search}`;
      requestModal.show(trigger);
    });
  });

  requestForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (!requestForm.reportValidity()) return;

    if (requestForm.dataset.recaptchaEnabled === 'true'
      && (!window.grecaptcha || !window.grecaptcha.getResponse())) {
      requestError.textContent = 'Completa la validación de seguridad.';
      requestError.classList.remove('d-none');
      return;
    }

    productField.value = visibleProductField.value.trim();
    if (!productField.value) {
      visibleProductField.focus();
      return;
    }

    requestError.classList.add('d-none');
    requestError.textContent = '';
    sendButton.disabled = true;
    sendButton.setAttribute('aria-busy', 'true');
    const label = sendButton.querySelector('span');
    if (label) label.textContent = 'Enviando...';

    try {
      const response = await fetch(requestForm.action, {
        method: 'POST',
        body: new FormData(requestForm),
        headers: {'X-Requested-With': 'XMLHttpRequest'},
        credentials: 'same-origin',
      });
      const result = await response.json();
      if (!response.ok || !result.success) {
        const fieldMessages = Object.values(result.errors || {})
          .flat()
          .map((error) => error.message)
          .filter(Boolean);
        requestError.textContent = fieldMessages.length
          ? `${result.message} ${fieldMessages.join(' ')}`
          : (result.message || 'No se pudo enviar la solicitud. Intenta nuevamente.');
        requestError.classList.remove('d-none');
        return;
      }

      requestForm.classList.add('d-none');
      requestSuccess.classList.remove('d-none');
      requestSuccess.focus();
    } catch (error) {
      requestError.textContent = 'No se pudo conectar con el servidor. Revisa tu conexión e inténtalo nuevamente.';
      requestError.classList.remove('d-none');
    } finally {
      sendButton.disabled = false;
      sendButton.removeAttribute('aria-busy');
      const label = sendButton.querySelector('span');
      if (label) label.textContent = 'Solicitar catálogo';
    }
  });
});
