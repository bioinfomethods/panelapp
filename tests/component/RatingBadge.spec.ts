import { expect, test } from "@sand4rt/experimental-ct-web";
import RatingBadge from "../../frontend/components/RatingBadge";

test.describe("visual", () => {
  test("primary", async ({ mount }) => {
    const component = await mount(RatingBadge, { props: { rating: "green" } });
    await expect(component).toHaveScreenshot();
  });

  test("ready", async ({ mount }) => {
    const component = await mount(RatingBadge, {
      props: { rating: "green", ready: true },
    });
    await expect(component).toHaveScreenshot();
  });

  test("block", async ({ mount }) => {
    const component = await mount(RatingBadge, {
      props: { rating: "green", block: true },
    });
    await expect(component).toHaveScreenshot();
  });
});
