const DAY = 24 * 60 * 60 * 1000;
const BEIJING_OFFSET = 8 * 60 * 60 * 1000;

export function beijingDay(now = new Date()) {
  return Math.floor((now.getTime() + BEIJING_OFFSET) / DAY);
}

function recordDay(date) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) return NaN;
  const timestamp = Date.parse(`${date}T00:00:00+08:00`);
  if (!Number.isFinite(timestamp)) return NaN;
  if (new Date(timestamp + BEIJING_OFFSET).toISOString().slice(0, 10) !== date) return NaN;
  return beijingDay(new Date(timestamp));
}

// Calendar days in Beijing, including today and the preceding six days.
// Older records remain in the page so the window can advance without a rebuild.
export function selectScenes(records, now = new Date()) {
  const today = beijingDay(now);
  const published = records
    .filter((record) => recordDay(record.date) <= today)
    .sort((a, b) => b.date.localeCompare(a.date));
  const recent = published.filter((record) => recordDay(record.date) >= today - 6);
  return recent.length ? recent : published.slice(0, 1);
}

export function initDailyScene(root) {
  const records = Array.from(root.querySelectorAll("[data-scene-date]"), (element) => ({
    date: element.dataset.sceneDate,
    element,
  }));
  const controls = root.querySelector("[data-scene-controls]");
  const counter = root.querySelector("[data-scene-counter]");
  const toggle = root.querySelector("[data-scene-toggle]");
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  let selected = [];
  let index = 0;
  let day = null;
  let timer;
  let paused = reducedMotion.matches;
  let hovered = false;
  let focused = root.contains(document.activeElement);

  function syncTimer() {
    window.clearTimeout(timer);
    const playing = selected.length > 1 && !paused && !hovered && !focused && !document.hidden;
    counter.setAttribute("aria-live", playing ? "off" : "polite");
    toggle.textContent = paused ? "继续轮播" : "暂停轮播";
    toggle.setAttribute("aria-pressed", String(paused));
    if (playing) timer = window.setTimeout(() => show(index + 1), 5000);
  }

  function show(nextIndex) {
    index = selected.length ? (nextIndex + selected.length) % selected.length : 0;
    records.forEach((record) => { record.element.hidden = true; });
    if (selected[index]) selected[index].element.hidden = false;
    controls.hidden = selected.length < 2;
    root.querySelector("[data-scene-empty]").hidden = selected.length > 0;
    counter.textContent = selected.length ? `${index + 1} / ${selected.length}` : "";
    syncTimer();
  }

  function refresh() {
    const now = new Date();
    if (day === beijingDay(now)) return;
    day = beijingDay(now);
    selected = selectScenes(records, now);
    const recent = selected.some((record) => recordDay(record.date) >= day - 6);
    root.querySelector("[data-scene-description]").textContent = selected.length && !recent
      ? "近七天暂无新照片，回顾最近一次记录。"
      : "近七天的生活片段，留住身边的小风景。";
    show(0);
  }

  root.querySelector("[data-scene-prev]").addEventListener("click", () => show(index - 1));
  root.querySelector("[data-scene-next]").addEventListener("click", () => show(index + 1));
  toggle.addEventListener("click", () => { paused = !paused; syncTimer(); });
  root.addEventListener("mouseenter", () => { hovered = true; syncTimer(); });
  root.addEventListener("mouseleave", () => { hovered = false; syncTimer(); });
  root.addEventListener("focusin", () => { focused = true; syncTimer(); });
  root.addEventListener("focusout", (event) => {
    focused = root.contains(event.relatedTarget);
    syncTimer();
  });
  root.addEventListener("keydown", (event) => {
    if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
      event.preventDefault();
      show(index + (event.key === "ArrowRight" ? 1 : -1));
    }
  });
  document.addEventListener("visibilitychange", () => { refresh(); syncTimer(); });
  reducedMotion.addEventListener("change", (event) => {
    if (event.matches) paused = true;
    syncTimer();
  });
  // Also recheck the calendar for visitors who keep this page open overnight.
  window.setInterval(refresh, 60_000);
  refresh();
}

if (typeof document !== "undefined") {
  document.querySelectorAll("[data-daily-scene]").forEach(initDailyScene);
}
