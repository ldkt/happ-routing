const CARD_VERSION = "0.2.0";
const DEFAULT_CONFIG = {
  status_entity: "sensor.urdb_status",
  changes_entity: "sensor.urdb_changes",
  check_entity: "button.check",
  update_entity: "button.update",
  restart_entity: "button.restart",
};

const escapeHtml = (value) => String(value ?? "—")
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;")
  .replaceAll("'", "&#039;");

class URDBCard extends HTMLElement {
  static getStubConfig() {
    return { ...DEFAULT_CONFIG };
  }

  static getConfigElement() {
    return document.createElement("urdb-card-editor");
  }

  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = { ...DEFAULT_CONFIG };
    this._operation = null;
    this._progress = 0;
    this._timer = null;
  }

  setConfig(config) {
    this._config = { ...DEFAULT_CONFIG, ...config };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return 6;
  }

  disconnectedCallback() {
    clearInterval(this._timer);
  }

  _state(entityId) {
    return this._hass?.states?.[entityId];
  }

  _formatDate(value) {
    if (!value) return "—";
    const date = new Date(value);
    if (Number.isNaN(date.valueOf())) return value;
    return new Intl.DateTimeFormat(this._hass?.locale?.language || undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(date);
  }

  async _run(action) {
    if (this._operation || !this._hass) return;
    const entityId = this._config[`${action}_entity`];
    this._operation = action;
    this._progress = 8;
    this._render();
    clearInterval(this._timer);
    this._timer = setInterval(() => {
      this._progress = Math.min(92, this._progress + (this._progress < 50 ? 9 : 3));
      this._render();
    }, 700);
    try {
      await this._hass.callService("button", "press", { entity_id: entityId });
      this._progress = 100;
    } catch (error) {
      this._error = error?.message || String(error);
      this._progress = 0;
    } finally {
      clearInterval(this._timer);
      this._render();
      window.setTimeout(() => {
        this._operation = null;
        this._progress = 0;
        this._error = null;
        this._render();
      }, 900);
    }
  }

  _render() {
    if (!this.shadowRoot) return;
    const status = this._state(this._config.status_entity);
    const changesState = this._state(this._config.changes_entity);
    const attributes = status?.attributes || {};
    const changes = changesState?.attributes?.changes || attributes.changes || [];
    const healthy = status?.state === "ok";
    const hasUpdate = Boolean(attributes.has_update);
    const operationLabel = {
      check: "Проверка обновлений",
      update: "Обновление URDB",
      restart: "Перезапуск URDB",
    }[this._operation];

    this.shadowRoot.innerHTML = `
      <style>
        :host { display: block; }
        ha-card {
          overflow: hidden;
          color: var(--primary-text-color);
          background: var(--ha-card-background, var(--card-background-color));
        }
        .header {
          display: flex; align-items: center; justify-content: space-between;
          padding: 20px 20px 12px; gap: 12px;
        }
        .title { display: flex; align-items: center; gap: 12px; min-width: 0; }
        .logo {
          width: 42px; height: 42px; display: grid; place-items: center;
          border-radius: 13px; color: var(--primary-color);
          background: color-mix(in srgb, var(--primary-color) 14%, transparent);
        }
        .logo ha-icon { --mdc-icon-size: 25px; }
        h2 { margin: 0; font-size: 20px; line-height: 1.2; }
        .subtitle { color: var(--secondary-text-color); font-size: 12px; margin-top: 3px; }
        .badge {
          padding: 6px 10px; border-radius: 999px; font-weight: 600; font-size: 12px;
          color: ${healthy ? "var(--success-color, #43a047)" : "var(--error-color)"};
          background: color-mix(in srgb, currentColor 12%, transparent);
        }
        .grid {
          display: grid; grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 10px; padding: 8px 20px 16px;
        }
        .metric { padding: 12px; border: 1px solid var(--divider-color); border-radius: 12px; }
        .metric.wide { grid-column: 1 / -1; }
        .label { color: var(--secondary-text-color); font-size: 12px; margin-bottom: 5px; }
        .value { font-size: 15px; font-weight: 600; overflow-wrap: anywhere; }
        .update-yes { color: var(--warning-color, #f9a825); }
        .changes { padding: 0 20px 16px; }
        .changes h3 { font-size: 14px; margin: 0 0 8px; }
        ul { margin: 0; padding-left: 20px; color: var(--secondary-text-color); }
        li + li { margin-top: 4px; }
        .empty { color: var(--secondary-text-color); font-size: 13px; }
        .progress { padding: 0 20px 16px; }
        .progress-head { display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 6px; }
        .track { height: 6px; border-radius: 999px; overflow: hidden; background: var(--divider-color); }
        .bar { height: 100%; width: ${this._progress}%; background: var(--primary-color); transition: width .25s ease; }
        .error { color: var(--error-color); font-size: 12px; margin-top: 6px; }
        .actions { display: grid; grid-template-columns: repeat(3, 1fr); border-top: 1px solid var(--divider-color); }
        button {
          appearance: none; border: 0; border-right: 1px solid var(--divider-color);
          background: transparent; color: var(--primary-text-color); min-height: 62px;
          padding: 8px 4px; cursor: pointer; display: flex; flex-direction: column;
          justify-content: center; align-items: center; gap: 4px; font: inherit; font-size: 11px;
        }
        button:last-child { border-right: 0; }
        button:hover { background: color-mix(in srgb, var(--primary-color) 8%, transparent); }
        button:disabled { opacity: .45; cursor: wait; }
        button ha-icon { color: var(--primary-color); --mdc-icon-size: 21px; }
        @media (max-width: 360px) { .grid { grid-template-columns: 1fr; } .metric.wide { grid-column: auto; } }
      </style>
      <ha-card>
        <div class="header">
          <div class="title"><div class="logo"><ha-icon icon="mdi:routes"></ha-icon></div><div>
            <h2>URDB</h2><div class="subtitle">Universal Routing Database</div>
          </div></div>
          <span class="badge">${healthy ? "Работает" : escapeHtml(status?.state || "Недоступен")}</span>
        </div>
        <div class="grid">
          <div class="metric"><div class="label">Текущая версия</div><div class="value">${escapeHtml(attributes.current_version)}</div></div>
          <div class="metric"><div class="label">Последняя версия</div><div class="value">${escapeHtml(attributes.latest_version)}</div></div>
          <div class="metric"><div class="label">Обновление</div><div class="value ${hasUpdate ? "update-yes" : ""}">${hasUpdate ? "Доступно" : "Не требуется"}</div></div>
          <div class="metric"><div class="label">Последняя проверка</div><div class="value">${escapeHtml(this._formatDate(attributes.checked_at))}</div></div>
        </div>
        <div class="changes"><h3>Последние изменения</h3>${changes.length
          ? `<ul>${changes.slice(0, 8).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`
          : '<div class="empty">Изменений нет</div>'}</div>
        ${this._operation ? `<div class="progress" role="status" aria-live="polite">
          <div class="progress-head"><span>${operationLabel}</span><span>${this._progress}%</span></div>
          <div class="track"><div class="bar"></div></div>${this._error ? `<div class="error">${escapeHtml(this._error)}</div>` : ""}
        </div>` : ""}
        <div class="actions">
          <button data-action="check" ${this._operation ? "disabled" : ""}><ha-icon icon="mdi:refresh"></ha-icon>Проверить</button>
          <button data-action="update" ${this._operation ? "disabled" : ""}><ha-icon icon="mdi:download"></ha-icon>Обновить</button>
          <button data-action="restart" ${this._operation ? "disabled" : ""}><ha-icon icon="mdi:restart"></ha-icon>Перезапустить</button>
        </div>
      </ha-card>`;
    this.shadowRoot.querySelectorAll("button[data-action]").forEach((button) => {
      button.addEventListener("click", () => this._run(button.dataset.action));
    });
  }
}

class URDBCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = { ...DEFAULT_CONFIG, ...config };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _render() {
    if (!this._config) return;
    this.innerHTML = `<style>.form{display:grid;gap:12px;padding:8px 0}</style><div class="form">
      ${Object.entries({ status_entity: "Состояние", changes_entity: "Изменения", check_entity: "Проверить", update_entity: "Обновить", restart_entity: "Перезапустить" })
        .map(([key, label]) => `<ha-entity-picker data-key="${key}" label="${label}"></ha-entity-picker>`).join("")}
    </div>`;
    this.querySelectorAll("ha-entity-picker").forEach((picker) => {
      picker.hass = this._hass;
      picker.value = this._config[picker.dataset.key];
      picker.addEventListener("value-changed", (event) => {
        this._config = { ...this._config, [picker.dataset.key]: event.detail.value };
        this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: this._config }, bubbles: true, composed: true }));
      });
    });
  }
}

if (!customElements.get("urdb-card")) customElements.define("urdb-card", URDBCard);
if (!customElements.get("urdb-card-editor")) customElements.define("urdb-card-editor", URDBCardEditor);
window.customCards = window.customCards || [];
if (!window.customCards.some((card) => card.type === "urdb-card")) {
  window.customCards.push({
    type: "urdb-card",
    name: "URDB",
    description: "Статус, обновления и управление Universal Routing Database",
    preview: true,
  });
}
console.info(`%c URDB CARD %c v${CARD_VERSION} `, "color:white;background:#03a9f4;font-weight:bold", "color:#03a9f4;background:white");
