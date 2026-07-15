import { LitElement, css, html, nothing } from "lit";

const INTEGRATION_VERSION = "0.4.0";
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

class URDBCard extends LitElement {
  static properties = {
    hass: { attribute: false },
    _operation: { state: true },
    _progress: { state: true },
    _lastAction: { state: true },
    _error: { state: true },
  };

  static styles = css`
    :host { display:block; container-type:inline-size; }
    ha-card { overflow:hidden; color:var(--primary-text-color); background:var(--ha-card-background,var(--card-background-color)); }
    .header { display:flex; align-items:center; justify-content:space-between; gap:16px; padding:22px 22px 16px; }
    .identity { display:flex; align-items:center; gap:14px; min-width:0; }
    .logo { width:46px; height:46px; flex:0 0 46px; display:grid; place-items:center; border-radius:14px; color:var(--primary-color); background:color-mix(in srgb,var(--primary-color) 14%,transparent); }
    .logo ha-icon { --mdc-icon-size:27px; } h2 { margin:0; font-size:20px; line-height:1.25; }
    .versions { display:flex; gap:8px 14px; flex-wrap:wrap; margin-top:5px; color:var(--secondary-text-color); font-size:12px; }
    .health { display:flex; align-items:center; gap:7px; padding:7px 11px; border-radius:999px; font-size:12px; font-weight:600; white-space:nowrap; }
    .health::before { content:""; width:8px; height:8px; border-radius:50%; background:currentColor; }
    .good { color:var(--success-color,#43a047); background:color-mix(in srgb,var(--success-color,#43a047) 12%,transparent); }
    .warn { color:var(--warning-color,#ef9f27); background:color-mix(in srgb,var(--warning-color,#ef9f27) 14%,transparent); }
    .bad { color:var(--error-color,#db4437); background:color-mix(in srgb,var(--error-color,#db4437) 12%,transparent); }
    .warning { display:flex; gap:10px; align-items:flex-start; margin:0 22px 16px; padding:12px 14px; border-radius:12px; color:var(--warning-color,#ef9f27); background:color-mix(in srgb,var(--warning-color,#ef9f27) 12%,transparent); font-size:13px; }
    .warning ha-icon { flex:0 0 auto; --mdc-icon-size:20px; }
    .section { padding:0 22px 18px; } .section-title { margin:0 0 10px; font-size:13px; font-weight:600; color:var(--secondary-text-color); }
    .grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; }
    .metric { min-width:0; padding:12px 13px; border:1px solid var(--divider-color); border-radius:12px; }
    .label { margin-bottom:5px; color:var(--secondary-text-color); font-size:11px; }
    .value { font-size:14px; font-weight:600; overflow-wrap:anywhere; }
    .update-banner { margin:0 22px 18px; padding:16px; border:1px solid color-mix(in srgb,var(--primary-color) 35%,var(--divider-color)); border-radius:14px; background:color-mix(in srgb,var(--primary-color) 8%,transparent); }
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
    @container (max-width:520px) { .header,.update-head { align-items:flex-start; } .header { flex-direction:column; } .grid { grid-template-columns:repeat(2,minmax(0,1fr)); } .actions { grid-template-columns:1fr; } }
    @container (max-width:340px) { .grid { grid-template-columns:1fr; } }
  `;

  constructor() {
    super();
    this._config = { ...DEFAULT_CONFIG };
    this._operation = null;
    this._progress = 0;
    this._timer = null;
    this._lastAction = null;
    this._error = null;
  }

  static getStubConfig() { return { ...DEFAULT_CONFIG }; }
  static getConfigElement() { return document.createElement("urdb-card-editor"); }
  setConfig(config) { this._config = { ...DEFAULT_CONFIG, ...config }; this.requestUpdate(); }
  getCardSize() { return 9; }
  disconnectedCallback() { super.disconnectedCallback(); clearInterval(this._timer); }
  _state(entityId) { return this.hass?.states?.[entityId]; }
  _strings() { return TEXT[this.hass?.locale?.language === "ru" ? "ru" : "en"]; }
  _formatDate(value) {
    if (!value) return "—";
    const date = new Date(value);
    if (Number.isNaN(date.valueOf())) return value;
    return new Intl.DateTimeFormat(this.hass?.locale?.language || undefined, { dateStyle: "medium", timeStyle: "short" }).format(date);
  }
  _actionLabel(action, t) { return { check:t.checking, update:t.updating, restart:t.restarting }[action]; }

  async _run(action) {
    if (this._operation || !this.hass) return;
    const entityId = this._config[`${action}_entity`];
    this._operation = action; this._progress = 6; this._error = null;
    this._lastAction = { action, state:"running", at:new Date().toISOString() };
    clearInterval(this._timer);
    this._timer = setInterval(() => { this._progress = Math.min(92, this._progress + (this._progress < 55 ? 8 : 2)); }, 700);
    try {
      await this.hass.callService("button", "press", { entity_id:entityId });
      this._progress = 100;
      this._lastAction = { action, state:"completed", at:new Date().toISOString() };
    } catch (error) {
      this._error = error?.message || String(error); this._progress = 0;
      this._lastAction = { action, state:"failed", at:new Date().toISOString() };
    } finally {
      clearInterval(this._timer);
      window.setTimeout(() => { this._operation = null; this._progress = 0; this._error = null; }, 1200);
    }
  }

  _metric(label, value) { return html`<div class="metric"><div class="label">${label}</div><div class="value">${value ?? "—"}</div></div>`; }

  render() {
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
    const activityState = this._lastAction ? { running:t.running, completed:t.completed, failed:t.failed }[this._lastAction.state] : null;
    const resources = [[t.cpu,attributes.cpu_percent,"%"],[t.memory,attributes.memory_percent,"%"],[t.uptime,attributes.uptime,""]].filter(([,v]) => v != null);
    return html`<ha-card>
      <div class="header"><div class="identity"><div class="logo"><ha-icon icon="mdi:routes"></ha-icon></div><div>
        <h2>${t.title}</h2><div class="versions"><span>${t.integration}: v${INTEGRATION_VERSION}</span><span>${t.routing}: ${attributes.current_version ?? "—"}</span></div>
      </div></div><span class="health ${healthTone}">${health === "ok" ? t.healthy : health}</span></div>
      ${githubStatus === "rate_limited" ? html`<div class="warning"><ha-icon icon="mdi:database-clock-outline"></ha-icon><span>${t.cachedWarning}</span></div>` : nothing}
      <section class="section"><h3 class="section-title">${t.status}</h3><div class="grid">
        ${this._metric(t.health, health === "ok" ? t.healthy : t.unavailable)}
        ${this._metric(t.github, githubLabel)} ${this._metric(t.current, attributes.current_version)}
        ${this._metric(t.latest, attributes.latest_version)} ${this._metric(t.updateAvailable, hasUpdate ? t.yes : t.no)}
        ${this._metric(t.lastCheck, this._formatDate(attributes.checked_at))}
        ${resources.map(([label,value,suffix]) => this._metric(label, `${value}${suffix}`))}
      </div></section>
      ${hasUpdate ? html`<section class="update-banner"><div class="update-head"><div><div class="update-title"><ha-icon icon="mdi:update"></ha-icon>${t.updateReady}</div><div class="latest">${t.latest}: ${attributes.latest_version ?? "—"}</div></div>
        <ha-button appearance="filled" data-action="update" ?disabled=${Boolean(this._operation)} @click=${() => this._run("update")}><ha-icon icon="mdi:download"></ha-icon>${t.update}</ha-button></div>
        <div class="notes"><strong>${t.releaseNotes}</strong>${changes.length ? html`<ul>${changes.slice(0,10).map((item) => html`<li>${item}</li>`)}</ul>` : html`<div class="activity-detail">${t.noNotes}</div>`}</div></section>`
        : html`<div class="up-to-date good"><ha-icon icon="mdi:check-circle-outline"></ha-icon>${t.upToDate}</div>`}
      <section class="section"><h3 class="section-title">${t.activity}</h3><div class="activity"><div class="activity-main"><ha-icon icon="mdi:history"></ha-icon><div>
        <div class="value">${this._lastAction ? this._actionLabel(this._lastAction.action,t) : t.noActivity}</div>
        ${this._lastAction ? html`<div class="activity-detail">${activityState} · ${this._formatDate(this._lastAction.at)}</div>` : nothing}
      </div></div>${this._operation ? html`<strong>${this._progress}%</strong>` : nothing}</div>
      ${this._operation ? html`<div class="progress" role="status" aria-live="polite"><ha-linear-progress .progress=${this._progress / 100}></ha-linear-progress>${this._error ? html`<div class="error">${this._error}</div>` : nothing}</div>` : nothing}</section>
      <div class="actions">
        ${[["check",t.check,"mdi:refresh"],["update",t.update,"mdi:download"],["restart",t.restart,"mdi:restart"]].map(([action,label,icon]) => html`
          <ha-button appearance="outlined" data-action=${action} ?disabled=${Boolean(this._operation)} @click=${() => this._run(action)}><ha-icon icon=${icon}></ha-icon>${label}</ha-button>`)}
      </div>
    </ha-card>`;
  }
}

class URDBCardEditor extends LitElement {
  static properties = { hass:{ attribute:false } };
  static styles = css`.form { display:grid; gap:12px; padding:8px 0; }`;
  constructor() { super(); this._config = { ...DEFAULT_CONFIG }; }
  setConfig(config) { this._config = { ...DEFAULT_CONFIG, ...config }; this.requestUpdate(); }
  _changed(key, event) {
    this._config = { ...this._config, [key]:event.detail.value };
    this.dispatchEvent(new CustomEvent("config-changed", { detail:{ config:this._config }, bubbles:true, composed:true }));
  }
  render() {
    const fields = { status_entity:"Status", changes_entity:"Changes", check_entity:"Check updates", update_entity:"Update", restart_entity:"Restart" };
    return html`<div class="form">${Object.entries(fields).map(([key,label]) => html`
      <ha-entity-picker .hass=${this.hass} .value=${this._config[key]} .label=${label} @value-changed=${(event) => this._changed(key,event)}></ha-entity-picker>`)}
    </div>`;
  }
}

if (!customElements.get("urdb-card")) customElements.define("urdb-card", URDBCard);
if (!customElements.get("urdb-card-editor")) customElements.define("urdb-card-editor", URDBCardEditor);
window.customCards = window.customCards || [];
if (!window.customCards.some((card) => card.type === "urdb-card")) window.customCards.push({
  type:"urdb-card", name:"Universal Routing Database", description:"Native URDB status and update dashboard", preview:true,
});
console.info(`%c URDB CARD %c v${INTEGRATION_VERSION} `,"color:white;background:#03a9f4;font-weight:bold","color:#03a9f4;background:white");
