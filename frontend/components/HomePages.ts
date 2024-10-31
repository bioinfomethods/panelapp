import { css, html, LitElement, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";

@customElement("x-home-pages")
export default class HomePages extends LitElement {
  @property({ type: String })
  active: string;

  static styles = css`
    @media (width >= 782px) {
      .container {
        display: grid;
        grid-template-columns: 3fr 9fr;
        column-gap: 1.3em;
      }
    }

    @media (width < 782px) {
      .container {
        display: grid;
      }
    }

    .nav {
      width: 100%;
    }

    ul {
      list-style-type: none;
      margin: 0;
      padding: 0;
    }

    a {
      text-decoration: none;
      display: block;
      box-sizing: border-box;
      width: 100%;
      text-align: start;
      padding: 0;
      border: none;
      border-radius: 4px;
      padding: 8px 16px;
      background-color: rgb(0, 0, 0, 0);
      color: rgb(0, 124, 131);
    }

    a:hover {
      color: rgb(0, 159, 169);
    }

    a.active {
      background-color: rgb(0, 124, 131);
      color: white;
    }

    .page.hidden {
      display: none;
    }
  `;

  render() {
    const pages = [
      ["Introduction", "Home"],
      ["News", "News"],
      ["Navigating", "Navigate & Explore"],
      ["Reviewers", "Reviewers"],
      ["Guidelines", "Guidelines"],
      ["API", "API"],
      ["FAQs", "FAQs"],
      ["Content", "Contact, Content & Glossary"],
    ];

    return html`
      <div class="container">
        <div class="nav">
          <ul role="navlist">
            ${pages.map(([name, title]) => this.item(name, title))}
          </ul>
        </div>
        <div class="content">${pages.map(([name, _]) => this.page(name))}</div>
      </div>
    `;
  }

  item(name: string, title: string): TemplateResult {
    const active = name === this.active;

    return html`
      <li>
        <a
          id="${name}"
          href="#${name}"
          class="${classMap({ active })}"
          @click=${this.switchPage}
        >
          ${title}
        </a>
      </li>
    `;
  }

  switchPage(e: Event) {
    e.preventDefault();
    this.active = (e.target as Element).getAttribute("id");
    this.dispatchEvent(
      new CustomEvent("activechanged", {
        detail: { active: this.active },
        bubbles: true,
        composed: true,
      })
    );
  }

  page(name: string): TemplateResult {
    const active = name === this.active;

    return html`
      <div class="page ${classMap({ hidden: !active })}" role="tabpanel">
        <slot name="${name}"></slot>
      </div>
    `;
  }
}
