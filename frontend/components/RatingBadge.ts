import { css, html, LitElement } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("x-rating-badge")
export default class RatingBadge extends LitElement {
  @property({ type: String })
  rating: string;

  @property({ type: Boolean })
  ready?: boolean = false;

  @property({ type: Boolean })
  block?: boolean = false;

  static styles = css`
    .badge {
      padding: 5px 8px;
      color: #fff;
      font-weight: bold;
      display: inline-block;
      border-radius: 3px;
      font-size: 1rem;
      text-transform: capitalize;
    }

    .ready {
      opacity: 0.8;
      font-size: 14px;
    }

    .block {
      display: block;
    }

    .grey {
      background-color: #ccc;
    }

    .red {
      background-color: #d9534f;
    }

    .amber {
      background-color: #f0ad4e;
    }

    .green {
      background-color: #3fad46;
    }
  `;

  render() {
    const ready = html`
      <br />
      <span class="ready">Ready</span>
    `;
    return html`
      <span class="badge ${this.rating} ${this.block ? "block" : ""}">
        ${this.rating} ${this.ready ? ready : ""}
      </span>
    `;
  }
}
