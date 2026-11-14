"""Package converted Codex Skills as Codex plugins and describe them in a marketplace."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Protocol

PLUGIN_DIRECTORY = "codex-plugins"
MARKETPLACE_NAME = "poteto-skills"
PLUGIN_SOURCE_PREFIX = f"./skills/{PLUGIN_DIRECTORY}"
PLUGIN_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
FALLBACK_AUTHOR = "poteto-skills contributors"
CATEGORY_LABELS = {
    "developer-tools": "Developer Tools",
    "productivity": "Productivity",
    "integrations": "Integrations",
    "utilities": "Utilities",
}
DEFAULT_CATEGORY = "developer-tools"
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
SHORT_DESCRIPTION_LIMIT = 100


class PluginSkill(Protocol):
    name: str
    plugin_name: str
    plugin_root: Path
    plugin_version: str
    license_file: Path


@dataclass(frozen=True)
class PluginPlan:
    name: str
    upstream: dict[str, object]
    skills: tuple[str, ...]
    license_file: Path


def plan_plugins(skills: Iterable[PluginSkill], experimental: set[str]) -> list[PluginPlan]:
    grouped: dict[str, list[PluginSkill]] = {}
    for skill in skills:
        if skill.name not in experimental:
            grouped.setdefault(skill.plugin_name, []).append(skill)
    plans: list[PluginPlan] = []
    for name in sorted(grouped):
        members = sorted(grouped[name], key=lambda item: item.name)
        manifest = members[0].plugin_root / ".cursor-plugin" / "plugin.json"
        plans.append(
            PluginPlan(
                name=name,
                upstream=json.loads(manifest.read_text(encoding="utf-8")),
                skills=tuple(item.name for item in members),
                license_file=members[0].license_file,
            )
        )
    return plans


def tree_digest(roots: Iterable[Path], base: Path) -> str:
    digest = hashlib.sha256()
    for root in roots:
        files = [root] if root.is_file() else sorted(p for p in root.rglob("*") if p.is_file())
        for path in files:
            digest.update(path.relative_to(base).as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def plugin_version(upstream: dict[str, object], digest: str) -> str:
    raw = upstream.get("version")
    base = raw if isinstance(raw, str) and SEMVER.fullmatch(raw) else "0.0.0"
    return f"{base}+poteto.{digest[:7]}"


def category_label(upstream: dict[str, object]) -> str:
    slug = upstream.get("category")
    if not isinstance(slug, str) or not slug:
        slug = DEFAULT_CATEGORY
    return CATEGORY_LABELS.get(slug, slug.replace("-", " ").title())


def short_description(text: str) -> str:
    first = re.split(r"(?<=[.!?])\s", text.strip(), maxsplit=1)[0]
    if len(first) <= SHORT_DESCRIPTION_LIMIT:
        return first
    return first[: SHORT_DESCRIPTION_LIMIT - 3].rsplit(" ", 1)[0] + "..."


def keywords(upstream: dict[str, object]) -> list[str]:
    seen: list[str] = []
    for field in ("keywords", "tags"):
        values = upstream.get(field)
        if isinstance(values, list):
            seen.extend(v for v in values if isinstance(v, str) and v not in seen)
    return seen


def author_name(upstream: dict[str, object]) -> str:
    author = upstream.get("author")
    if isinstance(author, dict) and isinstance(author.get("name"), str):
        return author["name"]
    return FALLBACK_AUTHOR


def manifests(plan: PluginPlan, version: str, repository: str) -> tuple[dict, dict]:
    upstream = plan.upstream
    display = upstream.get("displayName")
    display_name = display if isinstance(display, str) and display else plan.name
    description = upstream.get("description")
    if not isinstance(description, str) or not description:
        description = f"{display_name} Skills converted from the Cursor plugin for Codex."
    homepage = upstream.get("homepage")
    homepage = homepage if isinstance(homepage, str) and homepage else repository
    identity = {
        "name": plan.name,
        "version": version,
        "description": description,
        "author": {"name": author_name(upstream)},
        "homepage": homepage,
        "repository": repository,
        "license": "MIT",
        "keywords": keywords(upstream),
    }
    portable = {"$schema": PLUGIN_SCHEMA, **identity}
    compat = {
        **identity,
        "skills": "./skills/",
        "interface": {
            "displayName": display_name,
            "shortDescription": short_description(description),
            "longDescription": description,
            "developerName": author_name(upstream),
            "category": category_label(upstream),
            "websiteURL": homepage,
        },
    }
    return portable, compat


def write_json(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_plugins(
    plans: list[PluginPlan], codex_root: Path, destination: Path, repository: str
) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for plan in plans:
        root = destination / plan.name
        for skill in plan.skills:
            shutil.copytree(codex_root / skill, root / "skills" / skill)
        shutil.copy2(plan.license_file, root / "LICENSE")
        digest = tree_digest([root / "skills", root / "LICENSE"], root)
        version = plugin_version(plan.upstream, digest)
        portable, compat = manifests(plan, version, repository)
        write_json(root / "plugin.json", portable)
        write_json(root / ".codex-plugin" / "plugin.json", compat)
        entries.append(
            {
                "name": plan.name,
                "version": version,
                "category": compat["interface"]["category"],
                "skills": list(plan.skills),
            }
        )
    return entries


def marketplace_document(entries: list[dict[str, object]]) -> dict[str, object]:
    return {
        "name": MARKETPLACE_NAME,
        "interface": {"displayName": MARKETPLACE_NAME},
        "plugins": [
            {
                "name": entry["name"],
                "source": {"source": "local", "path": f"{PLUGIN_SOURCE_PREFIX}/{entry['name']}"},
                "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                "category": entry["category"],
            }
            for entry in entries
        ],
    }


def write_marketplace(path: Path, entries: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    staging = path.with_name(f".{path.name}.tmp")
    write_json(staging, marketplace_document(entries))
    staging.replace(path)


def directory_files(root: Path) -> dict[str, bytes]:
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def verify_plugins(output: Path, entries: object) -> None:
    if not isinstance(entries, list):
        raise ValueError(f"{output}: manifest is missing the Codex plugin inventory")
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("name"), str):
            raise ValueError(f"{output}: invalid Codex plugin entry")
        name = entry["name"]
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", name):
            raise ValueError(f"{output}: unsafe Codex plugin name")
        root = output / PLUGIN_DIRECTORY / name
        variant = entry.get("variant", "default")
        if variant not in ("default", "hooks"):
            raise ValueError(f"{root}: unsupported plugin variant")
        manifests_to_check = [root / ".codex-plugin" / "plugin.json"]
        if variant == "default":
            manifests_to_check.insert(0, root / "plugin.json")
        if not all(path.is_file() for path in [*manifests_to_check, root / "LICENSE"]):
            raise ValueError(f"{output}: incomplete Codex plugin {name}")
        for manifest in manifests_to_check:
            document = json.loads(manifest.read_text(encoding="utf-8"))
            if document.get("name") != name or document.get("version") != entry.get("version"):
                raise ValueError(f"{manifest}: does not match the plugin inventory")
        shipped = sorted(p.name for p in (root / "skills").iterdir())
        if shipped != sorted(entry["skills"]):
            raise ValueError(f"{root}: skill set differs from the plugin inventory")
        if variant == "hooks":
            verify_hook_plugin(root, entry, output)
            continue
        for skill in shipped:
            if directory_files(root / "skills" / skill) != directory_files(
                output / "codex" / skill
            ):
                raise ValueError(
                    f"{root}: skill {skill} differs from the Codex distribution"
                )


HOOK_SKILLS = {
    "ralph-loop": "ralph-loop",
    "cancel-ralph": "ralph-loop",
    "ralph-loop-help": "ralph-loop",
    "advisor": "advisor",
    "continual-learning": "continual-learning",
}
HOOK_SOURCE = Path(__file__).parent / "codex_hooks"
HOOK_COMMAND = 'python3 "${PLUGIN_ROOT}/scripts/runtime.py" stop'
HOOK_CONTENT_PATHS = (
    "skills",
    "scripts",
    "hooks",
    "licenses",
    "LICENSE",
    "metadata.json",
)
HOOK_UPSTREAM = {
    "version": "1.0.0",
    "displayName": "Codex Hooks (opt-in)",
    "description": "Opt-in finite Ralph loops, advisor nudges, and session preference checkpoints for Codex.",
    "author": {"name": FALLBACK_AUTHOR},
}


def hook_metadata(repository: str, provenance: dict[str, str]) -> dict:
    plan = PluginPlan(
        "codex-hooks", HOOK_UPSTREAM, tuple(sorted(HOOK_SKILLS)), Path("LICENSE")
    )
    _, compat = manifests(plan, "1.0.0", repository)
    compat["hooks"] = "./hooks/hooks.json"
    return {"compat": compat, "upstream_plugins": provenance}


def write_hook_plugin(
    skills: Iterable[PluginSkill], destination: Path, repository: str
) -> list[dict[str, object]]:
    selected = {skill.name: skill for skill in skills if skill.name in HOOK_SKILLS}
    if set(selected) != set(HOOK_SKILLS):
        return []
    if any(skill.plugin_name != HOOK_SKILLS[name] for name, skill in selected.items()):
        raise ValueError("hook Skills must come from their declared upstream plugins")
    root = destination / "codex-hooks"
    shutil.copytree(HOOK_SOURCE / "skills", root / "skills")
    (root / "scripts").mkdir()
    shutil.copy2(HOOK_SOURCE / "runtime.py", root / "scripts/runtime.py")
    shutil.copy2(Path(__file__).resolve().parents[1] / "LICENSE", root / "LICENSE")
    for upstream_name in sorted(set(HOOK_SKILLS.values())):
        member = next(
            skill for skill in selected.values() if skill.plugin_name == upstream_name
        )
        target = root / "licenses" / (upstream_name + ".txt")
        target.parent.mkdir(exist_ok=True)
        shutil.copy2(member.license_file, target)
        for name, origin in HOOK_SKILLS.items():
            if origin == upstream_name:
                shutil.copy2(member.license_file, root / "skills" / name / "LICENSE")
    write_json(
        root / "hooks/hooks.json",
        {
            "hooks": {
                "Stop": [{"hooks": [{"type": "command", "command": HOOK_COMMAND}]}]
            }
        },
    )
    provenance = {
        member.plugin_name: member.plugin_version for member in selected.values()
    }
    metadata = hook_metadata(repository, provenance)
    compat = metadata["compat"].copy()
    write_json(root / "metadata.json", metadata)
    digest = tree_digest([root / p for p in HOOK_CONTENT_PATHS], root)
    version = plugin_version(HOOK_UPSTREAM, digest)
    compat["version"] = version
    write_json(root / ".codex-plugin/plugin.json", compat)
    return [
        {
            "name": "codex-hooks",
            "variant": "hooks",
            "version": version,
            "category": compat["interface"]["category"],
            "skills": sorted(HOOK_SKILLS),
        }
    ]


def verify_hook_plugin(root: Path, entry: dict[str, object], output: Path) -> None:
    if entry.get("name") != "codex-hooks" or entry.get("skills") != sorted(HOOK_SKILLS):
        raise ValueError("unsupported hook plugin inventory")
    for name, upstream in HOOK_SKILLS.items():
        actual = directory_files(root / "skills" / name)
        expected = directory_files(HOOK_SOURCE / "skills" / name)
        expected["LICENSE"] = (
            output / PLUGIN_DIRECTORY / upstream / "LICENSE"
        ).read_bytes()
        if actual != expected:
            raise ValueError(f"{root}: unrecognized hook Skill variant {name}")
    if (root / "scripts/runtime.py").read_bytes() != (
        HOOK_SOURCE / "runtime.py"
    ).read_bytes():
        raise ValueError(f"{root}: hook runtime differs from source")
    hooks = json.loads((root / "hooks/hooks.json").read_text())
    if hooks != {
        "hooks": {"Stop": [{"hooks": [{"type": "command", "command": HOOK_COMMAND}]}]}
    }:
        raise ValueError(f"{root}: undeclared hooks")
    for upstream in set(HOOK_SKILLS.values()):
        if (root / "licenses" / (upstream + ".txt")).read_bytes() != (
            output / PLUGIN_DIRECTORY / upstream / "LICENSE"
        ).read_bytes():
            raise ValueError(f"{root}: missing or changed upstream license")
    metadata = json.loads((root / "metadata.json").read_text())
    manifest = json.loads((output / "manifest.json").read_text())
    provenance = {
        skill["plugin"]: skill["plugin_version"]
        for skill in manifest["skills"]
        if skill["plugin"] in set(HOOK_SKILLS.values())
    }
    if metadata != hook_metadata(manifest["source"], provenance):
        raise ValueError(f"{root}: unrecognized hook metadata")
    if (root / "LICENSE").read_bytes() != (
        Path(__file__).resolve().parents[1] / "LICENSE"
    ).read_bytes():
        raise ValueError(f"{root}: changed adapter license")
    expected_files = {
        ".codex-plugin/plugin.json",
        "LICENSE",
        "metadata.json",
        "hooks/hooks.json",
        "scripts/runtime.py",
    }
    expected_files.update(
        "licenses/" + name + ".txt" for name in set(HOOK_SKILLS.values())
    )
    for name in HOOK_SKILLS:
        expected_files.update(
            "skills/" + name + "/" + path
            for path in directory_files(HOOK_SOURCE / "skills" / name)
        )
        expected_files.add("skills/" + name + "/LICENSE")
    if set(directory_files(root)) != expected_files:
        raise ValueError(f"{root}: undeclared hook resources")
    digest = tree_digest([root / p for p in HOOK_CONTENT_PATHS], root)
    version = plugin_version({"version": "1.0.0"}, digest)
    if version != entry.get("version"):
        raise ValueError(f"{root}: hook version does not match resources")
    for relative, key in [(".codex-plugin/plugin.json", "compat")]:
        expected = {**metadata[key], "version": version}
        if json.loads((root / relative).read_text()) != expected:
            raise ValueError(f"{root}: hook metadata differs from manifest")
