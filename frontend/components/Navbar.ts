import { LitElement, html } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("x-navbar")
export default class Navbar extends LitElement {
  @property({ type: String })
  username?: string;

  @property({ type: String })
  auth: string;

  @property({ type: Boolean })
  hideItems: boolean = false;

  @property({ type: Boolean })
  cognito: boolean = false;

  render() {
    const loginItems = html`
      <ul class="navbar-nav ms-auto">
        <li class="nav-item">
          <a
            class="nav-link nav-panelapp rounded mx-2 my-1"
            href="/accounts/login/?next=/"
            >Log in</a
          >
        </li>
        <li class="nav-item">
          <a
            class="nav-link nav-panelapp rounded mx-2 my-1"
            href="/accounts/registration/"
            >Register</a
          >
        </li>
      </ul>
    `;
    const cognitoItems = html`
      <ul class="navbar-nav ms-auto">
        <li class="nav-item">
          <a
            class="nav-link nav-panelapp rounded mx-2 my-1"
            href="/accounts/login/"
            >Log in</a
          >
        </li>
      </ul>
    `;
    const anonymousItems = this.cognito ? cognitoItems : loginItems;
    const authenticatedItems = html`
      <ul class="navbar-nav ms-auto">
        <li class="nav-item">
          <a
            class="nav-link nav-panelapp rounded mx-2 my-1"
            href="/accounts/profile/"
            ><strong>${this.username}</strong></a
          >
        </li>
        <li class="nav-item">
          <a
            class="nav-link nav-panelapp rounded mx-2 my-1"
            href="/accounts/logout/"
            >Log out</a
          >
        </li>
      </ul>
    `;
    const accountItems =
      this.auth === "anonymous" ? anonymousItems : authenticatedItems;

    const gelItems = html`
      <li class="nav-item">
        <a
          class="nav-link nav-panelapp rounded mx-2 my-1"
          href="/panels/create/"
          >Add panel</a
        >
      </li>
      <li class="nav-item">
        <a class="nav-link nav-panelapp rounded mx-2 my-1" href="/panels/admin/"
          >Import panel</a
        >
      </li>
      <li class="nav-item dropdown">
        <a
          href="#"
          class="nav-link nav-panelapp dropdown-toggle rounded mx-2 my-1"
          data-bs-toggle="dropdown"
          role="button"
          aria-expanded="false"
          >Resources <span class="caret"></span
        ></a>
        <ul class="dropdown-menu">
          <li>
            <a class="dropdown-item" href="/panels/download_genes/"
              >Download all genes</a
            >
          </li>
          <li>
            <a class="dropdown-item" href="/panels/download_strs/"
              >Download all STRs</a
            >
          </li>
          <li>
            <a class="dropdown-item" href="/panels/download_regions/"
              >Download all Regions</a
            >
          </li>
          <li>
            <a class="dropdown-item" href="/panels/download_panel/"
              >Download all panels</a
            >
          </li>
        </ul>
      </li>
    `;

    const items = html`
      <button
        class="navbar-toggler"
        type="button"
        data-bs-toggle="collapse"
        data-bs-target="#navbarContent"
        aria-controls="navbarContent"
        aria-expanded="false"
        aria-label="Toggle navigation"
      >
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" id="navbarContent">
        <ul class="navbar-nav">
          <li class="nav-item">
            <a class="nav-link nav-panelapp rounded mx-2 my-1" href="/panels/"
              >Panels</a
            >
          </li>
          <li class="nav-item">
            <a
              class="nav-link nav-panelapp rounded mx-2 my-1"
              href="/panels/entities/"
              >Genes and Entities</a
            >
          </li>
          <li class="nav-item">
            <a
              class="nav-link nav-panelapp rounded mx-2 my-1"
              href="/panels/activity/"
              >Activity</a
            >
          </li>
          ${this.auth === "gel" ? gelItems : ""}
        </ul>
        ${accountItems}
      </div>
    `;

    return html`
      <nav class="navbar navbar-expand-md bg-primary navbar-dark overflow-x">
        <div class="container">
          <a class="navbar-brand" href="/">PanelApp</a>
          ${this.hideItems ? "" : items}
        </div>
      </nav>
    `;
  }

  // Render into the DOM instead of the Shadow DOM to allow
  // bootstrap styling and javascript to work
  // https://stackoverflow.com/questions/56376475/how-to-implement-bootstrap-navbar-as-component-in-lit-html-lit-element/58462176#58462176
  protected createRenderRoot(): HTMLElement | DocumentFragment {
    return this;
  }
}
