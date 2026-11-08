// @vitest-environment jsdom
import { describe, expect, it } from "vitest";

import { cleanExcerpt } from "./format";

describe("cleanExcerpt", () => {
  it("decodes HTML entities", () => {
    expect(cleanExcerpt("Thanks&nbsp;for applying &amp; good luck")).toBe(
      "Thanks for applying & good luck",
    );
  });

  it("drops inline-image markers and collapses whitespace", () => {
    expect(cleanExcerpt("[cid:image002.gif@01DD]  We want\n\nto meet you!")).toBe(
      "We want to meet you!",
    );
  });

  it("drops a stray leading number from mail headers", () => {
    expect(cleanExcerpt("96 Dear Kaushall, thank you")).toBe("Dear Kaushall, thank you");
    // …but keeps numbers that belong to the sentence.
    expect(cleanExcerpt("3 interviews are scheduled")).toBe("3 interviews are scheduled");
  });

  it("never turns markup into live elements", () => {
    expect(cleanExcerpt('<img src=x onerror="alert(1)">Hello')).toBe("Hello");
  });
});
