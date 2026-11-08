import { describe, expect, it } from "vitest";

import { quietDays } from "./StatusBadge";

const now = new Date("2026-11-08T12:00:00Z");
const daysAgo = (n: number) => new Date(now.getTime() - n * 86_400_000).toISOString();

describe("quietDays", () => {
  it("flags an interview process without news for two weeks", () => {
    expect(quietDays({ current_status: "next_round", last_event_at: daysAgo(20) }, now)).toBe(20);
    expect(quietDays({ current_status: "interview_invite", last_event_at: daysAgo(14) }, now)).toBe(14);
  });

  it("stays silent for recent news and for other statuses", () => {
    expect(quietDays({ current_status: "next_round", last_event_at: daysAgo(5) }, now)).toBeNull();
    expect(quietDays({ current_status: "rejection", last_event_at: daysAgo(60) }, now)).toBeNull();
    expect(quietDays({ current_status: "next_round", last_event_at: null }, now)).toBeNull();
  });
});
