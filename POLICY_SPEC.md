# Canonical Routing Policy Language

Status: design proposal for schema version 1

Scope: client-neutral routing policy

Non-goal: implementation of any new routing backend

This document defines the canonical language used to describe routing intent.
The language is independent of Happ, Xray, sing-box, Clash/Mihomo, Keenetic,
operating systems, VPN protocols and configuration file formats.

The canonical policy answers only these questions:

1. What traffic is being described?
2. Which logical egress should handle it?
3. In which order are routing decisions evaluated?

Client-specific compilation, file names, outbound tags, interfaces, tunnel
types, DNS URLs and deployment commands do not belong in this language.

## 1. Design principles

### Client neutrality

A policy must not contain client syntax such as:

```text
geosite:youtube
geoip:ru
ext:geosite_custom.dat:proxy
PROXY
DIRECT
vpn0
```

These are backend representations. A canonical policy references typed
matchers, logical Objects, Sets, Categories and Egresses. Backend adapters map
them into their native representation.

### Explicit semantics

Every value that affects routing has a declared type. A string must not be
interpreted differently by different backends. For example, a domain suffix,
regular expression and domain keyword are different matcher types.

### Deterministic execution

Given the same normalized policy and the same connection metadata, evaluation
must produce the same logical egress. Source file order, priorities, disabled
rules and fallback behavior are precisely defined below.

### Fail closed during compilation

Unsupported features must produce a compilation error. A backend must never
silently drop a matcher, weaken a logical expression or replace an unknown
egress with a default route.

### Stable logical identity

Rules should normally reference logical Objects such as `youtube`, not repeat
provider domains in many policies. Domain ownership changes over time; the
meaning of the logical Object should remain stable.

### Reproducibility

External data must be resolved into versioned resources with provenance and a
digest before compilation. A policy build must be explainable from its source
version, resolved resources and target capabilities.

## 2. Document structure

The proposed top-level structure is:

```yaml
schema_version: 1
kind: RoutingPolicy

metadata:
  name: default-routing
  revision: 2026-07-14

egresses: {}
domain_sets: {}
ip_sets: {}
objects: {}
categories: {}
rules: []
fallback: internet
```

Required top-level fields:

- `schema_version` — major version of the canonical policy schema;
- `kind` — must be `RoutingPolicy`;
- `metadata.name` — stable human-readable policy identifier;
- `egresses` — declared logical destinations;
- `rules` — ordered rule declarations;
- `fallback` — logical egress selected when no enabled rule matches.

Optional top-level fields:

- `metadata.revision`, `description`, `owners` and labels;
- `domain_sets`;
- `ip_sets`;
- `objects`;
- `categories`.

Unknown fields are errors in schema version 1. This prevents misspellings from
silently changing routing behavior.

## 3. Core concepts

### Rule

A Rule is an independently identifiable routing decision. It contains:

- a unique `id`;
- an optional human-readable `description`;
- an optional integer `priority`;
- an optional `enabled` flag;
- one Matcher expression in `match`;
- one Action in `action`.

Example:

```yaml
- id: proxy-youtube
  description: Route YouTube through the privacy egress
  priority: 100
  enabled: true
  match:
    object: youtube
  action:
    egress: vpn
```

Rule IDs are stable API identifiers. They must be unique within the policy and
should not be renamed merely to improve prose. Logs, test reports, exceptions
and migrations use the ID.

### Matcher

A Matcher is a typed predicate evaluated against connection metadata. It
returns `true`, `false` or `unknown` during abstract analysis. At runtime, a
backend must produce behavior equivalent to the canonical boolean result.

A matcher expression is either:

- one typed leaf matcher;
- `any` containing child matchers;
- `all` containing child matchers;
- `not` containing exactly one child matcher.

Each mapping node must contain exactly one matcher key. Ambiguous nodes are
schema errors.

### Action

An Action is the outcome selected by a matching Rule. Schema version 1 defines
one canonical action:

```yaml
action:
  egress: logical-egress-name
```

The action chooses a declared logical Egress. It does not name a backend tag,
network interface or VPN implementation.

Future action types, such as marking traffic without terminating evaluation,
require a new schema version or an explicitly versioned capability. They must
not be added as undocumented generator behavior.

### Egress

An Egress is a named logical destination for traffic. The core treats its name
as an opaque identifier.

Examples:

```yaml
egresses:
  internet:
    description: Default public internet path
  vpn:
    description: Privacy-preserving path
  block:
    description: Traffic must not leave the device
  wan2:
    description: Secondary uplink
  office:
    description: Corporate network path
```

The word `vpn` has no built-in meaning. One target may map it to an Xray
outbound tag, another to a Clash proxy group, another to a sing-box outbound,
and another to a Keenetic policy or interface. Likewise, an egress called
`block` is not automatically a reject action: the target binding gives it that
behavior.

Every egress referenced by a Rule or `fallback` must be declared. Every enabled
egress used by a policy must have a target binding before compilation.

### Object

An Object is a stable logical identity representing a service, organization,
application or destination concept.

Examples:

- `youtube`;
- `github`;
- `gosuslugi`;
- `yandex`;
- `telegram`;
- `company-office`.

An Object can reference Domain Sets and IP Sets:

```yaml
objects:
  youtube:
    description: YouTube service
    domain_sets:
      - youtube-domains
    ip_sets:
      - youtube-addresses
```

Objects must not contain routing actions. The same Object may be routed through
different egresses in different policies.

### Domain Set

A Domain Set is a named, reusable collection of typed domain entries. Entries
may use exact domain, suffix, keyword or regular expression forms.

```yaml
domain_sets:
  youtube-domains:
    entries:
      - domain: youtube.com
      - domain_suffix: googlevideo.com
      - domain_suffix: ytimg.com
```

A Domain Set is data, not a Rule. It does not declare an egress, priority or
fallback.

A set may also be resolved from an external resource:

```yaml
domain_sets:
  advertising:
    source:
      provider: v2fly-geosite
      resource: category-ads-all
      revision: 0433b7a
      sha256: 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
```

The resolver must pin provenance before backend compilation. `revision` and
`sha256` shown above are illustrative; production values must refer to the
actual resolved artifact.

### IP Set

An IP Set is a named, reusable collection of typed address predicates:

```yaml
ip_sets:
  private-networks:
    entries:
      - cidr: 10.0.0.0/8
      - cidr: 172.16.0.0/12
      - cidr: 192.168.0.0/16
      - cidr: fc00::/7
```

Country and ASN entries may also be used when the resolved dataset and target
capabilities support them:

```yaml
ip_sets:
  example-network:
    entries:
      - country:
          code: RU
          direction: destination
      - asn:
          number: 15169
          direction: destination
```

### Category

A Category is a curated logical grouping of Objects. It expresses policy intent
at a higher level than a provider-maintained domain list.

```yaml
categories:
  social-media:
    objects:
      - vk
      - instagram
      - facebook

  developer-services:
    objects:
      - github
      - openai
```

Categories may reference Objects only in schema version 1. They do not directly
contain raw matcher entries and may not reference other Categories. This keeps
the dependency graph simple and prevents recursive category expansion.

`category-ads-all` from a geosite provider is a Domain Set, not automatically a
canonical Category. Provider terminology must not redefine the core model.

### Capability

A Capability is a versioned statement that a compiler target can preserve a
specific canonical semantic.

Examples:

```text
matcher.domain.exact/v1
matcher.domain.suffix/v1
matcher.domain.regex.re2/v1
matcher.ip.cidr/v1
matcher.ip.country/v1
matcher.ip.asn/v1
matcher.port.destination/v1
matcher.protocol/v1
matcher.process/v1
logic.any/v1
logic.all/v1
logic.not/v1
rules.priority/v1
egress.named/v1
```

Capabilities are not marketing labels. A backend declares only semantics it can
compile without weakening or changing them.

## 4. Rule execution model

### Normalization

Before evaluation or backend compilation, the core must:

1. validate the schema;
2. normalize identifiers and matcher values;
3. resolve Object, Category and Set references;
4. reject missing references and dependency cycles;
5. calculate effective Rule order;
6. calculate required capabilities;
7. compare them with target capabilities;
8. produce an immutable normalized policy or a structured error.

### Ordering and priorities

Rules are sorted by this deterministic key:

1. `priority`, descending;
2. declaration position in the source `rules` array, ascending.

`priority` is a signed 32-bit integer. Its default value is `0`. Rules with the
same priority preserve source order.

Example:

```yaml
rules:
  - id: normal-direct
    priority: 0
    match: {object: yandex}
    action: {egress: internet}

  - id: emergency-block
    priority: 1000
    match: {object: compromised-service}
    action: {egress: block}
```

`emergency-block` is evaluated first even though it is declared later.

Priorities should be used sparingly. Most policies should rely on visible source
order. Large unexplained priority values make review difficult.

### First match

The evaluation algorithm is:

```text
for rule in effective_order:
    if rule.enabled is false:
        continue
    if evaluate(rule.match, connection) is true:
        return rule.action.egress
return policy.fallback
```

Evaluation stops at the first matching enabled Rule. There is no implicit
merging of actions and no second pass.

### Fallback

`fallback` is mandatory and must reference a declared Egress:

```yaml
fallback: internet
```

Backends must compile fallback explicitly. They must not rely on an accidental
client default. If the backend cannot represent the requested fallback, target
compilation fails.

### Disabled rules

`enabled` defaults to `true`.

```yaml
- id: future-process-test
  enabled: false
  match:
    process: example-browser
  action:
    egress: vpn
```

Disabled rules:

- remain schema-valid and reference-valid;
- are ignored during runtime ordering and evaluation;
- are included in lint and migration output;
- do not contribute required backend capabilities;
- are not emitted to backend artifacts;
- must be visibly reported as disabled in compilation diagnostics.

This allows future rules to be reviewed without making current targets reject
the entire active policy.

## 5. Typed matcher model

### Common matcher rules

- Every matcher node contains exactly one key.
- Scalar matcher values are not implicitly split on commas or whitespace.
- Lists are expressed through `any` or Set references, not overloaded scalars.
- Matcher types and their normalization rules are part of the schema contract.
- A backend must preserve matcher meaning or fail capability validation.

### Domain

Exact domain match:

```yaml
match:
  domain: accounts.example.com
```

It matches `accounts.example.com` only. It does not match subdomains.

Normalization:

- lowercase;
- remove one trailing root dot;
- encode internationalized labels using IDNA ASCII form;
- reject URL schemes, paths and ports.

### Domain suffix

```yaml
match:
  domain_suffix: example.com
```

It matches `example.com` and every label-boundary subdomain such as
`www.example.com`. It does not match `notexample.com`.

### Domain keyword

```yaml
match:
  domain_keyword: googlevideo
```

It performs a case-insensitive substring match against the normalized ASCII
domain name. Empty keywords and whitespace-only keywords are invalid.

Keyword matching is intentionally explicit because it may overmatch unrelated
domains. Policy review should prefer exact and suffix matchers.

### Domain regular expression

```yaml
match:
  domain_regex:
    pattern: '(^|\\.)example-[0-9]+\\.com$'
    dialect: re2
```

Schema version 1 defines `re2` as the canonical portable regex dialect. Features
not supported by RE2, such as backreferences and lookbehind, are invalid.

A backend that cannot preserve the expression must reject
`matcher.domain.regex.re2/v1`; it may not approximate the regex with a keyword
or suffix.

### IP

Exact destination address:

```yaml
match:
  destination_ip: 203.0.113.10
```

Both IPv4 and IPv6 are supported. Addresses are normalized to their canonical
text form. IPv4-mapped IPv6 handling must be declared by the target capability.

The shorthand `ip` may be accepted by an authoring tool, but it must normalize
to `destination_ip` before validation and must not appear in normalized IR.

### CIDR

Destination prefix:

```yaml
match:
  destination_cidr: 203.0.113.0/24
```

Host bits outside the prefix are rejected rather than silently cleared. IPv4
and IPv6 prefixes are supported.

The shorthand `cidr` normalizes to `destination_cidr`.

### Country

```yaml
match:
  country:
    code: RU
    direction: destination
    ip_set: geo-country
```

- `code` uses uppercase ISO 3166-1 alpha-2;
- `direction` is `source` or `destination`;
- `ip_set` identifies the resolved dataset namespace.

Country matching is data-dependent. Compilation records the dataset revision
and digest. A bare country code with no resolved data source is invalid for a
reproducible release.

### ASN

```yaml
match:
  asn:
    number: 15169
    direction: destination
    ip_set: geo-asn
```

The ASN is an integer from 0 through 4294967295. `AS15169` may be accepted as an
authoring convenience but normalizes to integer `15169`.

### Port

```yaml
match:
  port:
    direction: destination
    value: 443
```

Port values range from 1 through 65535. `direction` must be explicit and is
either `source` or `destination`.

### Port range

```yaml
match:
  port_range:
    direction: destination
    from: 8000
    to: 8999
```

Both boundaries are inclusive. `from` must be less than or equal to `to`.

### Protocol

Application or detected protocol:

```yaml
match:
  protocol: tls
```

Initial registry values may include `http`, `tls`, `quic`, `dns` and
`bittorrent`. Protocol detection is not equivalent to a port test. A backend
must advertise the exact protocol capability it implements.

### Network

Transport or network family:

```yaml
match:
  network: tcp
```

Schema version 1 registry values are `tcp`, `udp` and `icmp`. Additional values
require a schema registry update. `network: tcp` does not imply any application
protocol.

### Source IP

Exact source address:

```yaml
match:
  source_ip: 192.0.2.10
```

Source prefix:

```yaml
match:
  source_cidr: 192.0.2.0/24
```

The source is the address observed by the routing engine. NAT and transparent
proxy placement can change what a backend can observe; capability validation
must account for this.

### Destination IP

Exact address and prefix use `destination_ip` and `destination_cidr`. The
destination is the address available at the rule-evaluation stage. A target must
declare whether the address is original, resolved or post-redirect if that
distinction affects semantics.

### Process — future

Proposed syntax:

```yaml
match:
  process:
    name: firefox
```

Potential future fields include executable path, signing identity and user ID.
Process matching is not active in the mandatory schema version 1 capability
baseline. It may appear in disabled rules for design and migration testing.

Process identity is platform-specific. A future capability must state whether
matching is by basename, full path, executable hash or OS process metadata.

### Package name — future

Proposed syntax:

```yaml
match:
  package_name: org.telegram.messenger
```

This matcher is intended for platforms such as Android. It is not equivalent to
a process name. It remains outside the mandatory version 1 baseline until its
normalization and platform identity rules are finalized.

## 6. Logical operators

### any

`any` is true when at least one child matcher is true:

```yaml
match:
  any:
    - object: youtube
    - object: github
    - category: social-media
```

`any` must contain at least two children. For one child, use the child directly.
An empty `any` is invalid.

### all

`all` is true only when every child matcher is true:

```yaml
match:
  all:
    - object: youtube
    - network: tcp
    - port:
        direction: destination
        value: 443
```

`all` must contain at least two children. An empty `all` is invalid.

### not

`not` negates exactly one child expression:

```yaml
match:
  all:
    - category: developer-services
    - not:
        source_cidr: 10.0.0.0/8
```

Backends must preserve boolean grouping. Flattening `not` or distributing it
across unsupported matchers without a proven equivalent transformation is
forbidden.

### Logical normalization

The core may perform semantics-preserving transformations such as flattening
nested `any` nodes. It must not reorder expressions when the target has side
effects, remove unknown matchers or apply transformations that change
three-valued analysis results.

Normalized output should retain source locations for diagnostics even if its
tree structure changes.

## 7. Object model

### Why Objects are required

This is fragile:

```yaml
match:
  domain: youtube.com
```

It describes one hostname, not YouTube as a service. YouTube also uses other
domains and IP ranges, and those resources change independently of routing
intent.

This is the preferred policy:

```yaml
match:
  object: youtube
```

The routing decision remains stable while the Object's resolved resources can
be reviewed and updated separately.

### Separation of concerns

```text
Rule       decides when and where traffic routes
Object     defines a stable logical destination identity
Domain Set contains domain evidence for an Object
IP Set     contains address evidence for an Object
Category   groups Objects by policy meaning
Target     maps logical Egresses and capabilities to a backend
```

### Object resolution

When a Rule references an Object, the core resolves it to:

```text
any(
  every entry in referenced Domain Sets,
  every entry in referenced IP Sets
)
```

An Object with no resolved entries is invalid when referenced by an enabled
Rule. Duplicate entries are deduplicated after normalization but reported as a
lint warning.

### Categories and Objects

A Category matcher expands to `any(object...)` using the Category's explicit
Object membership. Membership must be deterministic and version controlled.

Backends may use a native category or rule-provider optimization only when the
resolved membership and semantics are proven equivalent. Otherwise, the
compiler emits expanded rules or fails on target limits.

## 8. Egress model and target bindings

The core never knows what “VPN” means. It does not know tunnels, interfaces,
proxy protocols, routing tables or client-specific outbound tags.

Canonical policy:

```yaml
egresses:
  internet: {}
  vpn: {}
  block: {}
  wan2: {}
  office: {}
```

Illustrative target bindings, outside the canonical policy:

```yaml
target: xray
egress_bindings:
  internet: direct
  vpn: proxy
  block: reject
  office: corporate-outbound
```

```yaml
target: keenetic
egress_bindings:
  internet: ISP
  vpn: Wireguard0
  block: reject-policy
  wan2: ISP2
  office: OfficeTunnel
```

```yaml
target: clash-mihomo
egress_bindings:
  internet: DIRECT
  vpn: Privacy
  block: REJECT
  office: Corporate
```

These examples specify design intent only; they do not implement new backends.

### Binding validation

Compilation fails when:

- an enabled Rule references an undeclared Egress;
- `fallback` references an undeclared Egress;
- the target lacks a binding for a used Egress;
- two canonical Egresses map to one backend target where that would change
  observable policy semantics;
- the backend binding cannot implement the requested behavior.

Unused declared Egresses are allowed but produce a lint warning.

## 9. Capability model

### Purpose

The Capability model proves that a target can preserve policy semantics before
any artifact is emitted.

The compilation pipeline is:

```text
YAML
  -> schema validation
  -> canonical model
  -> reference resolution
  -> normalized IR
  -> required capability set
  -> target capability comparison
  -> backend lowering
  -> serialization
```

### Required capabilities

The core derives requirements only from enabled Rules, active Sets, used
Egresses and fallback. Disabled rules remain validated but do not block an
otherwise compatible target.

Example derived set:

```yaml
required_capabilities:
  - matcher.object/v1
  - matcher.domain.suffix/v1
  - matcher.port.destination/v1
  - logic.all/v1
  - rules.first-match/v1
  - rules.priority/v1
  - egress.named/v1
```

### Target capabilities

A target adapter exposes a machine-readable capability descriptor:

```yaml
backend: example
adapter_version: 1.2.0
policy_schema:
  minimum: 1
  maximum: 1
capabilities:
  matcher.domain.exact/v1: native
  matcher.domain.suffix/v1: native
  matcher.port.destination/v1: native
  logic.all/v1: lowered-equivalent
  matcher.process/v1: unsupported
limits:
  maximum_rules: 10000
  maximum_regex_length: 4096
```

Allowed support modes:

- `native` — backend directly expresses the semantic;
- `lowered-equivalent` — adapter has a tested equivalence-preserving lowering;
- `unsupported` — compilation must fail when required.

### Compilation failure

An unsupported capability produces a structured error before output files are
written:

```text
E_CAPABILITY_UNSUPPORTED
backend: happ
rule: browser-only-proxy
source: policy.yaml:84
capability: matcher.process/v1
message: enabled rule requires process matching, which this target cannot preserve
```

The compiler must not:

- omit the Rule;
- replace the Matcher with `true`;
- approximate it using a domain matcher;
- route it through fallback;
- emit a warning and continue.

### Limits as capabilities

Backend limits are validated after lowering but before serialization. Examples:

- maximum number of rules;
- maximum nesting depth;
- regular-expression dialect and size;
- number of named egresses;
- IPv6 support;
- external Set support;
- source metadata visibility.

Exceeding a hard limit is a compilation error unless a proven equivalent
optimization reduces the plan.

## 10. Validation rules

Schema version 1 requires:

- unique Rule, Object, Set, Category and Egress IDs within their namespaces;
- identifiers matching `^[a-z][a-z0-9-]{0,62}$`;
- all references to resolve;
- no duplicate normalized entries inside a Set;
- no empty enabled Object, Category or Set reference;
- no recursive references;
- exactly one matcher key per matcher node;
- exactly one canonical action per Rule;
- `fallback` to reference a declared Egress;
- priorities within signed 32-bit range;
- ports from 1 through 65535;
- valid canonical IP/CIDR values;
- valid IDNA domains;
- supported regex dialect;
- external resources to include immutable provenance before release compilation.

Lint warnings, which do not change semantics, may include:

- unused Egresses, Objects or Sets;
- duplicate entries before normalization;
- a high-priority Rule shadowing another Rule;
- broad keywords or regexes;
- Rules that can never match;
- Categories containing only one Object;
- excessive use of priorities instead of visible ordering.

## 11. Versioning and migration

### Schema version

`schema_version` is a positive integer major version:

```yaml
schema_version: 1
```

Within a schema major version:

- meaning of existing fields does not change;
- required fields are not added;
- previously valid values are not reinterpreted;
- new optional metadata may be added only when unknown-field handling can
  remain strict through a published schema revision;
- compiler bug fixes may reject input that never conformed to the written spec.

A semantic or structural breaking change increments the major version.

### Schema revision versus policy revision

Schema version and policy revision are different:

```yaml
schema_version: 1
metadata:
  revision: 2026-07-14.1
```

`schema_version` selects language semantics. `metadata.revision` identifies a
particular business-policy update and may use an organization-defined format.

### Backend compatibility

Each adapter declares the minimum and maximum schema versions it accepts. A
compiler must reject a newer unsupported schema even when all fields appear
familiar.

### Migration strategy

Migration from version N to N+1 must be performed by a dedicated, deterministic
migrator:

```text
routing-policy migrate --from 1 --to 2 policy.yaml
```

A migrator must:

- preserve the original file;
- create a new document or explicit patch;
- be deterministic and idempotent;
- emit a machine-readable migration report;
- list every changed field and affected Rule ID;
- stop for human decisions when semantics cannot be inferred;
- never silently choose a new egress, matcher or fallback;
- validate the migrated policy against the new schema;
- support semantic comparison tests where possible.

Migrations are sequential. Version 1 to version 3 runs the reviewed v1→v2 and
v2→v3 transforms rather than an untested direct rewrite.

### Deprecation

Deprecation requires:

1. documentation in the specification;
2. a compiler warning containing source location and replacement;
3. at least one stable release cycle before removal;
4. a migration rule;
5. removal only in a new schema major version when semantics are affected.

### Release reproducibility

A compiled release records:

- policy schema version;
- policy content digest;
- policy metadata revision;
- resolved resource revisions and digests;
- compiler version;
- backend adapter version;
- capability descriptor digest;
- normalized IR digest;
- source commit SHA.

## 12. Complete examples

### Example A: minimal policy

```yaml
schema_version: 1
kind: RoutingPolicy

metadata:
  name: minimal
  revision: 1

egresses:
  internet: {}
  vpn: {}

domain_sets:
  youtube-domains:
    entries:
      - domain: youtube.com
      - domain_suffix: googlevideo.com
      - domain_suffix: ytimg.com

objects:
  youtube:
    domain_sets:
      - youtube-domains

rules:
  - id: proxy-youtube
    match:
      object: youtube
    action:
      egress: vpn

fallback: internet
```

Semantics: YouTube uses logical egress `vpn`; all unmatched traffic uses
`internet`.

### Example B: DIRECT, PROXY and BLOCK intent

```yaml
schema_version: 1
kind: RoutingPolicy

metadata:
  name: household-routing
  revision: 2026-07-14

egresses:
  internet: {}
  vpn: {}
  block: {}

domain_sets:
  government-domains:
    entries:
      - domain_suffix: gosuslugi.ru
      - domain_suffix: nalog.gov.ru

  developer-domains:
    entries:
      - domain_suffix: github.com
      - domain_suffix: openai.com
      - domain_suffix: chatgpt.com

  advertising:
    source:
      provider: v2fly-geosite
      resource: category-ads-all
      revision: pinned-release-id
      sha256: pinned-release-sha256

objects:
  government-services:
    domain_sets: [government-domains]
  developer-services:
    domain_sets: [developer-domains]
  advertising:
    domain_sets: [advertising]

rules:
  - id: block-advertising
    priority: 100
    match: {object: advertising}
    action: {egress: block}

  - id: direct-government
    match: {object: government-services}
    action: {egress: internet}

  - id: proxy-developer-services
    match: {object: developer-services}
    action: {egress: vpn}

fallback: internet
```

`block` is still only a logical name. A target must explicitly bind it to a
rejecting backend construct.

### Example C: logical operators and ports

```yaml
schema_version: 1
kind: RoutingPolicy

metadata:
  name: protocol-aware-routing

egresses:
  internet: {}
  vpn: {}

domain_sets:
  media-domains:
    entries:
      - domain_suffix: example-streaming.test

objects:
  media-service:
    domain_sets: [media-domains]

rules:
  - id: proxy-media-https
    match:
      all:
        - object: media-service
        - network: tcp
        - port:
            direction: destination
            value: 443
        - not:
            source_cidr: 10.0.0.0/8
    action:
      egress: vpn

fallback: internet
```

The target must support `all`, `not`, source CIDR, TCP and destination-port
matching. Otherwise compilation fails before serialization.

### Example D: Categories

```yaml
schema_version: 1
kind: RoutingPolicy

metadata:
  name: category-routing

egresses:
  internet: {}
  vpn: {}

domain_sets:
  github-domains:
    entries:
      - domain_suffix: github.com
      - domain_suffix: githubusercontent.com
  openai-domains:
    entries:
      - domain_suffix: openai.com
      - domain_suffix: chatgpt.com

objects:
  github:
    domain_sets: [github-domains]
  openai:
    domain_sets: [openai-domains]

categories:
  developer-services:
    objects:
      - github
      - openai

rules:
  - id: proxy-developer-services
    match:
      category: developer-services
    action:
      egress: vpn

fallback: internet
```

### Example E: multiple logical egresses

```yaml
schema_version: 1
kind: RoutingPolicy

metadata:
  name: multi-egress-office

egresses:
  internet: {}
  vpn: {}
  wan2: {}
  office: {}
  block: {}

ip_sets:
  office-networks:
    entries:
      - cidr: 10.20.0.0/16

objects:
  office-network:
    ip_sets: [office-networks]

rules:
  - id: route-office
    priority: 200
    match: {object: office-network}
    action: {egress: office}

  - id: secondary-wan-dns
    match:
      all:
        - protocol: dns
        - network: udp
    action: {egress: wan2}

fallback: internet
```

The core does not know whether `office` is a tunnel or whether `wan2` is a
physical interface. Target bindings provide those meanings.

### Example F: disabled future matcher

```yaml
schema_version: 1
kind: RoutingPolicy

metadata:
  name: staged-future-rule

egresses:
  internet: {}
  vpn: {}

rules:
  - id: future-telegram-package
    enabled: false
    match:
      package_name: org.telegram.messenger
    action:
      egress: vpn

fallback: internet
```

The Rule is schema-checked and preserved, but it is not emitted and does not
require `matcher.package-name/v1` while disabled.

## 13. Non-goals for schema version 1

The following are intentionally outside the initial canonical language:

- backend configuration and deployment;
- DNS server definitions and DNS routing actions;
- health checks and automatic egress selection;
- load balancing;
- traffic accounting and quotas;
- time schedules;
- user authentication;
- packet marking;
- rule mutation at runtime;
- process and package matching in the mandatory capability baseline;
- backend-specific escape hatches embedded in canonical policy.

Target-specific settings may exist outside the canonical policy, but they must
not change its routing meaning. An escape hatch that changes routing semantics
must be modeled as a versioned core feature or rejected.

## 14. Conformance requirements

A policy parser conforms to schema version 1 when it:

- validates every rule in this document;
- rejects unknown or ambiguous fields;
- produces deterministic normalized IR;
- preserves source locations for errors;
- resolves logical references without cycles;
- derives required capabilities;
- never silently weakens policy semantics.

A backend adapter conforms when it:

- declares its supported schema range and capabilities;
- validates all used egress bindings;
- fails on unsupported semantics;
- lowers only through tested equivalence-preserving transforms;
- serializes deterministically;
- reports the source Rule ID for generated rules;
- passes contract and golden-file tests;
- records its version and capability digest in release metadata.

A release conforms when its artifacts can be traced to:

- one canonical policy revision;
- one normalized IR digest;
- pinned resource revisions;
- one source commit;
- declared backend adapter versions;
- successful policy, capability, artifact and integrity checks.

This specification should be reviewed and accepted before the current
action-bucket policy format becomes a public compatibility promise.
