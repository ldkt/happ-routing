"""Compile domain-list-community source files into canonical domain IR.

Only this core module reads source files. Backends receive the resulting
immutable IR and have no access to ``data/`` or the source snapshot.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable

from .domain_ir import CanonicalDomain, CanonicalDomainIR, CanonicalDomainSet, DomainKind


_NAME = re.compile(r"^[a-z0-9!-]+$")
_DOMAIN = re.compile(r"^[a-z0-9.-]+$")


@dataclass(frozen=True)
class _Include:
    source: str
    required: tuple[str, ...]
    banned: tuple[str, ...]


@dataclass(frozen=True)
class _SourceList:
    entries: tuple[CanonicalDomain, ...]
    includes: tuple[_Include, ...]


class DomainSourceError(ValueError):
    """Raised when a domain source snapshot cannot form canonical IR."""


def compile_domain_ir(source_dir: Path, set_ids: Iterable[str]) -> CanonicalDomainIR:
    """Resolve named lists from one prepared source snapshot."""

    requested = tuple(dict.fromkeys(_list_name(item) for item in set_ids))
    parsed: dict[str, _SourceList] = {}
    resolved: dict[str, tuple[CanonicalDomain, ...]] = {}
    resolving: list[str] = []

    def load(name: str) -> _SourceList:
        if name in parsed:
            return parsed[name]
        path = source_dir / name
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as error:
            raise DomainSourceError(f"cannot read domain list {name!r}: {error}") from error
        entries: list[CanonicalDomain] = []
        includes: list[_Include] = []
        for line_number, original in enumerate(lines, 1):
            line = original.split("#", 1)[0].strip()
            if not line:
                continue
            try:
                if line.lower().startswith("include:"):
                    includes.append(_parse_include(line.removeprefix("include:")))
                else:
                    entries.append(_parse_domain(line))
            except DomainSourceError as error:
                raise DomainSourceError(f"{path}:{line_number}: {error}") from error
        value = _SourceList(tuple(entries), tuple(includes))
        parsed[name] = value
        return value

    def resolve(name: str) -> tuple[CanonicalDomain, ...]:
        if name in resolved:
            return resolved[name]
        if name in resolving:
            cycle = " -> ".join((*resolving, name))
            raise DomainSourceError(f"circular domain-list include: {cycle}")
        resolving.append(name)
        source = load(name)
        values = {entry for entry in source.entries}
        for include in source.includes:
            for entry in resolve(include.source):
                if _matches(entry, include):
                    values.add(entry)
        resolving.pop()
        result = _polish(values)
        resolved[name] = result
        return result

    sets = {
        name: CanonicalDomainSet(name, resolve(name))
        for name in requested
    }
    return CanonicalDomainIR.create(sets)


def _list_name(value: str) -> str:
    name = value.strip().lower()
    if not _NAME.fullmatch(name):
        raise DomainSourceError(f"invalid domain-list name: {value!r}")
    return name


def _parse_include(value: str) -> _Include:
    parts = value.split()
    if not parts:
        raise DomainSourceError("empty include")
    source = _list_name(parts[0])
    required: list[str] = []
    banned: list[str] = []
    for part in parts[1:]:
        if not part.startswith("@") or len(part) == 1:
            raise DomainSourceError(f"invalid include filter: {part!r}")
        attribute = part[1:].lower()
        if attribute.startswith("-"):
            banned.append(attribute[1:])
        else:
            required.append(attribute)
    return _Include(source, tuple(sorted(required)), tuple(sorted(banned)))


def _parse_domain(value: str) -> CanonicalDomain:
    parts = value.split()
    rule = parts[0]
    attributes: list[str] = []
    for part in parts[1:]:
        if part.startswith("@") and len(part) > 1:
            attributes.append(part[1:].lower())
        elif part.startswith("&") and len(part) > 1:
            continue
        else:
            raise DomainSourceError(f"invalid domain field: {part!r}")
    prefix, separator, raw = rule.partition(":")
    if separator and prefix.lower() in {item.value for item in DomainKind}:
        kind = DomainKind(prefix.lower())
        domain = raw
    elif separator:
        raise DomainSourceError(f"unsupported domain rule type: {prefix!r}")
    else:
        kind = DomainKind.DOMAIN
        domain = rule
    normalized = domain if kind is DomainKind.REGEXP else domain.lower()
    if not normalized:
        raise DomainSourceError("empty domain rule")
    if kind in {DomainKind.DOMAIN, DomainKind.FULL, DomainKind.KEYWORD}:
        if not _DOMAIN.fullmatch(normalized):
            raise DomainSourceError(f"invalid domain value: {normalized!r}")
    else:
        try:
            re.compile(normalized)
        except re.error as error:
            raise DomainSourceError(f"invalid regular expression: {error}") from error
    return CanonicalDomain(kind, normalized, tuple(sorted(set(attributes))))


def _matches(entry: CanonicalDomain, include: _Include) -> bool:
    attributes = set(entry.attributes)
    if not attributes and include.required:
        return False
    return all(item in attributes for item in include.required) and all(
        item not in attributes for item in include.banned
    )


def _polish(values: set[CanonicalDomain]) -> tuple[CanonicalDomain, ...]:
    domains = {
        entry.value
        for entry in values
        if entry.kind is DomainKind.DOMAIN and not entry.attributes
    }
    result: list[CanonicalDomain] = []
    for entry in values:
        if entry.attributes or entry.kind in {DomainKind.KEYWORD, DomainKind.REGEXP}:
            result.append(entry)
            continue
        parent = entry.value if entry.kind is DomainKind.DOMAIN else f".{entry.value}"
        redundant = False
        while "." in parent:
            parent = parent.split(".", 1)[1]
            if parent in domains:
                redundant = True
                break
        if not redundant:
            result.append(entry)
    return tuple(sorted(result, key=lambda item: (item.kind.value, item.value, item.attributes)))
