import { css, html, LitElement } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("x-facet")
export default class Facet extends LitElement {
  @property({ type: String })
  label: string;

  @property({ type: Boolean })
  open: boolean = false;

  static styles = css`
    .container {
      margin-left: 4px;
      margin-right: 4px;
      padding-top: 4px;
      padding-bottom: 4px;
      width: 100%;
    }

    .closed {
      display: none;
    }

    .label {
      display: block;
      font-size: 1.17em;
      font-weight: bold;
      margin-top: 2px;
      margin-bottom: 2px;
    }

    .button {
      display: flex;
      align-items: center;
      padding-top: 4px;
      padding-bottom: 4px;
      background-color: white;
      border: none;
      border-radius: 5px;
      width: 100%;
      height: 100%;
    }

    .button:hover {
      background-color: rgba(0, 124, 131, 0.1);
    }

    .button:active {
      background-color: rgba(0, 124, 131, 0.25);
    }
  `;

  render() {
    const arrow = this.open
      ? html`<x-arrow-down width="24px" height="24px"></x-arrow-down>`
      : html`<x-arrow-right width="24px" height="24px"></x-arrow-right>`;

    return html`
      <div class="container">
        <button class="button" type="button" @click="${this._toggle}">
          ${arrow}
          <span class="label">${this.label}</span>
        </button>
        <div class="${this.open ? "" : "closed"}">
          <slot></slot>
        </div>
      </div>
    `;
  }

  _toggle(e: Event) {
    this.open = !this.open;
  }
}
