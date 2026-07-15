import assert from "node:assert/strict";
import test from "node:test";
import { pathToFileURL } from "node:url";
import { resolve } from "node:path";
import { readFile } from "node:fs/promises";
import { Window } from "happy-dom";

const browser = new Window({ url: "http://homeassistant.local:8123/" });
for (const name of [
  "window", "document", "customElements", "HTMLElement", "Element", "Node",
  "Document", "DocumentFragment", "ShadowRoot", "CSSStyleSheet", "MutationObserver",
  "CustomEvent", "Event",
]) {
  globalThis[name] = name === "window" ? browser : browser[name];
}
globalThis.requestAnimationFrame = (callback) => setTimeout(callback, 0);
globalThis.cancelAnimationFrame = clearTimeout;

const consoleErrors = [];
const originalError = console.error;
console.error = (...args) => consoleErrors.push(args);
await import(`${pathToFileURL(resolve("custom_components/urdb/frontend/urdb-card.js"))}?test=${Date.now()}`);
console.error = originalError;

test("authors the card exclusively through the Lit render pipeline", async () => {
  const source = await readFile("custom_components/urdb/frontend/src/urdb-card.js", "utf8");
  assert.match(source, /class URDBCard extends LitElement/);
  assert.match(source, /render\(\)/);
  assert.match(source, /html`<ha-card>/);
  assert.doesNotMatch(source, /innerHTML/);
  assert.doesNotMatch(source, /extends HTMLElement/);
});

const status = {
  state: "ok",
  attributes: {
    current_version: "routing-1",
    latest_version: "routing-2",
    has_update: true,
    checked_at: "2026-07-15T00:00:00Z",
    github_status: "ok",
  },
};

const makeHass = (calls = []) => ({
  locale: { language: "en" },
  states: {
    "sensor.urdb_status": status,
    "sensor.urdb_changes": { state: "1", attributes: { changes: ["YouTube"] } },
  },
  callService: async (...args) => calls.push(args),
});

test("registers and creates the Lit card in the Home Assistant picker without runtime errors", async () => {
  const Card = customElements.get("urdb-card");
  assert.ok(Card);
  assert.ok(customElements.get("urdb-card-editor"));
  assert.equal(window.customCards.length, 1);
  assert.deepEqual(
    { type:window.customCards[0].type, name:window.customCards[0].name, preview:window.customCards[0].preview },
    { type:"urdb-card", name:"Universal Routing Database", preview:true },
  );

  const card = document.createElement("urdb-card");
  card.setConfig(Card.getStubConfig());
  card.hass = makeHass();
  document.body.append(card);
  await card.updateComplete;

  assert.ok(card.shadowRoot);
  assert.match(card.shadowRoot.textContent, /Universal Routing Database/);
  assert.match(card.shadowRoot.textContent, /routing-1/);
  assert.equal(consoleErrors.length, 0);
  assert.equal(Card.getConfigElement().localName, "urdb-card-editor");
});

test("renders status and invokes every Home Assistant action through Lit events", async () => {
  const calls = [];
  const card = document.createElement("urdb-card");
  card.setConfig(customElements.get("urdb-card").getStubConfig());
  card.hass = makeHass(calls);
  document.body.append(card);
  await card.updateComplete;

  assert.match(card.shadowRoot.textContent, /routing-2/);
  assert.match(card.shadowRoot.textContent, /YouTube/);
  assert.match(card.shadowRoot.textContent, /Integration: v0.4.1/);
  assert.match(card.shadowRoot.textContent, /Routing update available/);
  assert.ok(card.shadowRoot.querySelector("ha-card"));
  assert.ok(card.shadowRoot.querySelector("ha-progress-button"));

  for (const [action, entityId] of [
    ["check", "button.check"], ["update", "button.update"], ["restart", "button.restart"],
  ]) {
    card._operation = null;
    await card.updateComplete;
    card.shadowRoot.querySelector(`ha-progress-button[data-action="${action}"]`).click();
    await new Promise((resolve) => setTimeout(resolve, 0));
    assert.deepEqual(calls.at(-1), ["button", "press", { entity_id:entityId }]);
    assert.equal(card._lastAction.action, action);
    assert.equal(card._lastAction.state, "completed");
  }
});

test("renders progress and rate-limit state through the Lit template", async () => {
  const card = document.createElement("urdb-card");
  card.setConfig(customElements.get("urdb-card").getStubConfig());
  card.hass = makeHass();
  card.hass.states["sensor.urdb_status"] = {
    state:"ok",
    attributes:{ ...status.attributes, current_version:"routing-2", has_update:false, github_status:"rate_limited" },
  };
  card._operation = "update";
  card._progress = 42;
  document.body.append(card);
  await card.updateComplete;

  assert.match(card.shadowRoot.textContent, /Cached release data is being used/);
  assert.match(card.shadowRoot.textContent, /System is up to date/);
  const progress = card.shadowRoot.querySelector('ha-progress-button[data-action="update"]');
  assert.ok(progress);
  assert.equal(progress.progress, true);
  assert.match(card.shadowRoot.textContent, /42%/);
  assert.equal(card.shadowRoot.querySelector("ha-linear-progress"), null);
});
