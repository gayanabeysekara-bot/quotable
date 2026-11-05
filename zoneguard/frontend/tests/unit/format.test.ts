import { describe, expect, it } from "vitest";

import { describeWindows, fmtBytes, fmtOffset, SEVERITY_LABEL } from "@/lib/format";

describe("format helpers", () => {
  it("labels severities exactly as specified", () => {
    expect(Object.values(SEVERITY_LABEL)).toEqual(["Informational", "Review Required", "High Priority", "Critical Review"]);
  });
  it("describes schedules including overnight windows", () => {
    expect(describeWindows([])).toBe("Always");
    expect(describeWindows([{ days: [0, 1, 2, 3, 4], start: "18:00", end: "06:00" }])).toBe("Mon, Tue, Wed, Thu, Fri 18:00–06:00 (overnight)");
    expect(describeWindows([{ days: [0, 1, 2, 3, 4, 5, 6], start: "08:00", end: "17:00" }])).toBe("Every day 08:00–17:00");
  });
  it("formats sizes and offsets", () => {
    expect(fmtBytes(8_131_690)).toBe("7.8 MB");
    expect(fmtOffset(75.25)).toBe("1:15.3");
    expect(fmtOffset(null)).toBe("—");
  });
});
