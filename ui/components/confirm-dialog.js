// Copyright (c) 2024 LibreAssistant contributors.
// Licensed under the MIT License.

// Utility to show a confirmation modal using <la-modal-dialog>.
// Returns a Promise<boolean> that resolves to true when the user confirms.

window.showConsentModal = function (message) {
  return new Promise(resolve => {
    const dialog = document.createElement('la-modal-dialog');
    dialog.innerHTML = `
      <span slot="title">Confirm</span>
      <p style="margin: 0 0 var(--spacing-md) 0; font-family: var(--font-family-sans); line-height: var(--line-height-base);">${message}</p>
      <div style="margin-top: var(--spacing-md); display:flex; justify-content:flex-end; gap: var(--spacing-sm);">
        <button id="cancel" style="
          background-color: var(--color-surface);
          color: var(--color-text);
          font-family: var(--font-family-sans);
          font-size: var(--font-size-base);
          padding: var(--spacing-sm) var(--spacing-md);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-sm);
          cursor: pointer;
        ">Cancel</button>
        <button id="ok" style="
          background-color: var(--color-primary);
          color: var(--color-background);
          font-family: var(--font-family-sans);
          font-size: var(--font-size-base);
          font-weight: var(--font-weight-bold);
          padding: var(--spacing-sm) var(--spacing-md);
          border: none;
          border-radius: var(--radius-sm);
          cursor: pointer;
        ">OK</button>
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
