// Copyright (c) 2024 LibreAssistant contributors.
// Licensed under the MIT License.

// Utility to show a confirmation modal using <la-modal-dialog>.
// Returns a Promise<boolean> that resolves to true when the user confirms.

window.showConsentModal = function (message) {
  return new Promise(resolve => {
    const dialog = document.createElement('la-modal-dialog');
    dialog.innerHTML = `
      <style>
        .consent-actions {
          margin-top: var(--spacing-md);
          display: flex;
          justify-content: flex-end;
          gap: var(--spacing-sm);
        }
        .consent-actions button {
          font-family: var(--font-family-sans);
          font-size: var(--font-size-base);
          padding: var(--spacing-xs) var(--spacing-sm);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-sm);
          cursor: pointer;
          background: var(--color-background);
          color: var(--color-text);
        }
        .consent-actions button#ok {
          background-color: var(--color-primary);
          color: var(--color-background);
          border-color: var(--color-primary);
        }
        .consent-actions button:hover {
          opacity: 0.9;
        }
      </style>
      <span slot="title">Confirm</span>
      <p>${message}</p>
      <div class="consent-actions">
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
