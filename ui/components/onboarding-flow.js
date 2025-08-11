// Copyright (c) 2024 LibreAssistant contributors.
// Licensed under the MIT License.

class LAOnboardingFlow extends HTMLElement {
  constructor() {
    super();
    this.step = 0;
    const shadow = this.attachShadow({ mode: 'open' });
    shadow.innerHTML = `
      <style>
        [hidden] { display: none; }
        .step { padding: var(--spacing-md); }
        .controls {
          display: flex;
          justify-content: space-between;
          margin-top: var(--spacing-md);
        }
        button {
          background-color: var(--color-primary);
          color: var(--color-background);
          font-family: var(--font-family-sans);
          font-size: var(--font-size-base);
          padding: var(--spacing-sm) var(--spacing-md);
          border: none;
          border-radius: var(--radius-md);
          cursor: pointer;
        }
        button[disabled] {
          opacity: 0.5;
          cursor: default;
        }
      </style>
      <div class="step" data-step="0">Step 1: Choose AI engine</div>
      <div class="step" data-step="1" hidden>Step 2: Select provider</div>
      <div class="step" data-step="2" hidden>Step 3: Configure plugins</div>
      <div class="step" data-step="3" hidden>Step 4: Review permissions</div>
      <div class="step" data-step="4" hidden>Step 5: Privacy briefing</div>
      <div class="step" data-step="5" hidden>Step 6: Completion</div>
      <div class="controls">
        <button id="back">Back</button>
        <button id="next">Next</button>
      </div>
    `;
  }

  connectedCallback() {
    this.backBtn = this.shadowRoot.getElementById('back');
    this.nextBtn = this.shadowRoot.getElementById('next');
    this.steps = this.shadowRoot.querySelectorAll('.step');
    this.update();
    this.backBtn.addEventListener('click', () => {
      if (this.step > 0) {
        this.step -= 1;
        this.update();
      }
    });
    this.nextBtn.addEventListener('click', () => {
      if (this.step < this.steps.length - 1) {
        this.step += 1;
        this.update();
      }
    });
  }

  update() {
    this.steps.forEach((el, idx) => {
      el.hidden = idx !== this.step;
    });
    this.backBtn.disabled = this.step === 0;
    this.nextBtn.disabled = this.step === this.steps.length - 1;
  }
}

customElements.define('la-onboarding-flow', LAOnboardingFlow);
