// Copyright (c) 2024 LibreAssistant contributors.
// Licensed under the MIT License.

// Utility to show a confirmation modal using <la-modal-dialog>.
// Returns a Promise<boolean> that resolves to true when the user confirms.

window.showConsentModal = function (message) {
  return new Promise(resolve => {
    const dialog = document.createElement('la-modal-dialog');
    dialog.innerHTML = `
      <span slot="title">Confirm</span>
      <p>${message}</p>
      <div style="margin-top: var(--spacing-md); display:flex; justify-content:flex-end; gap: var(--spacing-sm);">
        <button id="cancel">Cancel</button>
        <button id="ok">OK</button>
      </div>
    `;
    const cleanup = (result) => {
      resolve(result);
      dialog.remove();
    };
    dialog.addEventListener('keydown', e => {
      if (e.key === 'Escape') cleanup(false);
    });
    dialog.shadowRoot.querySelector('.backdrop').addEventListener('click', () => cleanup(false));
    dialog.shadowRoot.querySelector('.close').addEventListener('click', () => cleanup(false));
    dialog.querySelector('#cancel').addEventListener('click', () => cleanup(false));
    dialog.querySelector('#ok').addEventListener('click', () => cleanup(true));
    document.body.appendChild(dialog);
    dialog.setAttribute('open', '');
  });
};

export {};
