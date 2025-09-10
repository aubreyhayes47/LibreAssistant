// Copyright (c) 2024 LibreAssistant contributors.
// Licensed under the MIT License.

class LABillOfMaterials extends HTMLElement {
  constructor() {
    super();
    const shadow = this.attachShadow({ mode: 'open' });
    shadow.innerHTML = `
      <style>
        :host {
          display: block;
          font-family: var(--font-family-sans);
        }
        h2 {
          font-size: var(--font-size-lg);
          font-weight: var(--font-weight-bold);
          line-height: var(--line-height-tight);
          color: var(--color-text);
          margin: 0 0 var(--spacing-lg) 0;
        }
        h3 {
          font-size: var(--font-size-base);
          font-weight: var(--font-weight-bold);
          line-height: var(--line-height-tight);
          color: var(--color-text);
          margin: var(--spacing-md) 0 var(--spacing-sm) 0;
        }
        section {
          margin-bottom: var(--spacing-lg);
        }
        ul { 
          list-style: disc; 
          padding-left: var(--spacing-md);
          margin: 0;
        }
        li {
          font-size: var(--font-size-base);
          line-height: var(--line-height-base);
          color: var(--color-text);
          margin-bottom: var(--spacing-xs);
        }
      </style>
      <h2>Bill of Materials</h2>
      <section>
        <h3>Dependencies</h3>
        <ul id="deps"></ul>
      </section>
      <section>
        <h3>Models</h3>
        <ul id="models"></ul>
      </section>
      <section>
        <h3>Datasets</h3>
        <ul id="datasets"></ul>
      </section>
    `;
  }

  async connectedCallback() {
    try {
      const resp = await fetch('/api/v1/bom');
      if (!resp.ok) return;
      const data = await resp.json();
      const deps = this.shadowRoot.getElementById('deps');
      data.dependencies.forEach(d => {
        const li = document.createElement('li');
        li.textContent = d;
        deps.appendChild(li);
      });
      const models = this.shadowRoot.getElementById('models');
      data.models.forEach(m => {
        const li = document.createElement('li');
        li.textContent = m;
        models.appendChild(li);
      });
      const datasets = this.shadowRoot.getElementById('datasets');
      data.datasets.forEach(ds => {
        const li = document.createElement('li');
        li.textContent = ds;
        datasets.appendChild(li);
      });
    } catch (err) {
      // ignore errors for now
    }
  }
}

customElements.define('la-bill-of-materials', LABillOfMaterials);
