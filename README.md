# Little Keebo community library

Extensions, phrasebooks and templates for Little Keebo, written by the people who use it. This is the community shelf the app lists.

- **Extensions** are one JavaScript file each: `/commands`, abbreviations, `//note` compose, spelling and grammar marks, and ⌃⌘/ actions.
- **Phrasebooks** give the writing model a field and its terms, so suggestions use that field's words.
- **Templates** are text with blanks to fill in, typed by entering `/~` and a trigger.

```
extensions/*.js         extensions, one JavaScript file each
extensions/index.json   generated
phrases/*.json          phrasebooks (schema 3)
phrases/index.json      generated
templates/*.json        template packs (schema 1)
templates/index.json    generated
scripts/                index builder
EXTENSIONS.md           the guide: the file format and every function a script can call
```

The app checks each download against the SHA-256 in the shelf's `index.json`. Extensions run in a sandbox with no files or keys, and a script uses the network only after the writer allows that one.

## Writing your own

1. Read [EXTENSIONS.md](EXTENSIONS.md). Copy a sample, change its id, and install it in the app from a file to try it.
   - [`extensions/wordcount.js`](extensions/wordcount.js)
   - [`phrases/cooking.json`](phrases/cooking.json)
   - [`templates/thank-you.json`](templates/thank-you.json)
2. Put your file on its shelf and run `python3 scripts/build-extension-index.py` at the root.
3. Commit the file with the shelf's `index.json` and open a pull request.
