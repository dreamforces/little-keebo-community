# Little Keebo community library

Extensions, phrasebooks and templates for Little Keebo, written by the people who use it. This is the community shelf the app lists.

- **Extensions** are one JavaScript file each: `/commands`, abbreviations, `//note` compose, spelling and grammar marks, and ⌃⌘/ actions.
- **Phrasebooks** give the writing model a field and its terms, so suggestions use that field's words.
- **Templates** are text with blanks to fill in: type `;` and a template's trigger, then Tab.

```
extensions/*.js         extensions, one JavaScript file each
extensions/index.json   generated
phrases/*.json          phrasebooks (schema 3)
phrases/index.json      generated
templates/*.json        template packs (schema 2)
templates/index.json    generated
scripts/                index builder, template pack check, and the publisher the workflow runs
EXTENSIONS.md           the guide: the file format and every function a script can call
```

Only a person merges to `main`, and `publish` then waits for a person to approve the run before it publishes the library to `downloads.littlekeebo.app` (`.github/workflows/publish.yml`): each new package
version goes up once under `extensions/community/<shelf>/<id>/<version>/`, and each shelf's index is signed with the
community library's key and written to `feeds/community/<shelf>/index.json`. The app checks that signature before it trusts
an index, then checks each download against the SHA-256 the index lists. Extensions run in a sandbox with no files or keys, and a script uses the network only after the writer allows that one.

## Suggesting a package

Every submission is reviewed by hand, and nothing is published until a person has approved it. A review can take days, and
a pull request may be changed or closed. What is checked is in [REVIEWING.md](REVIEWING.md).

## Writing your own

1. Read [EXTENSIONS.md](EXTENSIONS.md). Copy a sample, change its id, and install it in the app from a file to try it.
   - [`extensions/wordcount.js`](extensions/wordcount.js)
   - [`phrases/cooking.json`](phrases/cooking.json)
   - [`templates/thank-you.json`](templates/thank-you.json)
2. Put your file on its shelf and run `python3 scripts/build-extension-index.py` at the root. For a template pack, also check
   it against the schema the app reads, as the pull request's check does (it needs `pip install jsonschema`):
   `curl -so /tmp/schema.json https://littlekeebo.app/schema/template-pack.schema.json && python3 scripts/check-templates.py /tmp/schema.json templates/<yours>.json`
3. Commit the file with the shelf's `index.json` and open a pull request. It is reviewed by hand, which may take days. A version is published once: to change a package
   once it is out, bump its `version`.
