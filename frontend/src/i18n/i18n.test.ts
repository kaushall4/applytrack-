import { describe, expect, it } from "vitest";

import { ALL_INTENTS, ALL_STATUSES, INTENT_META, STATUS_META } from "../lib/status";
import { de } from "./de";
import { en } from "./en";

/** Every key path of a dictionary, e.g. "table.quietTag". */
function keys(obj: object, prefix = ""): string[] {
  return Object.entries(obj).flatMap(([k, v]) =>
    v && typeof v === "object" ? keys(v, `${prefix}${k}.`) : [`${prefix}${k}`],
  );
}

describe("translations", () => {
  it("German and English have exactly the same texts", () => {
    expect(keys(de).sort()).toEqual(keys(en).sort());
  });

  it("every status and intent has a label and colours", () => {
    for (const s of ALL_STATUSES) {
      expect(de.status[s]).toBeTruthy();
      expect(en.status[s]).toBeTruthy();
      expect(STATUS_META[s].hex).toMatch(/^#[0-9a-f]{6}$/i);
    }
    for (const i of ALL_INTENTS) {
      expect(de.intent[i]).toBeTruthy();
      expect(INTENT_META[i]).toBeDefined();
    }
  });

  it("uses Swiss German spelling (no ß)", () => {
    const texts = JSON.stringify(de, (_k, v) => (typeof v === "function" ? v(2, 5) : v));
    expect(texts).not.toContain("ß");
  });
});
