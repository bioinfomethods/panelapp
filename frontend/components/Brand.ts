import { html, LitElement } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("x-brand")
export default class Brand extends LitElement {
  @property({ type: String })
  title: string;

  render() {
    return html`
      <div class="container">
        <h1>${this.title}</h1>
        <p class="lead col-lg-11 fs-4">
          A crowdsourcing tool to allow gene panels to be shared, downloaded,
          viewed and evaluated by the Scientific Community
        </p>
      </div>
    `;
  }

  // Render into the DOM instead of the Shadow DOM to allow
  // bootstrap styling and javascript to work
  // https://stackoverflow.com/questions/56376475/how-to-implement-bootstrap-navbar-as-component-in-lit-html-lit-element/58462176#58462176
  protected createRenderRoot(): HTMLElement | DocumentFragment {
    return this;
  }
}
