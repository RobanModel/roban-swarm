// Chunk 1 glue: wires the model + validator to a minimal DOM dump.
// Canvas, timeline, and side panels land in later chunks.

import { ShowModel } from "./model.js";
import { validateTiming, validateSafety } from "./validate.js";

const model = new ShowModel();

const dump = document.getElementById("dump");
const issues = document.getElementById("issues");
const examplePicker = document.getElementById("example-select");
const filePicker = document.getElementById("file-picker");

document.getElementById("btn-new").addEventListener("click", () => {
  model.newShow();
});

document.getElementById("btn-open").addEventListener("click", () => {
  filePicker.click();
});

document.getElementById("btn-save").addEventListener("click", () => {
  if (!model.show) {
    alert("Nothing to save — create or load a show first.");
    return;
  }
  const text = model.toJson();
  const blob = new Blob([text], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = slugify(model.show.name) + ".json";
  a.click();
  URL.revokeObjectURL(a.href);
  model.dirty = false;
  render();
});

filePicker.addEventListener("change", async (ev) => {
  const file = ev.target.files?.[0];
  if (!file) return;
  try {
    const text = await file.text();
    model.loadJson(text);
  } catch (e) {
    renderError(`Load failed: ${e.message}`);
  }
  filePicker.value = "";
});

examplePicker.addEventListener("change", async (ev) => {
  const path = ev.target.value;
  if (!path) return;
  try {
    const res = await fetch(path);
    if (!res.ok) throw new Error(`fetch ${path}: ${res.status}`);
    const text = await res.text();
    model.loadJson(text);
  } catch (e) {
    renderError(`Load failed: ${e.message}`);
  }
  examplePicker.value = "";
});

// Drag-drop onto window
window.addEventListener("dragover", (e) => {
  e.preventDefault();
});
window.addEventListener("drop", async (e) => {
  e.preventDefault();
  const file = e.dataTransfer?.files?.[0];
  if (!file) return;
  try {
    const text = await file.text();
    model.loadJson(text);
  } catch (err) {
    renderError(`Load failed: ${err.message}`);
  }
});

model.on("show-changed", render);
model.on("selection-changed", render);

function render() {
  if (!model.show) {
    issues.innerHTML = `<span class="ok">No show loaded.</span>`;
    dump.textContent = "—";
    return;
  }
  const timing = validateTiming(model.show);
  const safety = validateSafety(model.show);
  const parts = [];
  parts.push(
    `<span class="${timing.length ? "err" : "ok"}">Timing: ${
      timing.length ? `${timing.length} error(s)` : "OK"
    }</span>`,
  );
  parts.push(
    `<span class="${safety.length ? "warn" : "ok"}">Safety: ${
      safety.length ? `${safety.length} warning(s) (3m min)` : "OK"
    }</span>`,
  );
  parts.push(
    `<span class="hint"> &middot; ${model.show.tracks.length} track(s), ` +
      `${totalWaypoints(model.show)} waypoints, ${model.show.duration_s}s</span>`,
  );
  const listItems = [
    ...timing.map((e) => `<li class="err">${escapeHtml(e.msg)}</li>`),
    ...safety.map((w) => `<li class="warn">${escapeHtml(w.msg)}</li>`),
  ];
  issues.innerHTML =
    parts.join(" ") +
    (listItems.length ? `<ul>${listItems.join("")}</ul>` : "");

  dump.textContent = model.toJson();
}

function renderError(msg) {
  issues.innerHTML = `<span class="err">${escapeHtml(msg)}</span>`;
  dump.textContent = "—";
}

function totalWaypoints(show) {
  return show.tracks.reduce((a, t) => a + t.waypoints.length, 0);
}

function slugify(name) {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "") || "show";
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

// Expose for debugging in the console
window.__model = model;
