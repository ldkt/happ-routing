import assert from "node:assert/strict";
import test from "node:test";
import { pathToFileURL } from "node:url";
import { resolve } from "node:path";

const registry = new Map();
class HTMLElementStub {
  attachShadow() {
    this.shadowRoot = {
      innerHTML: "",
      querySelector: () => null,
      querySelectorAll: () => [],
    };
  }
}

globalThis.HTMLElement = HTMLElementStub;
globalThis.customElements = {
  define: (name, constructor) => registry.set(name, constructor),
  get: (name) => registry.get(name),
};
globalThis.document = { createElement: (name) => ({ localName: name }) };
globalThis.window = { customCards: [], setTimeout: () => 1 };

await import(pathToFileURL(resolve("custom_components/urdb/frontend/urdb-card.js")));

test("registers a visual-editor card in the Home Assistant picker", () => {
  const Card = registry.get("urdb-card");
  assert.ok(Card);
  assert.ok(registry.get("urdb-card-editor"));
  assert.equal(window.customCards.length, 1);
  assert.equal(window.customCards[0].type, "urdb-card");
  assert.equal(Card.getConfigElement().localName, "urdb-card-editor");
});

test("renders first-class update status and invokes all Home Assistant buttons", async () => {
  const calls = [];
  const Card = registry.get("urdb-card");
  const card = new Card();
  card.setConfig(Card.getStubConfig());
  card.hass = {
    locale: { language: "en" },
    states: {
      "sensor.urdb_status": {
        state: "ok",
        attributes: {
          current_version: "routing-1",
          latest_version: "routing-2",
          has_update: true,
          checked_at: "2026-07-15T00:00:00Z",
          github_status: "ok",
        },
      },
      "sensor.urdb_changes": {
        state: "1",
        attributes: { changes: ["YouTube"] },
      },
    },
    callService: async (...args) => calls.push(args),
  };

  assert.match(card.shadowRoot.innerHTML, /routing-1/);
  assert.match(card.shadowRoot.innerHTML, /routing-2/);
  assert.match(card.shadowRoot.innerHTML, /YouTube/);
  assert.match(card.shadowRoot.innerHTML, /Universal Routing Database/);
  assert.match(card.shadowRoot.innerHTML, /Integration: v0\.3\.0/);
  assert.match(card.shadowRoot.innerHTML, /Routing update available/);
  for (const [action, entityId] of [
    ["check", "button.check"],
    ["update", "button.update"],
    ["restart", "button.restart"],
  ]) {
    card._operation = null;
    await card._run(action);
    assert.deepEqual(calls.at(-1), ["button", "press", { entity_id: entityId }]);
    assert.equal(card._progress, 100);
    assert.equal(card._lastAction.action, action);
    assert.equal(card._lastAction.state, "completed");
    assert.match(card.shadowRoot.innerHTML, /ha-linear-progress/);
  }
});

test("treats GitHub rate limiting as healthy cached operation", () => {
  const Card = registry.get("urdb-card");
  const card = new Card();
  card.setConfig(Card.getStubConfig());
  card.hass = {
    locale: { language: "en" },
    states: {
      "sensor.urdb_status": {
        state: "ok",
        attributes: {
          current_version: "routing-2",
          latest_version: "routing-2",
          has_update: false,
          checked_at: "2026-07-15T00:00:00Z",
          github_status: "rate_limited",
        },
      },
      "sensor.urdb_changes": { state: "0", attributes: { changes: [] } },
    },
    callService: async () => {},
  };

  assert.match(card.shadowRoot.innerHTML, /Cached release data is being used/);
  assert.match(card.shadowRoot.innerHTML, /System is up to date/);
  assert.match(card.shadowRoot.innerHTML, /health warn/);
  assert.doesNotMatch(card.shadowRoot.innerHTML, /health bad/);
});
