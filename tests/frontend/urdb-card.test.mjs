import assert from "node:assert/strict";
import test from "node:test";
import { pathToFileURL } from "node:url";
import { resolve } from "node:path";

const registry = new Map();
class HTMLElementStub {
  attachShadow() {
    this.shadowRoot = {
      innerHTML: "",
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

test("renders status and invokes all Home Assistant button entities", async () => {
  const calls = [];
  const Card = registry.get("urdb-card");
  const card = new Card();
  card.setConfig(Card.getStubConfig());
  card.hass = {
    locale: { language: "ru" },
    states: {
      "sensor.urdb_status": {
        state: "ok",
        attributes: {
          current_version: "routing-1",
          latest_version: "routing-2",
          has_update: true,
          checked_at: "2026-07-15T00:00:00Z",
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
  for (const [action, entityId] of [
    ["check", "button.check"],
    ["update", "button.update"],
    ["restart", "button.restart"],
  ]) {
    card._operation = null;
    await card._run(action);
    assert.deepEqual(calls.at(-1), ["button", "press", { entity_id: entityId }]);
    assert.equal(card._progress, 100);
    assert.match(card.shadowRoot.innerHTML, /class="progress"/);
  }
});
