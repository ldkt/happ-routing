# GAP ANALYSIS: implementation versus POLICY_SPEC.md

Status: implementation checklist for the first stable release
Baseline implementation: `main` at `df2684b`
Normative design: `POLICY_SPEC.md`, schema version 1 proposal

This document compares the current implementation with the canonical routing
language defined in `POLICY_SPEC.md`. It does not propose new routing backends
and does not change runtime behavior.

The central conclusion is that the repository currently has a working
Happ/Xray artifact generator, but it does not yet implement the canonical
Routing Policy language. Publishing the current action-bucket YAML as v1.0
would freeze an incompatible public contract and make the specification much
more expensive to adopt later.

## Priority definitions

- **P0** — must be fixed before v1.0 because it affects the public language,
  routing semantics, silent degradation, reproducibility or release claims.
- **P1** — should be fixed soon after v1.0; the v1 contract can remain stable
  without it if limitations are explicit.
- **P2** — future enhancement that is intentionally outside the initial stable
  implementation.

## Complexity scale

Estimates assume one contributor familiar with the repository and include
implementation, unit tests and integration tests, but not calendar delays for
review.

| Estimate | Typical effort |
| --- | --- |
| XS | Less than one day |
| S | One to two days |
| M | Three to five days |
| L | One to two weeks |
| XL | More than two weeks or requires staged delivery |

The estimates are relative, not commitments. Several gaps overlap; implementing
them in the recommended order should reduce total effort.

## Executive summary

| ID | Gap | Priority | Complexity |
| --- | --- | --- | --- |
| GAP-001 | Canonical top-level policy document is not implemented | P0 | M |
| GAP-002 | Rules are action buckets, not first-class ordered Rules | P0 | L |
| GAP-003 | Actions and egresses are hardcoded to direct/proxy/block | P0 | M |
| GAP-004 | Typed matcher AST is absent | P0 | XL |
| GAP-005 | `any`, `all` and `not` are absent | P0 | M |
| GAP-006 | Objects, Domain Sets, IP Sets and Categories are absent | P0 | L |
| GAP-007 | Xray/geosite syntax leaks into the canonical core | P0 | M |
| GAP-008 | Capability discovery and compatibility checks are absent | P0 | L |
| GAP-009 | Target configuration and egress bindings are untyped | P0 | M |
| GAP-010 | There is no explicit normalization/IR/compiler pipeline | P0 | L |
| GAP-011 | Generators perform lowering and configuration logic | P0 | M |
| GAP-012 | Schema validation and normalization are incomplete | P0 | L |
| GAP-013 | Compilation errors are not structured or atomic | P0 | M |
| GAP-014 | External data is not pinned reproducibly | P0 | M |
| GAP-015 | Release metadata does not prove policy provenance | P0 | M |
| GAP-016 | Existing experimental policy has no migration path | P0 | M |
| GAP-017 | Conformance and negative tests are incomplete | P0 | L |
| GAP-018 | Deterministic backend plans and serializers are not specified in code | P0 | S |
| GAP-019 | Source-location diagnostics are absent | P1 | M |
| GAP-020 | Static lint and shadowing analysis are absent | P1 | L |
| GAP-021 | Generic multi-version migration framework is absent | P1 | L |
| GAP-022 | Backend hard limits are not modeled | P1 | M |
| GAP-023 | Artifact manifest and validation are hardcoded | P1 | M |
| GAP-024 | External resource providers lack a common resolver interface | P1 | L |
| GAP-025 | Source/destination observation semantics are not represented | P1 | M |
| GAP-026 | Schema revision and deprecation lifecycle are not automated | P1 | M |
| GAP-027 | Generated rules do not retain source Rule IDs | P1 | M |
| GAP-028 | Authoring shorthands and canonical rewrite are absent | P1 | S |
| GAP-029 | Process matcher is not implemented | P2 | L |
| GAP-030 | Package-name matcher is not implemented | P2 | L |
| GAP-031 | Equivalence-preserving optimizer is absent | P2 | XL |
| GAP-032 | Generator registry requires central edits | P2 | S |
| GAP-033 | Advanced lint heuristics are absent | P2 | L |
| GAP-034 | Future action types are not implemented | P2 | XL |

## Current implementation strengths

The following parts are useful foundations and are not gaps:

- policy and target files are already separated;
- core dataclasses are immutable;
- duplicate entries inside one current action list are rejected;
- generator implementations do not import one another;
- targets are processed in deterministic filename order;
- duplicate output filenames are rejected;
- Happ link and JSON equivalence is tested;
- DNS defaults have a regression test;
- full builds verify the downloaded GeoIP checksum;
- release assets have `SHA256SUMS`;
- CI exercises both configuration generation and full geodata builds.

These strengths should be preserved while replacing the experimental language.

# P0 gaps — required before v1.0

## GAP-001 — Canonical top-level policy document is not implemented

**Difference**

The specification defines one `RoutingPolicy` document with:

```yaml
schema_version: 1
kind: RoutingPolicy
metadata: {}
egresses: {}
domain_sets: {}
ip_sets: {}
objects: {}
categories: {}
rules: []
fallback: internet
```

The implementation instead loads `policy/policy.yaml`, `direct.yaml`,
`proxy.yaml` and `block.yaml`. Its metadata fields are `version`, `name`,
`domain_strategy`, `action_order` and `fallback`.

**Why it exists**

The current format was created as the smallest refactor capable of preserving
the original Happ and Xray outputs. `POLICY_SPEC.md` was designed afterward and
has not yet been implemented.

**Impact**

The current files cannot be declared schema v1 without contradicting the
specification. External users would learn an obsolete format.

**Priority:** P0
**Complexity:** M

**Smallest clean implementation**

1. Replace the four action-bucket files with one canonical `policy.yaml`.
2. Add typed document dataclasses for top-level sections.
3. Require `schema_version: 1` and `kind: RoutingPolicy`.
4. Reject unknown top-level fields.
5. Keep the old loader only as a one-time migration input, not as a second
   runtime language.

**Acceptance checklist**

- [ ] One canonical policy file loads successfully.
- [ ] Missing `schema_version`, `kind`, `egresses`, `rules` or `fallback` fails.
- [ ] Unknown top-level fields fail.
- [ ] Existing generators no longer read the legacy action files.

## GAP-002 — Rules are action buckets, not first-class ordered Rules

**Difference**

The implementation stores `dict[Action, ActionRules]`. It has no Rule ID,
description, individual matcher, individual action, priority or enabled flag.
`action_order` orders three buckets rather than individual Rules.

The specification requires first-match execution over individual enabled Rules,
sorted by priority descending and declaration order ascending.

**Why it exists**

The initial implementation mirrored Happ's six arrays and Xray's simple routing
groups. That representation was sufficient for two generated files but is not a
general rule language.

**Impact**

- individual exceptions cannot be ordered correctly;
- rules cannot be traced in logs;
- priorities and disabled rules cannot be expressed;
- merging all domains by action can change first-match semantics;
- future backends would invent their own ordering rules.

**Priority:** P0
**Complexity:** L

**Smallest clean implementation**

Introduce only the schema-v1 Rule fields:

```python
Rule(id, description, priority, enabled, matcher, action, source_index)
```

Add one core function that returns enabled Rules sorted by
`(-priority, source_index)`. Generators and lowerers must consume that ordered
sequence. Do not add schedules, chaining or multi-action behavior.

**Acceptance checklist**

- [ ] Rule IDs are unique and stable.
- [ ] Default priority is zero.
- [ ] Equal priorities preserve declaration order.
- [ ] Disabled Rules are validated but never compiled.
- [ ] First match and fallback have direct unit tests.

## GAP-003 — Actions and egresses are hardcoded

**Difference**

`Action` is an enum containing `DIRECT`, `PROXY` and `BLOCK`. The core therefore
knows client-oriented routing roles. There is no Egress model or target binding.

The specification requires opaque logical names such as `internet`, `vpn`,
`block`, `wan2` and `office`, with backend-specific bindings outside policy.

**Why it exists**

The enum directly reflected the original Happ arrays and three Xray tags.

**Impact**

- adding a logical route requires changing core code;
- core implicitly knows what “proxy” and “block” mean;
- policy cannot remain neutral across network appliances and proxy clients;
- fallback and target tags are coupled to one enum.

**Priority:** P0
**Complexity:** M

**Smallest clean implementation**

1. Replace the enum with validated `EgressId` values.
2. Add `egresses: Mapping[EgressId, Egress]` to the document.
3. Define schema-v1 Action as only `Action(egress: EgressId)`.
4. Add explicit egress bindings to each existing target.
5. Preserve current behavior by binding `internet→direct`, `vpn→proxy` and
   `block→block/reject` as appropriate for Happ and Xray.

No new egress behavior or backend is required.

**Acceptance checklist**

- [ ] Core contains no direct/proxy/block enum.
- [ ] Undeclared or unbound used egresses fail compilation.
- [ ] Fallback references a declared logical egress.
- [ ] Existing Happ/Xray outputs preserve current effective behavior.

## GAP-004 — Typed matcher AST is absent

**Difference**

The current model stores only opaque domain and IP strings. It cannot distinguish
exact domain, suffix, keyword, regex, address, CIDR, Country, ASN, port, port
range, protocol, network, source address or destination address.

**Why it exists**

Existing values are passed directly to Xray/Happ syntax, so parsing was not
needed for the initial artifact generator.

**Impact**

- core cannot validate matcher meaning;
- capability requirements cannot be derived;
- generators must parse backend-specific strings;
- malformed domains, CIDRs, ports and regexes can reach releases;
- canonical semantic comparison is impossible.

**Priority:** P0
**Complexity:** XL

**Smallest clean implementation**

Implement the schema-v1 matcher types as immutable tagged dataclasses:

- exact domain, suffix, keyword and RE2 regex;
- destination/source IP and CIDR;
- Country and ASN references with dataset IDs;
- source/destination port and port range;
- protocol and network.

Process and package name remain recognized future schema nodes usable only in
disabled Rules; they do not require backend implementation before v1.0.

Parse every matcher into a common `Matcher` union. Existing backends may support
only a subset; unsupported enabled matchers are handled by GAP-008 rather than
silently approximated.

**Acceptance checklist**

- [ ] Every mandatory schema-v1 matcher has a unique runtime type.
- [ ] Domain/IDNA, IP, CIDR, port, Country, ASN and regex validation exist.
- [ ] `ip` and `cidr` shorthands, if accepted, normalize to explicit destination
  types.
- [ ] Opaque `geosite:` and `geoip:` strings are not matcher primitives.
- [ ] Unsupported target compilation fails before output.

## GAP-005 — Logical operators are absent

**Difference**

There is no representation or evaluation for `any`, `all` or `not`.

**Why it exists**

Action buckets are flat lists whose implicit behavior is similar to `any`.
Nested predicates were outside the original scope.

**Impact**

The implementation cannot express the canonical language or prove that a
backend preserves boolean grouping.

**Priority:** P0
**Complexity:** M

**Smallest clean implementation**

Add three matcher nodes:

```python
AnyMatcher(children)
AllMatcher(children)
NotMatcher(child)
```

Validate cardinality exactly as specified. Implement normalization only for
safe structural flattening. Mark logical capabilities as required and let
current backends fail if no equivalence-preserving lowering is defined.

**Acceptance checklist**

- [ ] Empty or single-child `any`/`all` is rejected.
- [ ] `not` accepts exactly one child.
- [ ] Nested semantics have truth-table tests.
- [ ] No generator flattens unsupported logical expressions silently.

## GAP-006 — Objects, Sets and Categories are absent

**Difference**

Rules reference backend strings directly. There are no logical Objects,
Domain Sets, IP Sets or Categories and no reference resolver.

**Why it exists**

Current geosite categories already look reusable, so the first implementation
used them as if they were canonical identities.

**Impact**

- routing intent is coupled to provider naming;
- service identity and provider data cannot evolve independently;
- object/category membership cannot be reviewed or validated;
- missing and cyclic references cannot be detected;
- domain/IP provenance cannot be attached to logical resources.

**Priority:** P0
**Complexity:** L

**Smallest clean implementation**

1. Add the four schema sections and immutable resource types.
2. Allow Objects to reference Domain Sets and IP Sets only.
3. Allow Categories to reference Objects only.
4. Add `object` and `category` matcher leaves.
5. Resolve references into an acyclic normalized matcher graph.
6. Model current `private`, `routing-*` and advertising resources as named Sets
   and Objects without adding new routing content.

**Acceptance checklist**

- [ ] Missing references fail.
- [ ] Cycles fail.
- [ ] Referenced empty Objects fail for enabled Rules.
- [ ] Category expansion is deterministic.
- [ ] Objects contain no routing action.

## GAP-007 — Backend syntax leaks into the core

**Difference**

Policy values include `geosite:...` and `geoip:...`. The core also contains
`domain_strategy: IPIfNonMatch`, which is Xray terminology.

**Why it exists**

The refactor retained existing Xray/Happ values to keep artifact output stable.

**Impact**

- the source of truth remains indirectly Xray-specific;
- a future target must understand Xray strings or duplicate parsing;
- resource type, provider and key cannot be validated independently;
- `domain_strategy` has no portable meaning.

**Priority:** P0
**Complexity:** M

**Smallest clean implementation**

Move provider information into typed Domain/IP Set sources. Move
`IPIfNonMatch` into Xray target settings unless a separately reviewed neutral
resolution policy is introduced. Map neutral resources back to the current
geosite/geoip strings only inside existing backend lowering.

**Acceptance checklist**

- [ ] Canonical policy contains no `geosite:`/`geoip:` encoded strings.
- [ ] Canonical core contains no `IPIfNonMatch` enum or field.
- [ ] Current generated files still receive the required native syntax.

## GAP-008 — Capability model is absent

**Difference**

Generators are called unconditionally. There is no required-capability set,
target descriptor, support mode or pre-compilation compatibility check.

**Why it exists**

Both current outputs happen to support the minimal action buckets, so capability
differences have not yet surfaced.

**Impact**

As soon as typed matchers are added, generators could silently omit or weaken
unsupported semantics. That violates the primary safety rule of the spec.

**Priority:** P0
**Complexity:** L

**Smallest clean implementation**

1. Define versioned capability IDs and support modes `native`,
   `lowered-equivalent`, `unsupported`.
2. Derive required capabilities from enabled normalized Rules.
3. Give Happ and Xray explicit descriptors for only their tested subset.
4. Compare sets before backend lowering.
5. Raise one structured error per unsupported requirement.

Do not attempt to make current backends support every matcher before v1.0. The
smallest safe implementation is an honest capability failure.

**Acceptance checklist**

- [ ] Enabled unsupported matcher fails before artifacts are written.
- [ ] Disabled unsupported matcher does not block compilation.
- [ ] No warning-only degradation path exists.
- [ ] Capability descriptors are versioned and test-covered.

## GAP-009 — Targets and egress bindings are untyped

**Difference**

`load_target()` validates only that `generator` is a string. Generators receive
`Mapping[str, Any]` and access nested keys directly. There is no explicit
egress-binding schema.

**Why it exists**

The two small target files were easier to consume as dictionaries.

**Impact**

- typos fail as `KeyError` inside generation;
- target compatibility cannot be checked before generation;
- `global_proxy` can conflict conceptually with policy fallback;
- logical egresses cannot map cleanly to native outbound tags.

**Priority:** P0
**Complexity:** M

**Smallest clean implementation**

Create typed `HappTarget` and `XrayTarget` settings plus a shared target header:

```python
TargetConfig(backend, adapter_version, egress_bindings)
```

Keep DNS and release URLs as target-specific settings. Remove routing-semantic
target flags that duplicate policy fallback, or derive them from the compiled
backend plan.

**Acceptance checklist**

- [ ] Unknown and missing target fields fail before lowering.
- [ ] Every used logical egress has one validated binding.
- [ ] Target settings cannot override policy ordering or fallback silently.

## GAP-010 — No explicit compiler pipeline or normalized IR

**Difference**

`generate_all()` loads policy and immediately invokes generators. There are no
separate schema, normalization, resolution, capability and lowering stages.

**Why it exists**

The current model is already shaped like generator input, making a compiler
pipeline appear unnecessary.

**Impact**

- validation responsibility is scattered;
- backend equivalence cannot be audited;
- normalized policy cannot be hashed or compared;
- future changes risk placing more business logic in generators.

**Priority:** P0
**Complexity:** L

**Smallest clean implementation**

Create an explicit orchestration pipeline:

```text
parse -> validate -> normalize -> resolve -> derive capabilities
      -> validate target -> lower to typed backend plan -> serialize
```

Use one immutable normalized IR containing ordered Rules and resolved resource
references. Avoid an optimizer in v1.0; simple deterministic expansion is
sufficient.

**Acceptance checklist**

- [ ] Each stage has a narrow input/output type.
- [ ] Normalized IR is backend-neutral and serializable for hashing.
- [ ] Lowering starts only after all core and capability checks pass.

## GAP-011 — Generators are not pure serializers

**Difference**

Happ generator maps action buckets, constructs DNS hosts, URLs and base64 link.
Xray generator creates field rules, splits domain/IP entries and constructs a
catch-all fallback. Both consume canonical policy plus untyped target settings.

**Why it exists**

The current `Generator` protocol combines backend lowering and serialization in
one method.

**Impact**

Business and mapping decisions can drift between generators. Serializer tests
cannot distinguish semantic lowering bugs from formatting bugs.

**Priority:** P0
**Complexity:** M

**Smallest clean implementation**

For each current backend, introduce:

- a typed backend plan;
- a lowerer from normalized IR plus typed target config to that plan;
- a serializer from the plan to `GeneratedFile` values.

DNS URL formatting and Happ link encoding may remain in the serializer when
they only represent target format. Fallback selection, rule expansion and
egress mapping belong in lowering.

**Acceptance checklist**

- [ ] Serializer input contains no canonical `RoutingPolicy`.
- [ ] Serializer performs no matcher capability decisions.
- [ ] Lowerer and serializer have separate tests.

## GAP-012 — Strict schema validation and normalization are incomplete

**Difference**

Current validation checks mapping shape, version equals one, nonempty policy
name, complete action enum and duplicates within a list. It does not reject
unknown fields or validate identifiers, typed values, references, IDNA, CIDR,
ports, regex dialects, Country codes or ASN ranges.

`str()` and `int()` coercions can accept values whose YAML types were wrong.

**Why it exists**

The experimental schema has very few typed concepts.

**Impact**

Invalid policy can be accepted, normalized differently by clients or fail late
inside a generator.

**Priority:** P0
**Complexity:** L

**Smallest clean implementation**

Use a strict schema layer followed by semantic validators. Avoid permissive
coercion. Implement the normative identifier and matcher validation rules from
the spec. Unknown fields must fail. Keep lint warnings separate from errors.

**Acceptance checklist**

- [ ] Wrong YAML scalar types fail instead of being coerced.
- [ ] Unknown fields fail at every schema level.
- [ ] Normalization is deterministic and unit-tested.
- [ ] Duplicate normalized values are errors or documented lint findings.

## GAP-013 — Errors are not structured and output is not atomic

**Difference**

The implementation uses string `PolicyError`, `SystemExit`, raw `KeyError` and
shell failures. `generate_all()` creates the output directory and writes each
artifact immediately, so a later failure can leave partial or stale output.

**Why it exists**

The CLI was optimized for a small happy-path build.

**Impact**

- CI errors are difficult to classify;
- tools cannot report Rule ID/capability consistently;
- a failed compilation can leave apparently usable artifacts;
- release scripts may package stale files.

**Priority:** P0
**Complexity:** M

**Smallest clean implementation**

1. Define error codes for schema, reference, capability, target and artifact
   failures.
2. Include entity ID and field path; exact YAML line can remain P1.
3. Compile all plans and serialize into an in-memory artifact collection or
   temporary output directory.
4. Replace the final output directory only after every target succeeds.

**Acceptance checklist**

- [ ] Failed generation leaves no partial new release.
- [ ] Errors have stable code, entity ID and field path.
- [ ] Unknown backend and duplicate artifact use the same error framework.

## GAP-014 — External data is not pinned reproducibly

**Difference**

`build.sh` fetches the current `master` of domain-list-community and downloads
the latest Loyalsoldier GeoIP release at build time. The source revisions are
not declared by canonical policy before compilation.

**Why it exists**

The project is designed to publish frequently updated geodata and currently
records some provenance after downloading it.

**Impact**

Two builds of the same source commit can produce different artifacts. A release
cannot be recreated solely from repository state.

**Priority:** P0
**Complexity:** M

**Smallest clean implementation**

Introduce a generated resource lock file containing exact upstream revision,
asset URL and SHA-256. The update workflow may refresh the lock intentionally,
but compilation consumes only locked values. Represent geosite/GeoIP resources
as typed Set sources linked to that lock.

**Acceptance checklist**

- [ ] Same source commit plus lock produces the same input resources.
- [ ] Resource update is a visible diff or recorded release input.
- [ ] Download digest is checked before compilation.
- [ ] Unpinned external resource fails release mode.

## GAP-015 — Release metadata does not prove canonical policy provenance

**Difference**

`release.json` records generation time, geosite commit, GeoIP channel and four
file digests. It does not record:

- source commit SHA;
- policy schema version and metadata revision;
- canonical policy digest;
- normalized IR digest;
- resource lock digest;
- compiler version;
- adapter versions;
- capability descriptor digests;
- Happ link metadata.

**Why it exists**

Release metadata predates the canonical language and capability design.

**Impact**

Users cannot prove which policy and compiler semantics produced an artifact.
This weakens the release verification promise.

**Priority:** P0
**Complexity:** M

**Smallest clean implementation**

Extend release metadata only with the fields mandated by the spec and generate
it from the completed artifact collection. Include every published artifact.
Pass source commit SHA from GitHub Actions or Git and verify it equals the
release tag target.

**Acceptance checklist**

- [ ] Metadata contains all required provenance fields.
- [ ] Every published artifact has size and SHA-256.
- [ ] Metadata provenance is covered by release verification tests.

## GAP-016 — Existing experimental policy has no migration path

**Difference**

There is no deterministic transform from current `policy/*.yaml` action buckets
to the canonical schema-v1 document.

**Why it exists**

The current format and the specification were developed sequentially.

**Impact**

Replacing the loader manually risks changing current Happ/Xray behavior. Keeping
both formats indefinitely would create two sources of truth.

**Priority:** P0
**Complexity:** M

**Smallest clean implementation**

Write a one-time `legacy-action-buckets -> schema-v1` migration with a fixed
mapping:

- `direct -> internet`;
- `proxy -> vpn`;
- `block -> block`;
- preserve bucket order as generated ordered Rules;
- preserve fallback;
- convert current geosite/geoip references into typed locked resources;
- emit a semantic comparison report for Happ and Xray artifacts.

Delete the legacy runtime loader after migration. It may remain only in a
migration test fixture.

**Acceptance checklist**

- [ ] Migrated policy produces semantically equivalent current artifacts.
- [ ] Old and new formats cannot both be active.
- [ ] Migration report lists every generated Rule and mapping.

## GAP-017 — Conformance and negative tests are incomplete

**Difference**

Six tests currently cover generation, Happ link equivalence, DNS, action order
and one duplicate-list error. There are no canonical schema, matcher,
normalization, reference, capability, lowering, migration or negative-output
tests.

**Why it exists**

Tests match the small experimental model.

**Impact**

The new public contract could regress without detection. Silent semantic loss
would not be caught.

**Priority:** P0
**Complexity:** L

**Smallest clean implementation**

Before v1.0 add:

- schema acceptance/rejection fixtures;
- one positive and multiple boundary tests per matcher;
- logical operator truth-table tests;
- ordering/priority/disabled/fallback tests;
- Object/Set/Category resolution and cycle tests;
- capability success and failure tests;
- migration equivalence tests;
- Happ and Xray lowerer contract tests;
- serializer golden files;
- atomic failure test proving no partial artifacts.

No new backend test is required.

**Acceptance checklist**

- [ ] Every P0 semantic has a regression test.
- [ ] Unsupported capability is a hard-error test.
- [ ] Existing Happ and Xray output behavior remains covered.

## GAP-018 — Deterministic backend plans and serialization are not enforced

**Difference**

Some ordering is stable by Python insertion order, but no plan type or test
defines canonical ordering of generated rules and object keys. Output
determinism is accidental rather than contractual.

**Why it exists**

Current generated documents are small and created in fixed code order.

**Impact**

Refactors can cause meaningless artifact churn, break reproducibility and make
digest comparisons unreliable.

**Priority:** P0
**Complexity:** S

**Smallest clean implementation**

Define deterministic ordering in typed backend plans, use stable JSON settings
and add a test that compiles the same locked policy twice and compares bytes.
Exclude only explicitly nondeterministic release metadata such as generation
time from semantic artifact comparison.

**Acceptance checklist**

- [ ] Repeated compilation produces byte-identical backend artifacts.
- [ ] Rule order follows normalized first-match order.
- [ ] Key and list ordering is documented and tested.

# P1 gaps — soon after v1.0

## GAP-019 — Source-location diagnostics are absent

**Difference**

Errors identify messages and sometimes filenames, but not exact YAML line,
column or source span as required for high-quality conformance diagnostics.

**Why it exists**

`yaml.safe_load()` discards source marks when converting directly to ordinary
Python dictionaries.

**Priority:** P1
**Complexity:** M

**Recommended implementation**

Use a marked YAML representation or maintain a path-to-source-span table during
parsing. Carry source references into normalized Rules and errors.

## GAP-020 — Static lint and shadowing analysis are absent

**Difference**

There are no warnings for unused resources, shadowed Rules, unreachable Rules,
broad keywords, suspicious regexes or excessive priorities.

**Why it exists**

Current action buckets do not provide enough structure for meaningful analysis.

**Priority:** P1
**Complexity:** L

**Recommended implementation**

Add a separate non-mutating linter after canonical normalization. Keep warnings
distinct from compilation errors and assign stable diagnostic codes.

## GAP-021 — Generic multi-version migration framework is absent

**Difference**

GAP-016 supplies a one-time migration, but the specification requires
deterministic sequential migrations for future schema versions.

**Why it exists**

Only schema version 1 currently exists.

**Priority:** P1
**Complexity:** L

**Recommended implementation**

Add a migration registry keyed by `(from_version, to_version)`, immutable input,
patch/report output, idempotency tests and explicit human-decision failures.

## GAP-022 — Backend hard limits are not modeled

**Difference**

Targets do not declare maximum rules, nesting, regex length, named egress count,
IPv6 support or external Set constraints.

**Why it exists**

Current generated policy is small and has not reached backend limits.

**Priority:** P1
**Complexity:** M

**Recommended implementation**

Extend capability descriptors with tested hard limits and validate the lowered
plan before serialization.

## GAP-023 — Artifact manifest and validation are hardcoded

**Difference**

`build.sh`, `release_metadata.py` and `validate.py` contain fixed Happ/Xray
filenames. Artifact production is not driven by one manifest.

**Why it exists**

Only three generated client files currently exist.

**Priority:** P1
**Complexity:** M

**Recommended implementation**

Make the compiler return an `ArtifactManifest` containing name, media type,
producer, digest and validation contract. Generate checksums, release metadata
and publish lists from it.

This does not add a backend; it removes duplicated orchestration.

## GAP-024 — External resource providers lack a common resolver interface

**Difference**

Geosite compilation and GeoIP download are shell-specific paths. There is no
provider-neutral resolver contract for typed Set sources.

**Why it exists**

The build currently uses only two known upstream projects.

**Priority:** P1
**Complexity:** L

**Recommended implementation**

After resource locking is stable, define a resolver interface that returns
typed entries plus provenance. Wrap current sources without adding new ones.

## GAP-025 — Source/destination observation semantics are not represented

**Difference**

The spec distinguishes original, resolved and post-redirect destination
addresses and notes that NAT affects observable source addresses. Target
capabilities currently express none of this.

**Why it exists**

The current policy has no source/destination typed matchers.

**Priority:** P1
**Complexity:** M

**Recommended implementation**

Add observation-stage metadata to relevant matcher capabilities. Until a target
declares an exact stage, reject enabled policies whose semantics depend on it.

## GAP-026 — Schema revision and deprecation lifecycle are not automated

**Difference**

There is no schema revision identifier, compatibility range, deprecation
diagnostic or enforcement of the documented release-cycle policy.

**Why it exists**

The language is not yet implemented as a public versioned contract.

**Priority:** P1
**Complexity:** M

**Recommended implementation**

Publish machine-readable schemas by major/revision, let adapters declare their
supported range and add stable deprecation codes with replacement hints.

## GAP-027 — Generated rules do not retain source Rule IDs

**Difference**

Generated Xray rules and Happ arrays contain no trace from an output entry back
to its canonical Rule ID. The current model has no IDs to preserve.

**Why it exists**

Action buckets lose rule identity before generation.

**Priority:** P1
**Complexity:** M

**Recommended implementation**

Carry origin IDs through normalized IR and backend plans. Where the output
format cannot store IDs, emit a sidecar mapping in release metadata or debug
artifacts.

## GAP-028 — Authoring shorthands and canonical rewrite are absent

**Difference**

The specification allows tools to accept conveniences such as `ip`, `cidr` and
`AS15169` if they normalize to canonical forms. No canonical formatter exists.

**Why it exists**

Typed matchers are not implemented.

**Priority:** P1
**Complexity:** S

**Recommended implementation**

Add a formatter that emits only canonical schema-v1 syntax and a `--check` mode
for CI. Keep parser acceptance narrower until the canonical form is stable.

# P2 gaps — future enhancements

## GAP-029 — Process matcher is not implemented

**Difference**

There is no process matcher, platform identity model or capability.

**Why it exists**

The specification explicitly marks process matching as future and excludes it
from the mandatory v1 capability baseline.

**Priority:** P2
**Complexity:** L

**Future direction**

Finalize basename/path/signing semantics before enabling it in active Rules.
The v1 parser may preserve it only in disabled Rules.

## GAP-030 — Package-name matcher is not implemented

**Difference**

There is no mobile package identity matcher or platform model.

**Why it exists**

It is intentionally future-facing in the specification.

**Priority:** P2
**Complexity:** L

**Future direction**

Define platform-qualified package IDs and observation semantics before enabling
the capability.

## GAP-031 — Equivalence-preserving optimizer is absent

**Difference**

There is no optimizer for rule factoring, set reuse, boolean rewrites or target
limit reduction.

**Why it exists**

The current policy is tiny, and an optimizer is unnecessary for the smallest
clean v1 compiler.

**Priority:** P2
**Complexity:** XL

**Future direction**

Add transformations only with equivalence proofs or exhaustive semantic tests.
Never use optimization to hide an unsupported capability.

## GAP-032 — Generator registry requires central edits

**Difference**

Adding an adapter requires importing it and editing the `GENERATORS` dictionary.

**Why it exists**

A static registry is simple and appropriate for two in-tree backends.

**Priority:** P2
**Complexity:** S

**Future direction**

Consider Python entry points or declarative registration only if external
adapters become a real requirement. Do not introduce plugin complexity for
v1.0.

## GAP-033 — Advanced lint heuristics are absent

**Difference**

Beyond basic P1 lint, there is no SAT-like overlap analysis, regex risk scoring,
policy coverage report or route simulation.

**Why it exists**

These are operational quality tools rather than language correctness
requirements.

**Priority:** P2
**Complexity:** L

**Future direction**

Build them on stable normalized IR after v1.0.

## GAP-034 — Future action types are not implemented

**Difference**

The implementation has fixed action buckets, and the specification intentionally
defines only egress selection for schema v1. There is no support for mark,
continue, DNS action, accounting or multi-action Rules.

**Why it exists**

These actions are explicit non-goals for the initial language.

**Priority:** P2
**Complexity:** XL

**Future direction**

Introduce a new versioned capability or schema major version only after the
execution semantics are specified. Do not add backend escape hatches.

# Differences that are not implementation gaps

The following specification topics intentionally require no v1.0 code change:

- adding sing-box, Clash/Mihomo or Keenetic backends;
- load balancing and health checks;
- time schedules;
- traffic accounting and quotas;
- user authentication;
- runtime policy mutation;
- DNS routing actions;
- external plugin discovery;
- optimization beyond deterministic normalization.

Target-specific Happ DNS URLs are also not a canonical-policy violation. They
belong in target configuration as long as they do not override routing Rule
semantics.

# Smallest clean v1.0 implementation plan

This sequence minimizes temporary compatibility layers and avoids rewriting the
same boundary twice.

## Phase 1 — Freeze schema and domain model

Addresses: GAP-001 through GAP-007 and GAP-012.

- [ ] Add strict schema-v1 parser.
- [ ] Add Egress, Rule, Action and matcher AST types.
- [ ] Add Domain/IP Sets, Objects and Categories.
- [ ] Add logical operators.
- [ ] Add deterministic normalization and reference resolution.
- [ ] Remove backend strings from canonical policy.

Exit criterion: canonical fixtures normalize into immutable backend-neutral IR.

## Phase 2 — Establish compiler boundaries

Addresses: GAP-008 through GAP-013 and GAP-018.

- [ ] Add required-capability derivation.
- [ ] Add explicit Happ and Xray capability descriptors.
- [ ] Add typed target configs and egress bindings.
- [ ] Split lowerers from serializers.
- [ ] Add structured errors and atomic artifact production.
- [ ] Prove deterministic compilation.

Exit criterion: unsupported semantics fail before any artifact is emitted.

## Phase 3 — Reproducibility and release provenance

Addresses: GAP-014 and GAP-015.

- [ ] Introduce a resource lock.
- [ ] Build only from pinned resource revisions in release mode.
- [ ] Record policy, IR, source, compiler, adapter and capability digests.
- [ ] Include every published artifact in metadata and checksums.

Exit criterion: a release can be traced to and recreated from recorded inputs.

## Phase 4 — Migration and conformance

Addresses: GAP-016 and GAP-017.

- [ ] Migrate the current action-bucket policy once.
- [ ] Compare old and new Happ/Xray effective outputs.
- [ ] Remove the legacy runtime loader.
- [ ] Add positive, negative, capability, migration and golden tests.
- [ ] Run the full procedure in `TESTING.md`.

Exit criterion: only canonical schema v1 is accepted in production, current
backend behavior is preserved, and every P0 semantic is test-covered.

# v1.0 release gate

The first stable release must not be tagged until all items below are true:

- [ ] Every P0 gap is closed or the specification is explicitly revised before
  implementation and reviewed again.
- [ ] Canonical schema v1 is the only active policy language.
- [ ] Existing policy has been migrated with semantic comparison evidence.
- [ ] Happ and Xray use logical egress bindings.
- [ ] Generators serialize typed backend plans rather than canonical policy.
- [ ] Unsupported enabled capabilities fail compilation.
- [ ] Builds are atomic and deterministic.
- [ ] External resources are pinned and verified.
- [ ] Release metadata contains complete policy and compiler provenance.
- [ ] All conformance, migration, backend and release tests pass.
- [ ] The functional release checklist in `TESTING.md` passes.
- [ ] No new backend or unrelated feature is included in the stabilization diff.

## Final assessment

The current implementation should be treated as a functioning prototype of the
artifact pipeline, not as the stable implementation of `POLICY_SPEC.md`.

The safest path to v1.0 is not to expand backend behavior. It is to replace the
experimental action-bucket contract with the smallest complete canonical core,
make unsupported features fail explicitly, preserve existing Happ/Xray output
through typed lowering, and lock release provenance.
