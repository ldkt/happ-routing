"""Deterministic canonical policy normalization and reference resolution."""

from __future__ import annotations

from types import MappingProxyType

from .model import (
    AllMatcher,
    AnyMatcher,
    CategoryRef,
    DomainSetRef,
    IPSetRef,
    Matcher,
    NormalizedPolicy,
    NotMatcher,
    ObjectRef,
    PolicyError,
    ResolvedAll,
    ResolvedAny,
    ResolvedDomainSet,
    ResolvedIPSet,
    ResolvedMatcher,
    ResolvedNot,
    ResolvedRule,
    RoutingPolicy,
)


def normalize_policy(policy: RoutingPolicy) -> NormalizedPolicy:
    """Validate cross-references and return deterministic backend-neutral IR."""

    if policy.fallback not in policy.egresses:
        raise PolicyError(f"fallback references undeclared egress: {policy.fallback}")

    for object_ in policy.objects.values():
        for set_id in object_.domain_sets:
            if set_id not in policy.domain_sets:
                raise PolicyError(
                    f"object {object_.id} references missing Domain Set: {set_id}"
                )
        for set_id in object_.ip_sets:
            if set_id not in policy.ip_sets:
                raise PolicyError(f"object {object_.id} references missing IP Set: {set_id}")

    for category in policy.categories.values():
        for object_id in category.objects:
            if object_id not in policy.objects:
                raise PolicyError(
                    f"category {category.id} references missing Object: {object_id}"
                )

    rules: list[ResolvedRule] = []
    for rule in policy.rules:
        if rule.action.egress not in policy.egresses:
            raise PolicyError(
                f"rule {rule.id} references undeclared egress: {rule.action.egress}"
            )
        rules.append(
            ResolvedRule(
                id=rule.id,
                matcher=_resolve_matcher(policy, rule.matcher),
                action=rule.action,
                description=rule.description,
                priority=rule.priority,
                enabled=rule.enabled,
                source_index=rule.source_index,
            )
        )

    rules.sort(key=lambda item: (-item.priority, item.source_index))
    return NormalizedPolicy(
        schema_version=policy.schema_version,
        metadata=policy.metadata,
        egresses=MappingProxyType(dict(policy.egresses)),
        rules=tuple(rules),
        fallback=policy.fallback,
    )


def _resolve_matcher(policy: RoutingPolicy, matcher: Matcher) -> ResolvedMatcher:
    if isinstance(matcher, DomainSetRef):
        try:
            return ResolvedDomainSet(policy.domain_sets[matcher.set_id])
        except KeyError as error:
            raise PolicyError(f"missing Domain Set: {matcher.set_id}") from error
    if isinstance(matcher, IPSetRef):
        try:
            return ResolvedIPSet(policy.ip_sets[matcher.set_id])
        except KeyError as error:
            raise PolicyError(f"missing IP Set: {matcher.set_id}") from error
    if isinstance(matcher, ObjectRef):
        try:
            object_ = policy.objects[matcher.object_id]
        except KeyError as error:
            raise PolicyError(f"missing Object: {matcher.object_id}") from error
        children: list[ResolvedMatcher] = [
            ResolvedDomainSet(policy.domain_sets[set_id]) for set_id in object_.domain_sets
        ]
        children.extend(ResolvedIPSet(policy.ip_sets[set_id]) for set_id in object_.ip_sets)
        return _combine_any(children, f"Object {object_.id}")
    if isinstance(matcher, CategoryRef):
        try:
            category = policy.categories[matcher.category_id]
        except KeyError as error:
            raise PolicyError(f"missing Category: {matcher.category_id}") from error
        children = [
            _resolve_matcher(policy, ObjectRef(object_id)) for object_id in category.objects
        ]
        return _combine_any(children, f"Category {category.id}")
    if isinstance(matcher, AnyMatcher):
        children: list[ResolvedMatcher] = []
        for child in matcher.children:
            resolved = _resolve_matcher(policy, child)
            if isinstance(resolved, ResolvedAny):
                children.extend(resolved.children)
            else:
                children.append(resolved)
        return _combine_any(children, "any")
    if isinstance(matcher, AllMatcher):
        children: list[ResolvedMatcher] = []
        for child in matcher.children:
            resolved = _resolve_matcher(policy, child)
            if isinstance(resolved, ResolvedAll):
                children.extend(resolved.children)
            else:
                children.append(resolved)
        if len(children) < 2:
            raise PolicyError("normalized all must contain at least two matchers")
        return ResolvedAll(tuple(children))
    if isinstance(matcher, NotMatcher):
        return ResolvedNot(_resolve_matcher(policy, matcher.child))
    return matcher


def _combine_any(children: list[ResolvedMatcher], owner: str) -> ResolvedMatcher:
    if not children:
        raise PolicyError(f"{owner} resolves to no matchers")
    if len(children) == 1:
        return children[0]
    flattened: list[ResolvedMatcher] = []
    for child in children:
        if isinstance(child, ResolvedAny):
            flattened.extend(child.children)
        else:
            flattened.append(child)
    return ResolvedAny(tuple(flattened))
