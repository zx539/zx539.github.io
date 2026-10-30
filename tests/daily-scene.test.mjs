import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("../assets/js/daily-scene.js", import.meta.url), "utf8");
const { beijingDay, selectScenes } = await import(`data:text/javascript;base64,${Buffer.from(source).toString("base64")}`);
const at = (time) => new Date(time);
const records = (...dates) => dates.map((date) => ({ date }));
const dates = (items) => items.map((item) => item.date);

test("Beijing's calendar changes at 16:00 UTC, independent of local timezone", () => {
  const before = at("2026-10-30T15:59:59Z");
  const after = at("2026-10-30T16:00:00Z");
  assert.equal(beijingDay(after) - beijingDay(before), 1);
  const items = records("2026-10-24", "2026-10-25", "2026-10-30");
  assert.deepEqual(dates(selectScenes(items, before)), ["2026-10-30", "2026-10-25", "2026-10-24"]);
  assert.deepEqual(dates(selectScenes(items, after)), ["2026-10-30", "2026-10-25"]);
});

test("the seven-day window includes today and day six, excluding day seven and future records", () => {
  const items = records("2026-10-23", "2026-10-31", "2026-10-24", "2026-10-30");
  assert.deepEqual(dates(selectScenes(items, at("2026-10-30T12:00:00+08:00"))), ["2026-10-30", "2026-10-24"]);
  assert.deepEqual(dates(items), ["2026-10-23", "2026-10-31", "2026-10-24", "2026-10-30"]);
});

test("falls back to only the latest past record, never to future records", () => {
  const now = at("2026-10-30T12:00:00+08:00");
  assert.deepEqual(dates(selectScenes(records("2026-10-01", "2026-10-20", "2026-11-01"), now)), ["2026-10-20"]);
  assert.deepEqual(selectScenes(records("2026-11-01"), now), []);
  assert.deepEqual(selectScenes([], now), []);
});

test("handles year boundaries, leap days and invalid dates", () => {
  assert.deepEqual(
    dates(selectScenes(records("2025-12-25", "2025-12-26", "2026-01-01"), at("2026-01-01T00:00:00+08:00"))),
    ["2026-01-01", "2025-12-26"],
  );
  assert.deepEqual(
    dates(selectScenes(records("2024-02-29", "2024-02-30", "bad-date", "2024-02-23"), at("2024-03-01T00:00:00+08:00"))),
    ["2024-02-29"],
  );
});
