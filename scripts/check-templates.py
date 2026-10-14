#!/usr/bin/env python3
"""Checks template packs against the schema the app reads: python3 scripts/check-templates.py <schema.json> <pack.json>…

The schema is https://littlekeebo.app/schema/template-pack.schema.json. Two rules it cannot say are checked here too: no two
templates in a pack share an id or a trigger. The app checks the rest when it installs a pack (each blank a template describes
is one its text has), so install yours from a file in the app before you open a pull request.
"""
import json
import sys

from jsonschema import Draft202012Validator


def problems(pack, validator):
    found = [f"{'/'.join(map(str, error.absolute_path)) or 'pack'}: {error.message}" for error in validator.iter_errors(pack)]
    templates = pack.get("templates", []) if isinstance(pack, dict) else []
    for key in ("id", "trigger"):
        values = [template.get(key) for template in templates if isinstance(template, dict) and key in template]
        found += [f"templates: two templates have the {key} {value}" for value in sorted({v for v in values if values.count(v) > 1})]
    return found


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__.split("\n")[0])
    with open(sys.argv[1]) as handle:
        validator = Draft202012Validator(json.load(handle))
    failed = False
    for path in sys.argv[2:]:
        if path.endswith("index.json"):
            continue
        with open(path) as handle:
            found = problems(json.load(handle), validator)
        for problem in found:
            print(f"error: {path}: {problem}")
        failed = failed or bool(found)
        if not found:
            print(f"ok: {path}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
