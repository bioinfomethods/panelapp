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

  @property({ type: String })
  text: "short" | "verbose" = "short";

  static styles = css`
    .badge {
      padding: 5px 8px;
      color: #fff;
      font-weight: bold;
      display: inline-block;
      border-radius: 3px;
      font-size: 1rem;
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
    const text =
      this.text === "short"
        ? { green: "Green", amber: "Amber", red: "Red", grey: "Grey" }[
            this.rating
          ]
        : {
            green: "Green List (high evidence)",
            amber: "Amber List (moderate evidence)",
            red: "Red List (low evidence)",
            grey: "No list",
          }[this.rating];
    return html`
      <span class="badge ${this.rating} ${this.block ? "block" : ""}">
        ${text} ${this.ready ? ready : ""}
      </span>
    `;
  }
}
