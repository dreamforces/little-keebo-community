# Reviewing a submission

Every pull request is read by a person before it is merged, and `publish` waits for a person to approve it before anything goes to `downloads.littlekeebo.app`. This is the checklist for that read. It applies to the pull request's whole diff, not only the new file.

## An extension (`extensions/*.js`)

- **What leaves the Mac, and to whom.** Without `network: true` an extension has nothing to send. With it, list every `keebo.fetch` address and what goes in it (the text the writer typed, the selection, a setting). Anything the writer typed that goes to a host the extension does not say so about is a reason to refuse.
- **Hosts match the words.** The hosts the code reaches are the hosts the description and `capabilities` name, and `"network"` is in the header's `capabilities` if and only if `network: true` is in `keebo.define`. The header and `keebo.define` describe the same extension.
- **Nothing hidden.** No `eval`, `Function(...)`, built-up code strings, encoded or minified blobs, or addresses assembled at run time. If a line cannot be read, ask the author to write it plainly.
- **Licence of anything bundled.** Word lists, data or code copied from elsewhere need a licence that allows redistribution, and the author's say-so that it is theirs to give. Name the source in the pull request.
- **Version.** A new package starts at a sensible `1.0.0`. A change to a published package bumps `version`, because a version is published once.
- **No personal data.** Examples, defaults and comments hold no real names, addresses, numbers or keys.
- **Does what it says.** Run it from a file in the app and try each command, abbreviation or action it declares.

## A phrasebook (`phrases/*.json`) or template pack (`templates/*.json`)

- The text is the author's own or under a licence that allows redistribution, with the source named.
- No personal data in examples, defaults or sample fields.
- Version bumped for a change to a published package.
- Nothing in the text promises advice the author cannot give (medical, legal or financial claims).

## Every pull request

- The shelf's `index.json` is the one `python3 scripts/build-extension-index.py` makes, and the `check` job is green.
- The diff touches nothing outside the package and its index. A change to `.github/`, `scripts/` or this file is reviewed as a change to how the library is published.
- Approve, ask for changes, or close with a reason. Review can take days; say so to the author if it will.
