// node_modules/.pnpm/@lit+reactive-element@2.1.2/node_modules/@lit/reactive-element/css-tag.js
var t = globalThis;
var e = t.ShadowRoot && (void 0 === t.ShadyCSS || t.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype;
var s = Symbol();
var o = /* @__PURE__ */ new WeakMap();
var n = class {
  constructor(t3, e4, o5) {
    if (this._$cssResult$ = true, o5 !== s) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = t3, this.t = e4;
  }
  get styleSheet() {
    let t3 = this.o;
    const s4 = this.t;
    if (e && void 0 === t3) {
      const e4 = void 0 !== s4 && 1 === s4.length;
      e4 && (t3 = o.get(s4)), void 0 === t3 && ((this.o = t3 = new CSSStyleSheet()).replaceSync(this.cssText), e4 && o.set(s4, t3));
    }
    return t3;
  }
  toString() {
    return this.cssText;
  }
};
var r = (t3) => new n("string" == typeof t3 ? t3 : t3 + "", void 0, s);
var i = (t3, ...e4) => {
  const o5 = 1 === t3.length ? t3[0] : e4.reduce((e5, s4, o6) => e5 + ((t4) => {
    if (true === t4._$cssResult$) return t4.cssText;
    if ("number" == typeof t4) return t4;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + t4 + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(s4) + t3[o6 + 1], t3[0]);
  return new n(o5, t3, s);
};
var S = (s4, o5) => {
  if (e) s4.adoptedStyleSheets = o5.map((t3) => t3 instanceof CSSStyleSheet ? t3 : t3.styleSheet);
  else for (const e4 of o5) {
    const o6 = document.createElement("style"), n4 = t.litNonce;
    void 0 !== n4 && o6.setAttribute("nonce", n4), o6.textContent = e4.cssText, s4.appendChild(o6);
  }
};
var c = e ? (t3) => t3 : (t3) => t3 instanceof CSSStyleSheet ? ((t4) => {
  let e4 = "";
  for (const s4 of t4.cssRules) e4 += s4.cssText;
  return r(e4);
})(t3) : t3;

// node_modules/.pnpm/@lit+reactive-element@2.1.2/node_modules/@lit/reactive-element/reactive-element.js
var { is: i2, defineProperty: e2, getOwnPropertyDescriptor: h, getOwnPropertyNames: r2, getOwnPropertySymbols: o2, getPrototypeOf: n2 } = Object;
var a = globalThis;
var c2 = a.trustedTypes;
var l = c2 ? c2.emptyScript : "";
var p = a.reactiveElementPolyfillSupport;
var d = (t3, s4) => t3;
var u = { toAttribute(t3, s4) {
  switch (s4) {
    case Boolean:
      t3 = t3 ? l : null;
      break;
    case Object:
    case Array:
      t3 = null == t3 ? t3 : JSON.stringify(t3);
  }
  return t3;
}, fromAttribute(t3, s4) {
  let i5 = t3;
  switch (s4) {
    case Boolean:
      i5 = null !== t3;
      break;
    case Number:
      i5 = null === t3 ? null : Number(t3);
      break;
    case Object:
    case Array:
      try {
        i5 = JSON.parse(t3);
      } catch (t4) {
        i5 = null;
      }
  }
  return i5;
} };
var f = (t3, s4) => !i2(t3, s4);
var b = { attribute: true, type: String, converter: u, reflect: false, useDefault: false, hasChanged: f };
Symbol.metadata ??= Symbol("metadata"), a.litPropertyMetadata ??= /* @__PURE__ */ new WeakMap();
var y = class extends HTMLElement {
  static addInitializer(t3) {
    this._$Ei(), (this.l ??= []).push(t3);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(t3, s4 = b) {
    if (s4.state && (s4.attribute = false), this._$Ei(), this.prototype.hasOwnProperty(t3) && ((s4 = Object.create(s4)).wrapped = true), this.elementProperties.set(t3, s4), !s4.noAccessor) {
      const i5 = Symbol(), h3 = this.getPropertyDescriptor(t3, i5, s4);
      void 0 !== h3 && e2(this.prototype, t3, h3);
    }
  }
  static getPropertyDescriptor(t3, s4, i5) {
    const { get: e4, set: r4 } = h(this.prototype, t3) ?? { get() {
      return this[s4];
    }, set(t4) {
      this[s4] = t4;
    } };
    return { get: e4, set(s5) {
      const h3 = e4?.call(this);
      r4?.call(this, s5), this.requestUpdate(t3, h3, i5);
    }, configurable: true, enumerable: true };
  }
  static getPropertyOptions(t3) {
    return this.elementProperties.get(t3) ?? b;
  }
  static _$Ei() {
    if (this.hasOwnProperty(d("elementProperties"))) return;
    const t3 = n2(this);
    t3.finalize(), void 0 !== t3.l && (this.l = [...t3.l]), this.elementProperties = new Map(t3.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(d("finalized"))) return;
    if (this.finalized = true, this._$Ei(), this.hasOwnProperty(d("properties"))) {
      const t4 = this.properties, s4 = [...r2(t4), ...o2(t4)];
      for (const i5 of s4) this.createProperty(i5, t4[i5]);
    }
    const t3 = this[Symbol.metadata];
    if (null !== t3) {
      const s4 = litPropertyMetadata.get(t3);
      if (void 0 !== s4) for (const [t4, i5] of s4) this.elementProperties.set(t4, i5);
    }
    this._$Eh = /* @__PURE__ */ new Map();
    for (const [t4, s4] of this.elementProperties) {
      const i5 = this._$Eu(t4, s4);
      void 0 !== i5 && this._$Eh.set(i5, t4);
    }
    this.elementStyles = this.finalizeStyles(this.styles);
  }
  static finalizeStyles(s4) {
    const i5 = [];
    if (Array.isArray(s4)) {
      const e4 = new Set(s4.flat(1 / 0).reverse());
      for (const s5 of e4) i5.unshift(c(s5));
    } else void 0 !== s4 && i5.push(c(s4));
    return i5;
  }
  static _$Eu(t3, s4) {
    const i5 = s4.attribute;
    return false === i5 ? void 0 : "string" == typeof i5 ? i5 : "string" == typeof t3 ? t3.toLowerCase() : void 0;
  }
  constructor() {
    super(), this._$Ep = void 0, this.isUpdatePending = false, this.hasUpdated = false, this._$Em = null, this._$Ev();
  }
  _$Ev() {
    this._$ES = new Promise((t3) => this.enableUpdating = t3), this._$AL = /* @__PURE__ */ new Map(), this._$E_(), this.requestUpdate(), this.constructor.l?.forEach((t3) => t3(this));
  }
  addController(t3) {
    (this._$EO ??= /* @__PURE__ */ new Set()).add(t3), void 0 !== this.renderRoot && this.isConnected && t3.hostConnected?.();
  }
  removeController(t3) {
    this._$EO?.delete(t3);
  }
  _$E_() {
    const t3 = /* @__PURE__ */ new Map(), s4 = this.constructor.elementProperties;
    for (const i5 of s4.keys()) this.hasOwnProperty(i5) && (t3.set(i5, this[i5]), delete this[i5]);
    t3.size > 0 && (this._$Ep = t3);
  }
  createRenderRoot() {
    const t3 = this.shadowRoot ?? this.attachShadow(this.constructor.shadowRootOptions);
    return S(t3, this.constructor.elementStyles), t3;
  }
  connectedCallback() {
    this.renderRoot ??= this.createRenderRoot(), this.enableUpdating(true), this._$EO?.forEach((t3) => t3.hostConnected?.());
  }
  enableUpdating(t3) {
  }
  disconnectedCallback() {
    this._$EO?.forEach((t3) => t3.hostDisconnected?.());
  }
  attributeChangedCallback(t3, s4, i5) {
    this._$AK(t3, i5);
  }
  _$ET(t3, s4) {
    const i5 = this.constructor.elementProperties.get(t3), e4 = this.constructor._$Eu(t3, i5);
    if (void 0 !== e4 && true === i5.reflect) {
      const h3 = (void 0 !== i5.converter?.toAttribute ? i5.converter : u).toAttribute(s4, i5.type);
      this._$Em = t3, null == h3 ? this.removeAttribute(e4) : this.setAttribute(e4, h3), this._$Em = null;
    }
  }
  _$AK(t3, s4) {
    const i5 = this.constructor, e4 = i5._$Eh.get(t3);
    if (void 0 !== e4 && this._$Em !== e4) {
      const t4 = i5.getPropertyOptions(e4), h3 = "function" == typeof t4.converter ? { fromAttribute: t4.converter } : void 0 !== t4.converter?.fromAttribute ? t4.converter : u;
      this._$Em = e4;
      const r4 = h3.fromAttribute(s4, t4.type);
      this[e4] = r4 ?? this._$Ej?.get(e4) ?? r4, this._$Em = null;
    }
  }
  requestUpdate(t3, s4, i5, e4 = false, h3) {
    if (void 0 !== t3) {
      const r4 = this.constructor;
      if (false === e4 && (h3 = this[t3]), i5 ??= r4.getPropertyOptions(t3), !((i5.hasChanged ?? f)(h3, s4) || i5.useDefault && i5.reflect && h3 === this._$Ej?.get(t3) && !this.hasAttribute(r4._$Eu(t3, i5)))) return;
      this.C(t3, s4, i5);
    }
    false === this.isUpdatePending && (this._$ES = this._$EP());
  }
  C(t3, s4, { useDefault: i5, reflect: e4, wrapped: h3 }, r4) {
    i5 && !(this._$Ej ??= /* @__PURE__ */ new Map()).has(t3) && (this._$Ej.set(t3, r4 ?? s4 ?? this[t3]), true !== h3 || void 0 !== r4) || (this._$AL.has(t3) || (this.hasUpdated || i5 || (s4 = void 0), this._$AL.set(t3, s4)), true === e4 && this._$Em !== t3 && (this._$Eq ??= /* @__PURE__ */ new Set()).add(t3));
  }
  async _$EP() {
    this.isUpdatePending = true;
    try {
      await this._$ES;
    } catch (t4) {
      Promise.reject(t4);
    }
    const t3 = this.scheduleUpdate();
    return null != t3 && await t3, !this.isUpdatePending;
  }
  scheduleUpdate() {
    return this.performUpdate();
  }
  performUpdate() {
    if (!this.isUpdatePending) return;
    if (!this.hasUpdated) {
      if (this.renderRoot ??= this.createRenderRoot(), this._$Ep) {
        for (const [t5, s5] of this._$Ep) this[t5] = s5;
        this._$Ep = void 0;
      }
      const t4 = this.constructor.elementProperties;
      if (t4.size > 0) for (const [s5, i5] of t4) {
        const { wrapped: t5 } = i5, e4 = this[s5];
        true !== t5 || this._$AL.has(s5) || void 0 === e4 || this.C(s5, void 0, i5, e4);
      }
    }
    let t3 = false;
    const s4 = this._$AL;
    try {
      t3 = this.shouldUpdate(s4), t3 ? (this.willUpdate(s4), this._$EO?.forEach((t4) => t4.hostUpdate?.()), this.update(s4)) : this._$EM();
    } catch (s5) {
      throw t3 = false, this._$EM(), s5;
    }
    t3 && this._$AE(s4);
  }
  willUpdate(t3) {
  }
  _$AE(t3) {
    this._$EO?.forEach((t4) => t4.hostUpdated?.()), this.hasUpdated || (this.hasUpdated = true, this.firstUpdated(t3)), this.updated(t3);
  }
  _$EM() {
    this._$AL = /* @__PURE__ */ new Map(), this.isUpdatePending = false;
  }
  get updateComplete() {
    return this.getUpdateComplete();
  }
  getUpdateComplete() {
    return this._$ES;
  }
  shouldUpdate(t3) {
    return true;
  }
  update(t3) {
    this._$Eq &&= this._$Eq.forEach((t4) => this._$ET(t4, this[t4])), this._$EM();
  }
  updated(t3) {
  }
  firstUpdated(t3) {
  }
};
y.elementStyles = [], y.shadowRootOptions = { mode: "open" }, y[d("elementProperties")] = /* @__PURE__ */ new Map(), y[d("finalized")] = /* @__PURE__ */ new Map(), p?.({ ReactiveElement: y }), (a.reactiveElementVersions ??= []).push("2.1.2");

// node_modules/.pnpm/lit-html@3.3.3/node_modules/lit-html/lit-html.js
var t2 = globalThis;
var i3 = (t3) => t3;
var s2 = t2.trustedTypes;
var e3 = s2 ? s2.createPolicy("lit-html", { createHTML: (t3) => t3 }) : void 0;
var h2 = "$lit$";
var o3 = `lit$${Math.random().toFixed(9).slice(2)}$`;
var n3 = "?" + o3;
var r3 = `<${n3}>`;
var l2 = document;
var c3 = () => l2.createComment("");
var a2 = (t3) => null === t3 || "object" != typeof t3 && "function" != typeof t3;
var u2 = Array.isArray;
var d2 = (t3) => u2(t3) || "function" == typeof t3?.[Symbol.iterator];
var f2 = "[ 	\n\f\r]";
var v = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g;
var _ = /-->/g;
var m = />/g;
var p2 = RegExp(`>|${f2}(?:([^\\s"'>=/]+)(${f2}*=${f2}*(?:[^
\f\r"'\`<>=]|("|')|))|$)`, "g");
var g = /'/g;
var $ = /"/g;
var y2 = /^(?:script|style|textarea|title)$/i;
var x = (t3) => (i5, ...s4) => ({ _$litType$: t3, strings: i5, values: s4 });
var b2 = x(1);
var w = x(2);
var T = x(3);
var E = Symbol.for("lit-noChange");
var A = Symbol.for("lit-nothing");
var C = /* @__PURE__ */ new WeakMap();
var P = l2.createTreeWalker(l2, 129);
function V(t3, i5) {
  if (!u2(t3) || !t3.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return void 0 !== e3 ? e3.createHTML(i5) : i5;
}
var N = (t3, i5) => {
  const s4 = t3.length - 1, e4 = [];
  let n4, l3 = 2 === i5 ? "<svg>" : 3 === i5 ? "<math>" : "", c4 = v;
  for (let i6 = 0; i6 < s4; i6++) {
    const s5 = t3[i6];
    let a3, u3, d3 = -1, f3 = 0;
    for (; f3 < s5.length && (c4.lastIndex = f3, u3 = c4.exec(s5), null !== u3); ) f3 = c4.lastIndex, c4 === v ? "!--" === u3[1] ? c4 = _ : void 0 !== u3[1] ? c4 = m : void 0 !== u3[2] ? (y2.test(u3[2]) && (n4 = RegExp("</" + u3[2], "g")), c4 = p2) : void 0 !== u3[3] && (c4 = p2) : c4 === p2 ? ">" === u3[0] ? (c4 = n4 ?? v, d3 = -1) : void 0 === u3[1] ? d3 = -2 : (d3 = c4.lastIndex - u3[2].length, a3 = u3[1], c4 = void 0 === u3[3] ? p2 : '"' === u3[3] ? $ : g) : c4 === $ || c4 === g ? c4 = p2 : c4 === _ || c4 === m ? c4 = v : (c4 = p2, n4 = void 0);
    const x2 = c4 === p2 && t3[i6 + 1].startsWith("/>") ? " " : "";
    l3 += c4 === v ? s5 + r3 : d3 >= 0 ? (e4.push(a3), s5.slice(0, d3) + h2 + s5.slice(d3) + o3 + x2) : s5 + o3 + (-2 === d3 ? i6 : x2);
  }
  return [V(t3, l3 + (t3[s4] || "<?>") + (2 === i5 ? "</svg>" : 3 === i5 ? "</math>" : "")), e4];
};
var S2 = class _S {
  constructor({ strings: t3, _$litType$: i5 }, e4) {
    let r4;
    this.parts = [];
    let l3 = 0, a3 = 0;
    const u3 = t3.length - 1, d3 = this.parts, [f3, v2] = N(t3, i5);
    if (this.el = _S.createElement(f3, e4), P.currentNode = this.el.content, 2 === i5 || 3 === i5) {
      const t4 = this.el.content.firstChild;
      t4.replaceWith(...t4.childNodes);
    }
    for (; null !== (r4 = P.nextNode()) && d3.length < u3; ) {
      if (1 === r4.nodeType) {
        if (r4.hasAttributes()) for (const t4 of r4.getAttributeNames()) if (t4.endsWith(h2)) {
          const i6 = v2[a3++], s4 = r4.getAttribute(t4).split(o3), e5 = /([.?@])?(.*)/.exec(i6);
          d3.push({ type: 1, index: l3, name: e5[2], strings: s4, ctor: "." === e5[1] ? I : "?" === e5[1] ? L : "@" === e5[1] ? z : H }), r4.removeAttribute(t4);
        } else t4.startsWith(o3) && (d3.push({ type: 6, index: l3 }), r4.removeAttribute(t4));
        if (y2.test(r4.tagName)) {
          const t4 = r4.textContent.split(o3), i6 = t4.length - 1;
          if (i6 > 0) {
            r4.textContent = s2 ? s2.emptyScript : "";
            for (let s4 = 0; s4 < i6; s4++) r4.append(t4[s4], c3()), P.nextNode(), d3.push({ type: 2, index: ++l3 });
            r4.append(t4[i6], c3());
          }
        }
      } else if (8 === r4.nodeType) if (r4.data === n3) d3.push({ type: 2, index: l3 });
      else {
        let t4 = -1;
        for (; -1 !== (t4 = r4.data.indexOf(o3, t4 + 1)); ) d3.push({ type: 7, index: l3 }), t4 += o3.length - 1;
      }
      l3++;
    }
  }
  static createElement(t3, i5) {
    const s4 = l2.createElement("template");
    return s4.innerHTML = t3, s4;
  }
};
function M(t3, i5, s4 = t3, e4) {
  if (i5 === E) return i5;
  let h3 = void 0 !== e4 ? s4._$Co?.[e4] : s4._$Cl;
  const o5 = a2(i5) ? void 0 : i5._$litDirective$;
  return h3?.constructor !== o5 && (h3?._$AO?.(false), void 0 === o5 ? h3 = void 0 : (h3 = new o5(t3), h3._$AT(t3, s4, e4)), void 0 !== e4 ? (s4._$Co ??= [])[e4] = h3 : s4._$Cl = h3), void 0 !== h3 && (i5 = M(t3, h3._$AS(t3, i5.values), h3, e4)), i5;
}
var R = class {
  constructor(t3, i5) {
    this._$AV = [], this._$AN = void 0, this._$AD = t3, this._$AM = i5;
  }
  get parentNode() {
    return this._$AM.parentNode;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  u(t3) {
    const { el: { content: i5 }, parts: s4 } = this._$AD, e4 = (t3?.creationScope ?? l2).importNode(i5, true);
    P.currentNode = e4;
    let h3 = P.nextNode(), o5 = 0, n4 = 0, r4 = s4[0];
    for (; void 0 !== r4; ) {
      if (o5 === r4.index) {
        let i6;
        2 === r4.type ? i6 = new k(h3, h3.nextSibling, this, t3) : 1 === r4.type ? i6 = new r4.ctor(h3, r4.name, r4.strings, this, t3) : 6 === r4.type && (i6 = new Z(h3, this, t3)), this._$AV.push(i6), r4 = s4[++n4];
      }
      o5 !== r4?.index && (h3 = P.nextNode(), o5++);
    }
    return P.currentNode = l2, e4;
  }
  p(t3) {
    let i5 = 0;
    for (const s4 of this._$AV) void 0 !== s4 && (void 0 !== s4.strings ? (s4._$AI(t3, s4, i5), i5 += s4.strings.length - 2) : s4._$AI(t3[i5])), i5++;
  }
};
var k = class _k {
  get _$AU() {
    return this._$AM?._$AU ?? this._$Cv;
  }
  constructor(t3, i5, s4, e4) {
    this.type = 2, this._$AH = A, this._$AN = void 0, this._$AA = t3, this._$AB = i5, this._$AM = s4, this.options = e4, this._$Cv = e4?.isConnected ?? true;
  }
  get parentNode() {
    let t3 = this._$AA.parentNode;
    const i5 = this._$AM;
    return void 0 !== i5 && 11 === t3?.nodeType && (t3 = i5.parentNode), t3;
  }
  get startNode() {
    return this._$AA;
  }
  get endNode() {
    return this._$AB;
  }
  _$AI(t3, i5 = this) {
    t3 = M(this, t3, i5), a2(t3) ? t3 === A || null == t3 || "" === t3 ? (this._$AH !== A && this._$AR(), this._$AH = A) : t3 !== this._$AH && t3 !== E && this._(t3) : void 0 !== t3._$litType$ ? this.$(t3) : void 0 !== t3.nodeType ? this.T(t3) : d2(t3) ? this.k(t3) : this._(t3);
  }
  O(t3) {
    return this._$AA.parentNode.insertBefore(t3, this._$AB);
  }
  T(t3) {
    this._$AH !== t3 && (this._$AR(), this._$AH = this.O(t3));
  }
  _(t3) {
    this._$AH !== A && a2(this._$AH) ? this._$AA.nextSibling.data = t3 : this.T(l2.createTextNode(t3)), this._$AH = t3;
  }
  $(t3) {
    const { values: i5, _$litType$: s4 } = t3, e4 = "number" == typeof s4 ? this._$AC(t3) : (void 0 === s4.el && (s4.el = S2.createElement(V(s4.h, s4.h[0]), this.options)), s4);
    if (this._$AH?._$AD === e4) this._$AH.p(i5);
    else {
      const t4 = new R(e4, this), s5 = t4.u(this.options);
      t4.p(i5), this.T(s5), this._$AH = t4;
    }
  }
  _$AC(t3) {
    let i5 = C.get(t3.strings);
    return void 0 === i5 && C.set(t3.strings, i5 = new S2(t3)), i5;
  }
  k(t3) {
    u2(this._$AH) || (this._$AH = [], this._$AR());
    const i5 = this._$AH;
    let s4, e4 = 0;
    for (const h3 of t3) e4 === i5.length ? i5.push(s4 = new _k(this.O(c3()), this.O(c3()), this, this.options)) : s4 = i5[e4], s4._$AI(h3), e4++;
    e4 < i5.length && (this._$AR(s4 && s4._$AB.nextSibling, e4), i5.length = e4);
  }
  _$AR(t3 = this._$AA.nextSibling, s4) {
    for (this._$AP?.(false, true, s4); t3 !== this._$AB; ) {
      const s5 = i3(t3).nextSibling;
      i3(t3).remove(), t3 = s5;
    }
  }
  setConnected(t3) {
    void 0 === this._$AM && (this._$Cv = t3, this._$AP?.(t3));
  }
};
var H = class {
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  constructor(t3, i5, s4, e4, h3) {
    this.type = 1, this._$AH = A, this._$AN = void 0, this.element = t3, this.name = i5, this._$AM = e4, this.options = h3, s4.length > 2 || "" !== s4[0] || "" !== s4[1] ? (this._$AH = Array(s4.length - 1).fill(new String()), this.strings = s4) : this._$AH = A;
  }
  _$AI(t3, i5 = this, s4, e4) {
    const h3 = this.strings;
    let o5 = false;
    if (void 0 === h3) t3 = M(this, t3, i5, 0), o5 = !a2(t3) || t3 !== this._$AH && t3 !== E, o5 && (this._$AH = t3);
    else {
      const e5 = t3;
      let n4, r4;
      for (t3 = h3[0], n4 = 0; n4 < h3.length - 1; n4++) r4 = M(this, e5[s4 + n4], i5, n4), r4 === E && (r4 = this._$AH[n4]), o5 ||= !a2(r4) || r4 !== this._$AH[n4], r4 === A ? t3 = A : t3 !== A && (t3 += (r4 ?? "") + h3[n4 + 1]), this._$AH[n4] = r4;
    }
    o5 && !e4 && this.j(t3);
  }
  j(t3) {
    t3 === A ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, t3 ?? "");
  }
};
var I = class extends H {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(t3) {
    this.element[this.name] = t3 === A ? void 0 : t3;
  }
};
var L = class extends H {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(t3) {
    this.element.toggleAttribute(this.name, !!t3 && t3 !== A);
  }
};
var z = class extends H {
  constructor(t3, i5, s4, e4, h3) {
    super(t3, i5, s4, e4, h3), this.type = 5;
  }
  _$AI(t3, i5 = this) {
    if ((t3 = M(this, t3, i5, 0) ?? A) === E) return;
    const s4 = this._$AH, e4 = t3 === A && s4 !== A || t3.capture !== s4.capture || t3.once !== s4.once || t3.passive !== s4.passive, h3 = t3 !== A && (s4 === A || e4);
    e4 && this.element.removeEventListener(this.name, this, s4), h3 && this.element.addEventListener(this.name, this, t3), this._$AH = t3;
  }
  handleEvent(t3) {
    "function" == typeof this._$AH ? this._$AH.call(this.options?.host ?? this.element, t3) : this._$AH.handleEvent(t3);
  }
};
var Z = class {
  constructor(t3, i5, s4) {
    this.element = t3, this.type = 6, this._$AN = void 0, this._$AM = i5, this.options = s4;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(t3) {
    M(this, t3);
  }
};
var B = t2.litHtmlPolyfillSupport;
B?.(S2, k), (t2.litHtmlVersions ??= []).push("3.3.3");
var D = (t3, i5, s4) => {
  const e4 = s4?.renderBefore ?? i5;
  let h3 = e4._$litPart$;
  if (void 0 === h3) {
    const t4 = s4?.renderBefore ?? null;
    e4._$litPart$ = h3 = new k(i5.insertBefore(c3(), t4), t4, void 0, s4 ?? {});
  }
  return h3._$AI(t3), h3;
};

// node_modules/.pnpm/lit-element@4.2.2/node_modules/lit-element/lit-element.js
var s3 = globalThis;
var i4 = class extends y {
  constructor() {
    super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
  }
  createRenderRoot() {
    const t3 = super.createRenderRoot();
    return this.renderOptions.renderBefore ??= t3.firstChild, t3;
  }
  update(t3) {
    const r4 = this.render();
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(t3), this._$Do = D(r4, this.renderRoot, this.renderOptions);
  }
  connectedCallback() {
    super.connectedCallback(), this._$Do?.setConnected(true);
  }
  disconnectedCallback() {
    super.disconnectedCallback(), this._$Do?.setConnected(false);
  }
  render() {
    return E;
  }
};
i4._$litElement$ = true, i4["finalized"] = true, s3.litElementHydrateSupport?.({ LitElement: i4 });
var o4 = s3.litElementPolyfillSupport;
o4?.({ LitElement: i4 });
(s3.litElementVersions ??= []).push("4.2.2");

// custom_components/urdb/frontend/src/urdb-card.js
var INTEGRATION_VERSION = "0.4.1";
var DEFAULT_CONFIG = {
  status_entity: "sensor.urdb_status",
  changes_entity: "sensor.urdb_changes",
  check_entity: "button.check",
  update_entity: "button.update",
  restart_entity: "button.restart"
};
var TEXT = {
  en: {
    title: "Universal Routing Database",
    integration: "Integration",
    routing: "Routing",
    status: "Status",
    health: "Health",
    github: "GitHub status",
    current: "Current version",
    latest: "Latest version",
    updateAvailable: "Update available",
    lastCheck: "Last check",
    yes: "Yes",
    no: "No",
    healthy: "Healthy",
    unavailable: "Unavailable",
    upToDate: "System is up to date",
    updateReady: "Routing update available",
    releaseNotes: "Release notes",
    noNotes: "No release notes provided",
    cachedWarning: "GitHub rate limit reached. Cached release data is being used; URDB remains healthy.",
    check: "Check updates",
    update: "Update",
    restart: "Restart",
    activity: "Activity",
    noActivity: "No actions executed in this session",
    running: "Running",
    completed: "Completed",
    failed: "Failed",
    checking: "Checking for updates",
    updating: "Updating URDB",
    restarting: "Restarting URDB",
    cpu: "CPU",
    memory: "Memory",
    uptime: "Uptime"
  },
  ru: {
    title: "Universal Routing Database",
    integration: "\u0418\u043D\u0442\u0435\u0433\u0440\u0430\u0446\u0438\u044F",
    routing: "\u041C\u0430\u0440\u0448\u0440\u0443\u0442\u0438\u0437\u0430\u0446\u0438\u044F",
    status: "\u0421\u043E\u0441\u0442\u043E\u044F\u043D\u0438\u0435",
    health: "\u0417\u0434\u043E\u0440\u043E\u0432\u044C\u0435",
    github: "\u0421\u0442\u0430\u0442\u0443\u0441 GitHub",
    current: "\u0422\u0435\u043A\u0443\u0449\u0430\u044F \u0432\u0435\u0440\u0441\u0438\u044F",
    latest: "\u041F\u043E\u0441\u043B\u0435\u0434\u043D\u044F\u044F \u0432\u0435\u0440\u0441\u0438\u044F",
    updateAvailable: "\u0414\u043E\u0441\u0442\u0443\u043F\u043D\u043E \u043E\u0431\u043D\u043E\u0432\u043B\u0435\u043D\u0438\u0435",
    lastCheck: "\u041F\u043E\u0441\u043B\u0435\u0434\u043D\u044F\u044F \u043F\u0440\u043E\u0432\u0435\u0440\u043A\u0430",
    yes: "\u0414\u0430",
    no: "\u041D\u0435\u0442",
    healthy: "\u0420\u0430\u0431\u043E\u0442\u0430\u0435\u0442",
    unavailable: "\u041D\u0435\u0434\u043E\u0441\u0442\u0443\u043F\u0435\u043D",
    upToDate: "\u0421\u0438\u0441\u0442\u0435\u043C\u0430 \u0430\u043A\u0442\u0443\u0430\u043B\u044C\u043D\u0430",
    updateReady: "\u0414\u043E\u0441\u0442\u0443\u043F\u043D\u043E \u043E\u0431\u043D\u043E\u0432\u043B\u0435\u043D\u0438\u0435 \u043C\u0430\u0440\u0448\u0440\u0443\u0442\u0438\u0437\u0430\u0446\u0438\u0438",
    releaseNotes: "\u0418\u0437\u043C\u0435\u043D\u0435\u043D\u0438\u044F",
    noNotes: "\u041E\u043F\u0438\u0441\u0430\u043D\u0438\u0435 \u0438\u0437\u043C\u0435\u043D\u0435\u043D\u0438\u0439 \u043E\u0442\u0441\u0443\u0442\u0441\u0442\u0432\u0443\u0435\u0442",
    cachedWarning: "\u0414\u043E\u0441\u0442\u0438\u0433\u043D\u0443\u0442 \u043B\u0438\u043C\u0438\u0442 GitHub. \u0418\u0441\u043F\u043E\u043B\u044C\u0437\u0443\u044E\u0442\u0441\u044F \u043A\u044D\u0448\u0438\u0440\u043E\u0432\u0430\u043D\u043D\u044B\u0435 \u0434\u0430\u043D\u043D\u044B\u0435; URDB \u043F\u0440\u043E\u0434\u043E\u043B\u0436\u0430\u0435\u0442 \u0440\u0430\u0431\u043E\u0442\u0430\u0442\u044C.",
    check: "\u041F\u0440\u043E\u0432\u0435\u0440\u0438\u0442\u044C",
    update: "\u041E\u0431\u043D\u043E\u0432\u0438\u0442\u044C",
    restart: "\u041F\u0435\u0440\u0435\u0437\u0430\u043F\u0443\u0441\u0442\u0438\u0442\u044C",
    activity: "\u0410\u043A\u0442\u0438\u0432\u043D\u043E\u0441\u0442\u044C",
    noActivity: "\u0412 \u044D\u0442\u043E\u0439 \u0441\u0435\u0441\u0441\u0438\u0438 \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u0439 \u0435\u0449\u0451 \u043D\u0435 \u0431\u044B\u043B\u043E",
    running: "\u0412\u044B\u043F\u043E\u043B\u043D\u044F\u0435\u0442\u0441\u044F",
    completed: "\u0417\u0430\u0432\u0435\u0440\u0448\u0435\u043D\u043E",
    failed: "\u041E\u0448\u0438\u0431\u043A\u0430",
    checking: "\u041F\u0440\u043E\u0432\u0435\u0440\u043A\u0430 \u043E\u0431\u043D\u043E\u0432\u043B\u0435\u043D\u0438\u0439",
    updating: "\u041E\u0431\u043D\u043E\u0432\u043B\u0435\u043D\u0438\u0435 URDB",
    restarting: "\u041F\u0435\u0440\u0435\u0437\u0430\u043F\u0443\u0441\u043A URDB",
    cpu: "CPU",
    memory: "\u041F\u0430\u043C\u044F\u0442\u044C",
    uptime: "\u0412\u0440\u0435\u043C\u044F \u0440\u0430\u0431\u043E\u0442\u044B"
  }
};
var URDBCard = class extends i4 {
  static properties = {
    hass: { attribute: false },
    _operation: { state: true },
    _progress: { state: true },
    _lastAction: { state: true },
    _error: { state: true }
  };
  static styles = i`
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
    .error { color:var(--error-color); font-size:12px; margin-top:10px; }
    .actions { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; padding:0 22px 22px; }
    ha-progress-button { width:100%; } ha-progress-button ha-icon { margin-right:6px; --mdc-icon-size:19px; }
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
  static getStubConfig() {
    return { ...DEFAULT_CONFIG };
  }
  static getConfigElement() {
    return document.createElement("urdb-card-editor");
  }
  setConfig(config) {
    this._config = { ...DEFAULT_CONFIG, ...config };
    this.requestUpdate();
  }
  getCardSize() {
    return 9;
  }
  disconnectedCallback() {
    super.disconnectedCallback();
    clearInterval(this._timer);
  }
  _state(entityId) {
    return this.hass?.states?.[entityId];
  }
  _strings() {
    return TEXT[this.hass?.locale?.language === "ru" ? "ru" : "en"];
  }
  _formatDate(value) {
    if (!value) return "\u2014";
    const date = new Date(value);
    if (Number.isNaN(date.valueOf())) return value;
    return new Intl.DateTimeFormat(this.hass?.locale?.language || void 0, { dateStyle: "medium", timeStyle: "short" }).format(date);
  }
  _actionLabel(action, t3) {
    return { check: t3.checking, update: t3.updating, restart: t3.restarting }[action];
  }
  async _run(action) {
    if (this._operation || !this.hass) return;
    const entityId = this._config[`${action}_entity`];
    this._operation = action;
    this._progress = 6;
    this._error = null;
    this._lastAction = { action, state: "running", at: (/* @__PURE__ */ new Date()).toISOString() };
    clearInterval(this._timer);
    this._timer = setInterval(() => {
      this._progress = Math.min(92, this._progress + (this._progress < 55 ? 8 : 2));
    }, 700);
    try {
      await this.hass.callService("button", "press", { entity_id: entityId });
      this._progress = 100;
      this._lastAction = { action, state: "completed", at: (/* @__PURE__ */ new Date()).toISOString() };
    } catch (error) {
      this._error = error?.message || String(error);
      this._progress = 0;
      this._lastAction = { action, state: "failed", at: (/* @__PURE__ */ new Date()).toISOString() };
    } finally {
      clearInterval(this._timer);
      window.setTimeout(() => {
        this._operation = null;
        this._progress = 0;
        this._error = null;
      }, 1200);
    }
  }
  _metric(label, value) {
    return b2`<div class="metric"><div class="label">${label}</div><div class="value">${value ?? "\u2014"}</div></div>`;
  }
  render() {
    const t3 = this._strings();
    const status = this._state(this._config.status_entity);
    const changesState = this._state(this._config.changes_entity);
    const attributes = status?.attributes || {};
    const changesAttributes = changesState?.attributes || {};
    const changes = changesAttributes.changes || attributes.changes || [];
    const githubStatus = attributes.github_status || changesAttributes.github_status || "ok";
    const hasUpdate = Boolean(attributes.has_update);
    const health = status?.state || "unavailable";
    const healthTone = health !== "ok" ? "bad" : githubStatus !== "ok" ? "warn" : "good";
    const githubLabel = githubStatus === "rate_limited" ? "Rate limited \xB7 cached" : githubStatus === "ok" ? "Connected" : githubStatus;
    const activityState = this._lastAction ? { running: t3.running, completed: t3.completed, failed: t3.failed }[this._lastAction.state] : null;
    const resources = [[t3.cpu, attributes.cpu_percent, "%"], [t3.memory, attributes.memory_percent, "%"], [t3.uptime, attributes.uptime, ""]].filter(([, v2]) => v2 != null);
    return b2`<ha-card>
      <div class="header"><div class="identity"><div class="logo"><ha-icon icon="mdi:routes"></ha-icon></div><div>
        <h2>${t3.title}</h2><div class="versions"><span>${t3.integration}: v${INTEGRATION_VERSION}</span><span>${t3.routing}: ${attributes.current_version ?? "\u2014"}</span></div>
      </div></div><span class="health ${healthTone}">${health === "ok" ? t3.healthy : health}</span></div>
      ${githubStatus === "rate_limited" ? b2`<div class="warning"><ha-icon icon="mdi:database-clock-outline"></ha-icon><span>${t3.cachedWarning}</span></div>` : A}
      <section class="section"><h3 class="section-title">${t3.status}</h3><div class="grid">
        ${this._metric(t3.health, health === "ok" ? t3.healthy : t3.unavailable)}
        ${this._metric(t3.github, githubLabel)} ${this._metric(t3.current, attributes.current_version)}
        ${this._metric(t3.latest, attributes.latest_version)} ${this._metric(t3.updateAvailable, hasUpdate ? t3.yes : t3.no)}
        ${this._metric(t3.lastCheck, this._formatDate(attributes.checked_at))}
        ${resources.map(([label, value, suffix]) => this._metric(label, `${value}${suffix}`))}
      </div></section>
      ${hasUpdate ? b2`<section class="update-banner"><div class="update-head"><div><div class="update-title"><ha-icon icon="mdi:update"></ha-icon>${t3.updateReady}</div><div class="latest">${t3.latest}: ${attributes.latest_version ?? "\u2014"}</div></div>
        <ha-progress-button appearance="filled" data-action="update" .progress=${this._operation === "update"} ?disabled=${Boolean(this._operation)} @click=${() => this._run("update")}><ha-icon icon="mdi:download"></ha-icon>${t3.update}</ha-progress-button></div>
        <div class="notes"><strong>${t3.releaseNotes}</strong>${changes.length ? b2`<ul>${changes.slice(0, 10).map((item) => b2`<li>${item}</li>`)}</ul>` : b2`<div class="activity-detail">${t3.noNotes}</div>`}</div></section>` : b2`<div class="up-to-date good"><ha-icon icon="mdi:check-circle-outline"></ha-icon>${t3.upToDate}</div>`}
      <section class="section"><h3 class="section-title">${t3.activity}</h3><div class="activity"><div class="activity-main"><ha-icon icon="mdi:history"></ha-icon><div>
        <div class="value">${this._lastAction ? this._actionLabel(this._lastAction.action, t3) : t3.noActivity}</div>
        ${this._lastAction ? b2`<div class="activity-detail">${activityState} · ${this._formatDate(this._lastAction.at)}</div>` : A}
      </div></div>${this._operation ? b2`<strong>${this._progress}%</strong>` : A}</div>
      ${this._error ? b2`<div class="error" role="status" aria-live="polite">${this._error}</div>` : A}</section>
      <div class="actions">
        ${[["check", t3.check, "mdi:refresh"], ["update", t3.update, "mdi:download"], ["restart", t3.restart, "mdi:restart"]].map(([action, label, icon]) => b2`
          <ha-progress-button appearance="outlined" data-action=${action} .progress=${this._operation === action} ?disabled=${Boolean(this._operation)} @click=${() => this._run(action)}><ha-icon icon=${icon}></ha-icon>${label}</ha-progress-button>`)}
      </div>
    </ha-card>`;
  }
};
var URDBCardEditor = class extends i4 {
  static properties = { hass: { attribute: false } };
  static styles = i`.form { display:grid; gap:12px; padding:8px 0; }`;
  constructor() {
    super();
    this._config = { ...DEFAULT_CONFIG };
  }
  setConfig(config) {
    this._config = { ...DEFAULT_CONFIG, ...config };
    this.requestUpdate();
  }
  _changed(key, event) {
    this._config = { ...this._config, [key]: event.detail.value };
    this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: this._config }, bubbles: true, composed: true }));
  }
  render() {
    const fields = { status_entity: "Status", changes_entity: "Changes", check_entity: "Check updates", update_entity: "Update", restart_entity: "Restart" };
    return b2`<div class="form">${Object.entries(fields).map(([key, label]) => b2`
      <ha-entity-picker .hass=${this.hass} .value=${this._config[key]} .label=${label} @value-changed=${(event) => this._changed(key, event)}></ha-entity-picker>`)}
    </div>`;
  }
};
if (!customElements.get("urdb-card")) customElements.define("urdb-card", URDBCard);
if (!customElements.get("urdb-card-editor")) customElements.define("urdb-card-editor", URDBCardEditor);
window.customCards = window.customCards || [];
if (!window.customCards.some((card) => card.type === "urdb-card")) window.customCards.push({
  type: "urdb-card",
  name: "Universal Routing Database",
  description: "Native URDB status and update dashboard",
  preview: true
});
console.info(`%c URDB CARD %c v${INTEGRATION_VERSION} `, "color:white;background:#03a9f4;font-weight:bold", "color:#03a9f4;background:white");
/*! Bundled license information:

@lit/reactive-element/css-tag.js:
  (**
   * @license
   * Copyright 2019 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/reactive-element.js:
lit-html/lit-html.js:
lit-element/lit-element.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-html/is-server.js:
  (**
   * @license
   * Copyright 2022 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)
*/
