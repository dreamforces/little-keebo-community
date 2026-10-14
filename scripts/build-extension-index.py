#!/usr/bin/env python3
"""Run at the root of a library: writes extensions/index.json, phrases/index.json and templates/index.json.

Little Keebo lists what each index lists and installs a package only if its SHA-256 matches, so run
this after every change and commit the packages with their indexes.

The same file is library/scripts/build-extension-index.py in dreamforces/little-keebo and scripts/build-extension-index.py in
dreamforces/little-keebo-community; the library's check fails when the two differ.
"""
import hashlib, json, pathlib

def count(n, noun):
    plural = noun[:-1] + "ies" if noun.endswith("y") else noun + "s"
    return f"{n} {noun if n == 1 else plural}" if n else None

phrases = pathlib.Path("phrases")
phrases.mkdir(exist_ok=True)
entries = []
for path in sorted(phrases.glob("*.json")):
    if path.name == "index.json":
        continue
    data = path.read_bytes()
    package = json.loads(data)
    assert package.get("schemaVersion") == 3, f"{path}: phrases/ holds phrasebooks (schema 3)"
    assert package["id"] not in {e["id"] for e in entries}, f"{path}: duplicate id"
    entry = {key: package[key] for key in ("id", "name", "description", "author", "version")}
    entry.update(path=path.as_posix(), sha256=hashlib.sha256(data).hexdigest(),
                 capabilities=[c for c in [count(len(package.get("terms", [])), "term")] if c])
    if package.get("tags"):
        entry["tags"] = package["tags"]
    entries.append(entry)
entries.sort(key=lambda entry: entry["id"])
(phrases / "index.json").write_text(json.dumps({"schemaVersion": 1, "packages": entries}, indent=2, ensure_ascii=False) + "\n")
print(f"phrases/index.json: {len(entries)} package(s)")

extensions = pathlib.Path("extensions")
extensions.mkdir(exist_ok=True)
entries = []
for path in sorted(extensions.glob("*.js")):
    data = path.read_bytes()
    first = data.splitlines()[0].decode()
    assert first.startswith("// keebo "), f"{path}: missing // keebo header"
    header = json.loads(first[len("// keebo "):])
    source = data.decode()
    assert "keebo.define(" in source, f"{path}: an extension calls keebo.define"
    assert header["id"] not in {e["id"] for e in entries}, f"{path}: duplicate id"
    entry = {key: header[key] for key in ("id", "name", "description", "author", "version")}
    entry.update(path=path.as_posix(), sha256=hashlib.sha256(data).hexdigest(), capabilities=header.get("capabilities") or [])
    if header.get("tags"):
        entry["tags"] = header["tags"]
    if header.get("icon"):
        entry["icon"] = header["icon"]
    entries.append(entry)
entries.sort(key=lambda entry: entry["id"])
(extensions / "index.json").write_text(json.dumps({"schemaVersion": 1, "packages": entries}, indent=2, ensure_ascii=False) + "\n")
print(f"extensions/index.json: {len(entries)} package(s)")

templates = pathlib.Path("templates")
templates.mkdir(exist_ok=True)
entries = []
for path in sorted(templates.glob("*.json")):
    if path.name == "index.json":
        continue
    data = path.read_bytes()
    package = json.loads(data)
    assert package.get("schemaVersion") == 2, f"{path}: templates/ holds template packs (schema 2)"
    assert package["id"] not in {e["id"] for e in entries}, f"{path}: duplicate id"
    ids = [t.get("id") for t in package["templates"]]
    assert all(ids) and len(set(ids)) == len(ids), f"{path}: every template has its own id"
    names = {}
    for name in package.get("categories", []) + [t["category"] for t in package["templates"] if t.get("category")]:
        names.setdefault(name.casefold(), name)
    entry = {key: package[key] for key in ("id", "name", "description", "author", "version")}
    entry.update(path=path.as_posix(), sha256=hashlib.sha256(data).hexdigest(), schema=package["schemaVersion"],
                 capabilities=[c for c in [count(len(package["templates"]), "template"), count(len(names), "category")] if c])
    if package.get("tags"):
        entry["tags"] = package["tags"]
    entries.append(entry)
entries.sort(key=lambda entry: entry["id"])
(templates / "index.json").write_text(json.dumps({"schemaVersion": 1, "packages": entries}, indent=2, ensure_ascii=False) + "\n")
print(f"templates/index.json: {len(entries)} package(s)")
