import { css, html, LitElement } from "lit";
import { customElement, property } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";

@customElement("x-badge")
export default class Badge extends LitElement {
  @property({ type: String })
  value: string;

  @property({ type: String })
  colour:
    | "blue"
    | "purple"
    | "pink"
    | "red"
    | "orange"
    | "yellow"
    | "green"
    | "teal"
    | "grey-500"
    | "grey-800" = "blue";

  static styles = css`
    .badge {
      padding-left: 8px;
      padding-right: 8px;
      color: #fff;
      font-weight: bold;
      display: inline-block;
      border-radius: 3px;
      font-size: 0.8em;
    }

    .blue {
      background-color: #0d6efd;
    }

    .purple {
      background-color: #6f42c1;
    }

    .pink {
      background-color: #d63384;
    }

    .red {
      background-color: #dc3545;
    }

    .orange {
      background-color: #fd7e14;
    }

    .yellow {
      background-color: #ffc107;
    }

    .green {
      background-color: #198754;
    }

    .teal {
      background-color: #20c997;
    }

    .grey-500 {
      background-color: #adb5bd;
    }

    .grey-600 {
      background-color: #6c757d;
    }

    .grey-700 {
      background-color: #495057;
    }
  `;

  render() {
    let classes = {};
    classes[this.colour] = true;

    return html`
      <span class="badge ${classMap(classes)}"> ${this.value} </span>
    `;
  }
}
