const INTEGRATION_VERSION = "0.3.2";
const DEFAULT_CONFIG = {
  status_entity: "sensor.urdb_status",
  changes_entity: "sensor.urdb_changes",
  check_entity: "button.check",
  update_entity: "button.update",
  restart_entity: "button.restart",
};

const TEXT = {
  en: {
    title: "Universal Routing Database", integration: "Integration", routing: "Routing",
    status: "Status", health: "Health", github: "GitHub status", current: "Current version",
    latest: "Latest version", updateAvailable: "Update available", lastCheck: "Last check",
    yes: "Yes", no: "No", healthy: "Healthy", unavailable: "Unavailable", upToDate: "System is up to date",
    updateReady: "Routing update available", releaseNotes: "Release notes", noNotes: "No release notes provided",
    cachedWarning: "GitHub rate limit reached. Cached release data is being used; URDB remains healthy.",
    check: "Check updates", update: "Update", restart: "Restart", activity: "Activity",
    noActivity: "No actions executed in this session", running: "Running", completed: "Completed", failed: "Failed",
    checking: "Checking for updates", updating: "Updating URDB", restarting: "Restarting URDB",
    cpu: "CPU", memory: "Memory", uptime: "Uptime",
  },
  ru: {
    title: "Universal Routing Database", integration: "Интеграция", routing: "Маршрутизация",
    status: "Состояние", health: "Здоровье", github: "Статус GitHub", current: "Текущая версия",
    latest: "Последняя версия", updateAvailable: "Доступно обновление", lastCheck: "Последняя проверка",
    yes: "Да", no: "Нет", healthy: "Работает", unavailable: "Недоступен", upToDate: "Система актуальна",
    updateReady: "Доступно обновление маршрутизации", releaseNotes: "Изменения", noNotes: "Описание изменений отсутствует",
    cachedWarning: "Достигнут лимит GitHub. Используются кэшированные данные; URDB продолжает работать.",
    check: "Проверить", update: "Обновить", restart: "Перезапустить", activity: "Активность",
    noActivity: "В этой сессии действий ещё не было", running: "Выполняется", completed: "Завершено", failed: "Ошибка",
    checking: "Проверка обновлений", updating: "Обновление URDB", restarting: "Перезапуск URDB",
    cpu: "CPU", memory: "Память", uptime: "Время работы",
  },
};

const escapeHtml = (value) => String(value ?? "—")
  .replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;").replaceAll("'", "&#039;");

class URDBCard extends HTMLElement {
  static getStubConfig() { return { ...DEFAULT_CONFIG }; }
  static getConfigElement() { return document.createElement("urdb-card-editor"); }

  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = { ...DEFAULT_CONFIG };
    this._operation = null;
    this._progress = 0;
    this._timer = null;
    this._lastAction = null;
  }

  setConfig(config) { this._config = { ...DEFAULT_CONFIG, ...config }; this._render(); }
  set hass(hass) { this._hass = hass; this._render(); }
  getCardSize() { return 9; }
  disconnectedCallback() { clearInterval(this._timer); }
  _state(entityId) { return this._hass?.states?.[entityId]; }
  _strings() { return TEXT[this._hass?.locale?.language === "ru" ? "ru" : "en"]; }

  _formatDate(value) {
    if (!value) return "—";
    const date = new Date(value);
    if (Number.isNaN(date.valueOf())) return value;
    return new Intl.DateTimeFormat(this._hass?.locale?.language || undefined, {
      dateStyle: "medium", timeStyle: "short",
    }).format(date);
  }

  async _run(action) {
    if (this._operation || !this._hass) return;
    const t = this._strings();
    const entityId = this._config[`${action}_entity`];
    this._operation = action;
    this._progress = 6;
    this._lastAction = { action, state: "running", at: new Date().toISOString() };
    this._render();
    clearInterval(this._timer);
    this._timer = setInterval(() => {
      this._progress = Math.min(92, this._progress + (this._progress < 55 ? 8 : 2));
      this._render();
    }, 700);
    try {
      await this._hass.callService("button", "press", { entity_id: entityId });
      this._progress = 100;
      this._lastAction = { action, state: "completed", at: new Date().toISOString() };
    } catch (error) {
      this._error = error?.message || String(error);
      this._progress = 0;
      this._lastAction = { action, state: "failed", at: new Date().toISOString() };
    } finally {
      clearInterval(this._timer);
      this._render();
      window.setTimeout(() => {
        this._operation = null;
        this._progress = 0;
        this._error = null;
        this._render();
      }, 1200);
    }
  }

  _actionLabel(action, t) {
    return { check: t.checking, update: t.updating, restart: t.restarting }[action];
  }

  _render() {
    if (!this.shadowRoot) return;
    const t = this._strings();
    const status = this._state(this._config.status_entity);
    const changesState = this._state(this._config.changes_entity);
    const attributes = status?.attributes || {};
    const changesAttributes = changesState?.attributes || {};
    const changes = changesAttributes.changes || attributes.changes || [];
    const githubStatus = attributes.github_status || changesAttributes.github_status || "ok";
    const hasUpdate = Boolean(attributes.has_update);
    const health = status?.state || "unavailable";
    const healthTone = health !== "ok" ? "bad" : githubStatus !== "ok" ? "warn" : "good";
    const githubLabel = githubStatus === "rate_limited" ? "Rate limited · cached" : githubStatus === "ok" ? "Connected" : githubStatus;
    const resources = [
      [t.cpu, attributes.cpu_percent, "%"],
      [t.memory, attributes.memory_percent, "%"],
      [t.uptime, attributes.uptime, ""],
    ].filter(([, value]) => value !== undefined && value !== null);
    const activityState = this._lastAction
      ? { running: t.running, completed: t.completed, failed: t.failed }[this._lastAction.state]
      : null;

    this.shadowRoot.innerHTML = `
      <style>
        :host { display:block; container-type:inline-size; }
        ha-card { overflow:hidden; color:var(--primary-text-color); background:var(--ha-card-background,var(--card-background-color)); }
        .header { display:flex; align-items:center; justify-content:space-between; gap:16px; padding:22px 22px 16px; }
        .identity { display:flex; align-items:center; gap:14px; min-width:0; }
        .logo { width:46px; height:46px; flex:0 0 46px; display:grid; place-items:center; border-radius:14px;
          color:var(--primary-color); background:color-mix(in srgb,var(--primary-color) 14%,transparent); }
        .logo ha-icon { --mdc-icon-size:27px; } h2 { margin:0; font-size:20px; line-height:1.25; }
        .versions { display:flex; gap:8px 14px; flex-wrap:wrap; margin-top:5px; color:var(--secondary-text-color); font-size:12px; }
        .health { display:flex; align-items:center; gap:7px; padding:7px 11px; border-radius:999px; font-size:12px; font-weight:600; white-space:nowrap; }
        .health::before { content:""; width:8px; height:8px; border-radius:50%; background:currentColor; }
        .good { color:var(--success-color,#43a047); background:color-mix(in srgb,var(--success-color,#43a047) 12%,transparent); }
        .warn { color:var(--warning-color,#ef9f27); background:color-mix(in srgb,var(--warning-color,#ef9f27) 14%,transparent); }
        .bad { color:var(--error-color,#db4437); background:color-mix(in srgb,var(--error-color,#db4437) 12%,transparent); }
        .warning { display:flex; gap:10px; align-items:flex-start; margin:0 22px 16px; padding:12px 14px; border-radius:12px;
          color:var(--warning-color,#ef9f27); background:color-mix(in srgb,var(--warning-color,#ef9f27) 12%,transparent); font-size:13px; }
        .warning ha-icon { flex:0 0 auto; --mdc-icon-size:20px; }
        .section { padding:0 22px 18px; } .section-title { margin:0 0 10px; font-size:13px; font-weight:600; color:var(--secondary-text-color); }
        .grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; }
        .metric { min-width:0; padding:12px 13px; border:1px solid var(--divider-color); border-radius:12px; }
        .label { margin-bottom:5px; color:var(--secondary-text-color); font-size:11px; }
        .value { font-size:14px; font-weight:600; overflow-wrap:anywhere; }
        .update-banner { margin:0 22px 18px; padding:16px; border:1px solid color-mix(in srgb,var(--primary-color) 35%,var(--divider-color));
          border-radius:14px; background:color-mix(in srgb,var(--primary-color) 8%,transparent); }
        .update-head { display:flex; justify-content:space-between; align-items:flex-start; gap:14px; }
        .update-title { display:flex; align-items:center; gap:8px; font-weight:700; } .update-title ha-icon { color:var(--primary-color); }
        .latest { margin-top:5px; color:var(--secondary-text-color); font-size:12px; }
        .notes { margin:12px 0 0; padding:12px 0 0; border-top:1px solid var(--divider-color); }
        .notes strong { font-size:12px; } ul { margin:7px 0 0; padding-left:20px; color:var(--secondary-text-color); font-size:13px; }
        li+li { margin-top:4px; } .up-to-date { display:flex; align-items:center; gap:9px; margin:0 22px 18px; padding:13px 15px; border-radius:12px; font-weight:600; }
        .activity { display:flex; justify-content:space-between; align-items:center; gap:12px; padding:12px 13px; border:1px solid var(--divider-color); border-radius:12px; }
        .activity-main { display:flex; align-items:center; gap:10px; min-width:0; } .activity-main ha-icon { color:var(--primary-color); }
        .activity-detail { color:var(--secondary-text-color); font-size:12px; margin-top:3px; }
        .progress { margin-top:10px; } ha-linear-progress { width:100%; } .error { color:var(--error-color); font-size:12px; margin-top:7px; }
        .actions { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; padding:0 22px 22px; }
        ha-button { width:100%; } ha-button ha-icon { margin-right:6px; --mdc-icon-size:19px; }
        @container (max-width:520px) { .header,.update-head { align-items:flex-start; } .header { flex-direction:column; }
          .grid { grid-template-columns:repeat(2,minmax(0,1fr)); } .actions { grid-template-columns:1fr; } }
        @container (max-width:340px) { .grid { grid-template-columns:1fr; } }
      </style>
      <ha-card>
        <div class="header">
          <div class="identity"><div class="logo"><ha-icon icon="mdi:routes"></ha-icon></div><div>
            <h2>${t.title}</h2><div class="versions"><span>${t.integration}: v${INTEGRATION_VERSION}</span><span>${t.routing}: ${escapeHtml(attributes.current_version)}</span></div>
          </div></div>
          <span class="health ${healthTone}">${health === "ok" ? t.healthy : escapeHtml(health)}</span>
        </div>
        ${githubStatus === "rate_limited" ? `<div class="warning"><ha-icon icon="mdi:database-clock-outline"></ha-icon><span>${t.cachedWarning}</span></div>` : ""}
        <section class="section"><h3 class="section-title">${t.status}</h3><div class="grid">
          <div class="metric"><div class="label">${t.health}</div><div class="value">${health === "ok" ? t.healthy : t.unavailable}</div></div>
          <div class="metric"><div class="label">${t.github}</div><div class="value">${escapeHtml(githubLabel)}</div></div>
          <div class="metric"><div class="label">${t.current}</div><div class="value">${escapeHtml(attributes.current_version)}</div></div>
          <div class="metric"><div class="label">${t.latest}</div><div class="value">${escapeHtml(attributes.latest_version)}</div></div>
          <div class="metric"><div class="label">${t.updateAvailable}</div><div class="value">${hasUpdate ? t.yes : t.no}</div></div>
          <div class="metric"><div class="label">${t.lastCheck}</div><div class="value">${escapeHtml(this._formatDate(attributes.checked_at))}</div></div>
          ${resources.map(([label,value,suffix]) => `<div class="metric"><div class="label">${label}</div><div class="value">${escapeHtml(value)}${suffix}</div></div>`).join("")}
        </div></section>
        ${hasUpdate ? `<section class="update-banner"><div class="update-head"><div><div class="update-title"><ha-icon icon="mdi:update"></ha-icon>${t.updateReady}</div>
          <div class="latest">${t.latest}: ${escapeHtml(attributes.latest_version)}</div></div>
          <ha-button appearance="filled" data-action="update" ${this._operation ? "disabled" : ""}><ha-icon icon="mdi:download"></ha-icon>${t.update}</ha-button></div>
          <div class="notes"><strong>${t.releaseNotes}</strong>${changes.length ? `<ul>${changes.slice(0,10).map((item)=>`<li>${escapeHtml(item)}</li>`).join("")}</ul>` : `<div class="activity-detail">${t.noNotes}</div>`}</div></section>`
          : `<div class="up-to-date good"><ha-icon icon="mdi:check-circle-outline"></ha-icon>${t.upToDate}</div>`}
        <section class="section"><h3 class="section-title">${t.activity}</h3><div class="activity"><div class="activity-main"><ha-icon icon="mdi:history"></ha-icon><div>
          <div class="value">${this._lastAction ? escapeHtml(this._actionLabel(this._lastAction.action,t)) : t.noActivity}</div>
          ${this._lastAction ? `<div class="activity-detail">${activityState} · ${escapeHtml(this._formatDate(this._lastAction.at))}</div>` : ""}
        </div></div>${this._operation ? `<strong>${this._progress}%</strong>` : ""}</div>
        ${this._operation ? `<div class="progress" role="status" aria-live="polite"><ha-linear-progress></ha-linear-progress>${this._error ? `<div class="error">${escapeHtml(this._error)}</div>` : ""}</div>` : ""}</section>
        <div class="actions">
          <ha-button appearance="outlined" data-action="check" ${this._operation ? "disabled" : ""}><ha-icon icon="mdi:refresh"></ha-icon>${t.check}</ha-button>
          <ha-button appearance="outlined" data-action="update" ${this._operation ? "disabled" : ""}><ha-icon icon="mdi:download"></ha-icon>${t.update}</ha-button>
          <ha-button appearance="outlined" data-action="restart" ${this._operation ? "disabled" : ""}><ha-icon icon="mdi:restart"></ha-icon>${t.restart}</ha-button>
        </div>
      </ha-card>`;
    const progress = this.shadowRoot.querySelector("ha-linear-progress");
    if (progress) progress.progress = this._progress / 100;
    this.shadowRoot.querySelectorAll("[data-action]").forEach((button) => {
      button.addEventListener("click", () => this._run(button.dataset.action));
    });
  }
}

class URDBCardEditor extends HTMLElement {
  setConfig(config) { this._config = { ...DEFAULT_CONFIG, ...config }; this._render(); }
  set hass(hass) { this._hass = hass; this._render(); }
  _render() {
    if (!this._config) return;
    this.innerHTML = `<style>.form{display:grid;gap:12px;padding:8px 0}</style><div class="form">${Object.entries({
      status_entity:"Status",changes_entity:"Changes",check_entity:"Check updates",update_entity:"Update",restart_entity:"Restart",
    }).map(([key,label])=>`<ha-entity-picker data-key="${key}" label="${label}"></ha-entity-picker>`).join("")}</div>`;
    this.querySelectorAll("ha-entity-picker").forEach((picker) => {
      picker.hass = this._hass; picker.value = this._config[picker.dataset.key];
      picker.addEventListener("value-changed", (event) => {
        this._config = { ...this._config, [picker.dataset.key]: event.detail.value };
        this.dispatchEvent(new CustomEvent("config-changed", { detail:{ config:this._config }, bubbles:true, composed:true }));
      });
    });
  }
}

if (!customElements.get("urdb-card")) customElements.define("urdb-card", URDBCard);
if (!customElements.get("urdb-card-editor")) customElements.define("urdb-card-editor", URDBCardEditor);
window.customCards = window.customCards || [];
if (!window.customCards.some((card) => card.type === "urdb-card")) window.customCards.push({
  type:"urdb-card", name:"Universal Routing Database", description:"Native URDB status and update dashboard", preview:true,
});
console.info(`%c URDB CARD %c v${INTEGRATION_VERSION} `,"color:white;background:#03a9f4;font-weight:bold","color:#03a9f4;background:white");
