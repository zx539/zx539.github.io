const dialog = document.querySelector('[data-award-dialog]');

if (dialog && typeof dialog.showModal === 'function') {
  const title = dialog.querySelector('#award-dialog-title');
  const image = dialog.querySelector('[data-award-image]');
  const original = dialog.querySelector('[data-award-original]');
  const status = dialog.querySelector('[data-award-status]');
  let trigger;

  document.querySelectorAll('[data-award-preview]').forEach((link) => {
    link.addEventListener('click', (event) => {
      if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      trigger = link;
      title.textContent = link.dataset.awardTitle;
      image.alt = `${link.dataset.awardTitle}荣誉证书`;
      status.hidden = true;
      image.hidden = false;
      image.src = link.href;
      original.href = link.dataset.awardFile;
      dialog.showModal();
      document.documentElement.classList.add('award-modal-open');
    });
  });

  image.addEventListener('error', () => {
    image.hidden = true;
    status.hidden = false;
  });
  dialog.querySelector('[data-award-close]').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', (event) => {
    if (event.target !== dialog) return;
    const rect = dialog.getBoundingClientRect();
    if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) dialog.close();
  });
  dialog.addEventListener('close', () => {
    document.documentElement.classList.remove('award-modal-open');
    image.removeAttribute('src');
    trigger?.focus({ preventScroll: true });
  });
}
