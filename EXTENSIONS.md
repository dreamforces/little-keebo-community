# Extension API

An extension is one JavaScript file. The script calls `keebo.define` once, and after that the only host it can reach is `keebo`. This page is the contract: the file, each thing a script can declare, and each `keebo` function, with an example.

The app ships no extensions. Install a `.js` file from **Extensions → Install from File** after **Allow third-party extensions**. Until that switch is on, search and install stay off. **Details** shows what a package adds. **Options…** draws the settings the script declares.

A phrasebook is a different file: JSON, no script. It is at the end of this page.

## Contents

- [The file](#the-file)
- [A first command](#a-first-command)
- [What `run` receives](#what-run-receives)
- [Settings](#settings)
- [Commands](#commands)
- [Asking the writing model](#asking-the-writing-model)
- [Selection commands](#selection-commands)
- [Commands the user writes](#commands-the-user-writes)
- [Abbreviations](#abbreviations)
- [Compose](#compose)
- [Marks](#marks)
- [Prompt style](#prompt-style)
- [Actions](#actions)
- [Models](#models)
- [Network](#network)
- [`keebo` functions](#keebo-functions)
- [Sandbox and limits](#sandbox-and-limits)
- [Phrasebooks](#phrasebooks)
- [Templates](#templates)
- [Publishing](#publishing)

## The file

The first line is a header. The rest of the file calls `keebo.define` once, with the same id, name, version, author, and description. A second `keebo.define` is rejected. The header and the call have to describe the same extension.

```js
// keebo {"id":"you.commands","name":"My Commands","version":"1.0.0","author":"You","description":"Word count.","tags":["commands"],"capabilities":["1 command"]}
keebo.define({
  id: "you.commands",
  name: "My Commands",
  version: "1.0.0",
  author: "You",
  description: "Word count.",
  commands: {
    wc: { title: "Word count", run(ctx) { return keebo.words(ctx.text).length + " words" } }
  }
})
```

| Field | Rule |
|---|---|
| `id` | Lowercase letters, digits, `.` and `-`. At least two segments, such as `you.commands`. At most 100 characters. |
| `name` | 1–80 characters. |
| `version` | `1.2.0`, three numbers. |
| `author` | At most 100 characters. |
| `description` | At most 160 characters, about two lines. Options and the list show two lines; the rest is the hover tip. |
| `tags` | On the header only, up to 8, each 1–24 characters. Tags inside `keebo.define` are ignored. |
| `capabilities` | On the header only. The library index shows this array before install. The app ignores it and reads what `keebo.define` declares. Use the same words the app would show: `1 command`, `2 actions`, `your commands`, `abbreviations`, `compose`, `prompt style`, `marks writing`, `translation model`, `network`. |

The file is at most 256 KB. A field this version of the app does not know is rejected, so a script cannot smuggle an extra key into `keebo.define`. Text the package shows (titles, help, options) cannot contain control characters. The extension has to declare something to do: a command, abbreviations, compose, marks, a prompt style, or an action.

`keebo.words`, `keebo.fetch`, and the other functions below exist inside `run` and `analyze`. They are not installed yet while the file is loading, so the top of the file can define helpers and then call `keebo.define`. It cannot call those functions there.

`throw new Error("use a whole number")` is how a command tells the writer what went wrong. The message is shown as the status.

## A first command

Save this as `wordcount.js` and install it from a file. Type `twelve apples /wc` and press Tab. The line becomes `2 words`.

```js
// keebo {"id":"you.wordcount","name":"Word Count","version":"1.0.0","author":"You","description":"Type /wc, then Tab, for the number of words.","tags":["commands"],"capabilities":["1 command"]}
keebo.define({
  id: "you.wordcount",
  name: "Word Count",
  version: "1.0.0",
  author: "You",
  description: "Type /wc, then Tab, for the number of words.",
  settings: [
    { id: "unit", title: "Say", type: "choice", options: ["words", "Wörter"], value: "words" }
  ],
  commands: {
    wc: {
      title: "Word count",
      usage: "[which]",
      examples: ["", "sentences"],
      run(ctx) {
        const count = ctx.args === "sentences" ? keebo.sentences(ctx.text).length : keebo.words(ctx.text).length
        return count + " " + ctx.settings.unit
      }
    }
  }
})
```

`run` returns a string or a number. That text replaces the slash command. In the scratchpad, line breaks in the string stay. In another app they are joined onto one line, because Return can send a message. A reply from the writing model, and an abbreviation with several lines, keep their breaks. See [Asking the writing model](#asking-the-writing-model) and [Abbreviations](#abbreviations).

Returning `""` removes the slash command and types nothing. That is allowed when the command has already posted a notice or a menu-bar line. An empty return with neither of those fails with “returned no text.”

## What `run` receives

`run(ctx)` gets one object. For `twelve apples /wc sentences` with the caret at the end of the line:

| Field | Value |
|---|---|
| `ctx.args` | `"sentences"` — the words after the name |
| `ctx.before` | `"twelve apples "` — the field before the slash command |
| `ctx.after` | `""` — the field after the caret |
| `ctx.text` | `ctx.before + ctx.after` |
| `ctx.language` | A BCP-47 tag for the writing, such as `en` or `tr`. English until the text shows otherwise. |
| `ctx.settings` | The extension’s settings, plus settings declared on this command. Keyed by id. |

A command runs when the slash is at the start of the line or after a space. `and/or` and a URL are left alone. Typing `/` opens a menu at the caret: five rows, ↑↓ or the scroll wheel to move, keep typing to narrow, Esc to close. Tab halfway through a name completes it. Tab on a whole name runs a command whose `usage` does not start with `<`, and only closes the menu for one that still needs words (`usage` starts with `<`).

Keep one command per file so two packages do not claim the same name. The engine allows up to 40 commands in one file. When two enabled extensions answer to the same name, the first one runs.

## Settings

Every option lives in the script. The app draws it. `settings` is a list of `{ id, title, type, value, help?, options?, custom?, columns?, when? }`. `value` is the default. What the writer saves replaces it, and a saved value that no longer fits falls back to the default. Ids are lowercase letters, digits, and `-`, up to 40 characters. At most 24 settings, including settings declared on a command.

`help` may contain Markdown links. Only `https` links stay clickable.

| `type` | `value` | What Options shows |
|---|---|---|
| `text` | string, up to 500 characters | a text field |
| `number` | integer 0–100000 | a stepper |
| `toggle` | `true` or `false` | a checkbox |
| `choice` | one of `options` (1–600, each 1–40 characters) | a pop-up menu |
| `choices` | a subset of `options` (1–40). With `custom: true`, also up to 20 names the writer types, comma-separated, each 1–40 characters | checkboxes |
| `list` | rows of `{ columnId: string }`, at most 100 | a table. A column with `code: true` is a JavaScript editor (a cell up to 4,000 characters). `multiline: true` is several lines (up to 500). `placeholder` shows while a cell is empty. 1–4 columns. |
| `info` | a string, 1–500 characters | a note. The writer cannot edit it, and the saved value has to stay the default. |

`when: { setting, equals }` shows an option only while another `choice` has that value. A hidden option still has its value, and `run` still reads it.

A command may declare its own `settings`. Options lists them under that command, and only that command’s `ctx.settings` includes them, together with the extension’s top-level settings.

```js
settings: [
  { id: "length", title: "Length", type: "number", value: 16, help: "4 to 128 characters." },
  { id: "characters", title: "Characters", type: "choice", value: "Letters and digits",
    options: ["Letters and digits", "Letters, digits and symbols", "Digits"] },
  { id: "symbols", title: "Symbols", type: "text", value: "!@#$%^&*_-+=?",
    when: { setting: "characters", equals: "Letters, digits and symbols" } },
  { id: "tones", title: "Tones", type: "choices", custom: true,
    options: ["Friendly", "Formal"], value: ["Friendly", "Formal"],
    help: "Add your own, such as Sarcastic." },
  { id: "accepted", title: "Words to accept", type: "list",
    columns: [{ id: "word", title: "Word", placeholder: "Little Keebo" }],
    value: [{ word: "Little Keebo" }] },
  { id: "stops", title: "How Tab moves", type: "info",
    value: "Type the trigger, then Tab. Tab walks $1, $2, and leaves the caret at $0." }
],
commands: {
  greet: {
    title: "Greet",
    settings: [
      { id: "who", title: "Name", type: "text", value: "there" }
    ],
    run(ctx) { return "Hello " + ctx.settings.who }
  }
}
```

Inside `run` and `analyze`, a text setting is a string, a number is a number, a toggle is a boolean, a choices setting is an array of strings, and a list is an array of row objects.

## Commands

`commands` is an object. The key is the script’s name for the command. The writer types that name after `/`, unless `nameFrom` says otherwise.

```js
settings: [
  { id: "command", title: "Command", type: "text", value: "date",
    help: "What you type after the /. Several names: date, d." }
],
commands: {
  date: {
    title: "Today's date",
    nameFrom: "command",
    usage: "[tomorrow or +7]",
    examples: ["", "yesterday", "+7"],
    run(ctx) {
      const given = String(ctx.args || "").trim()
      const iso = given ? keebo.date(given, { language: ctx.language }) : keebo.date("today")
      return iso
    }
  }
}
```

| Field | Meaning |
|---|---|
| `title` | 1–40 characters. Shown in the `/` menu and in Options. |
| `nameFrom` | The id of a top-level `text` setting. Its value is what the writer types after `/`. Several names are separated by commas or spaces: `date, d`. A leading `/` is stripped. Lowercase letters, digits, and hyphens, up to 40, plus `=` so the line can read `/= 3^2`. Empty or invalid falls back to the key (`date` here). |
| `usage` | Up to 40 characters, shown beside the name. `<time>` means words are required: Tab on the finished name waits for them. `[format]` means words are optional: Tab runs the command. |
| `examples` | Up to 4 strings, each the words after the name, up to 80 characters. `""` is the command on its own. Options shows `/date` and `/date yesterday`, and runs each one with the writer’s current settings. Live examples run when the command has `nameFrom` and no `written` samples. Notices and menu-bar lines are described in that preview; they are not posted. |
| `settings` | Options for this command only. See [Settings](#settings). |
| `selection` | `true` or omitted. See [Selection commands](#selection-commands). |
| `written` | Up to 4 `{ input, output }` samples for a command that asks the model. `input` is the words after the name (1–80). `output` is what the model wrote (1–1,200) and may contain line breaks. Options shows them as written and does not call the model. |

A line that starts with `/=`, or has `/=` after a space, is the command named `=` through the end of the line, so a later `/` is division.

## Asking the writing model

`run` may return `{ ask }` instead of text. Tab sends that to the writing model and types the reply. With a remote model, the app has to be one the writer allowed. Line breaks in the reply are kept, including in other apps.

```js
run(ctx) {
  keebo.loading(true)
  return {
    ask: {
      instruction: "Write placeholder prose about the topic. Return only the prose.",
      text: "Topic: " + (ctx.args || "none"),
      examples: [
        { user: "Topic: tea", reply: "Tea has been brewed for thousands of years." }
      ],
      maxTokens: 400,
      separateParagraphs: false
    }
  }
}
```

| Field | Rule |
|---|---|
| `instruction` | System prompt. 1–2,000 characters. |
| `text` | What to write. 1–2,000 characters. |
| `examples` | Up to 4 `{ user, reply }` turns, each side 1–800 characters. A small model follows these. |
| `maxTokens` | Clamped to 32–2,048. The default is 512. |
| `separateParagraphs` | `true` turns a single line break in the reply into a blank line. |

Leave `keebo.loading(true)` on when you return `ask`. The spinner stays up while the model answers, and the app turns it off when the reply arrives. Anything else in the returned object, or an `ask` that breaks these limits, fails the command.

Pair this with `written` samples so Options can show a result without calling the model. See [Commands](#commands).

## Selection commands

⌃⌘/ lists a command when `usage` is exactly `<text>`, or when the command sets `selection: true`. Choosing it runs the same `run(ctx)`, with the selected text as `ctx.args`. The string it returns replaces the selection.

```js
commands: {
  latin: {
    title: "Plain Latin letters",
    usage: "<text>",
    selection: true,
    examples: ["Café İzmir"],
    run(ctx) {
      if (!ctx.args) throw new Error("type some text after the command.")
      return keebo.latin(ctx.args)
    }
  }
}
```

Put `"1 action"` in the header `capabilities` next to `"1 command"`, so the library can say so before install. A command’s name and an action’s id have to differ. Commands the writer types in Options (`commandsFrom`) are not listed in ⌃⌘/.

## Commands the user writes

`commandsFrom` names a `list` setting with a `name` column and a `run` column. The `run` column is `code: true`: each cell is a function body, with `ctx` already in scope.

```js
keebo.define({
  id: "you.mine",
  name: "My Commands",
  version: "1.0.0",
  author: "You",
  description: "Commands you write in Options.",
  settings: [
    { id: "commands", title: "Commands", type: "list",
      columns: [
        { id: "name", title: "Name", placeholder: "wc" },
        { id: "run", title: "JavaScript", code: true, placeholder: "return ctx.text.length" }
      ],
      value: [{ name: "chars", run: "return ctx.text.length + ' characters'" }] }
  ],
  commandsFrom: "commands"
})
```

The name follows the same rules as a command key. These commands have no options of their own. They read `ctx.args`, `ctx.text`, and the extension’s top-level settings. Put `"your commands"` in the header `capabilities`.

## Abbreviations

`expansionsFrom` names a `list` setting with `trigger` and `text` columns. The writer types `;` and a trigger (`;brb`), then Tab, and the trigger is replaced (the writer can choose `;;` or `,,` instead of `;`). A plain word never expands. A trigger is 1–40 characters with no space. The replacement is 1–500 characters.

```js
settings: [
  { id: "abbreviations", title: "Abbreviations", type: "list",
    columns: [
      { id: "trigger", title: "Type", placeholder: "brb" },
      { id: "text", title: "Becomes", placeholder: "The text to type. Return adds a line.", multiline: true }
    ],
    value: [
      { trigger: "brb", text: "be right back" },
      { trigger: "late", text: "Hi ${1:everyone},\n\nSorry, ${2:10 minutes}." }
    ] }
],
expansionsFrom: "abbreviations"
```

`typedExpansions: true` expands the trigger as it is typed, such as `+1` or `<3`, and those rows are not listed after `;`. `{skin}` in the replacement becomes the skin-tone modifier from a `choice` setting whose id is `skin`, when that choice is an emoji of the tone. It becomes nothing when the emoji has no tone.

```js
settings: [
  { id: "skin", title: "Skin tone", type: "choice", value: "👍",
    options: ["👍", "👍🏻", "👍🏼", "👍🏽", "👍🏾", "👍🏿"] },
  { id: "emoji", title: "Replacements", type: "list",
    columns: [{ id: "trigger", title: "You type" }, { id: "text", title: "Emoji" }],
    value: [{ trigger: ":)", text: "😊" }, { trigger: "+1", text: "👍{skin}" }] }
],
expansionsFrom: "emoji",
typedExpansions: true
```

Put `"abbreviations"` in the header `capabilities`.

### Tab stops

Stops in an abbreviation’s text are written the way TextMate writes them.

| You write | What happens |
|---|---|
| `$1`, `$2`, … | Places Tab visits, in order. A number used twice is one stop, at its first place. |
| `${1:name}` | A stop whose default is selected when Tab arrives. Typing replaces it. |
| `$0` | Where the caret ends. With no `$0`, it ends at the end of the text. |
| `\$` | A dollar sign. `$5` is stop 5, so a price is `\$5`. |
| `\}` | A brace inside a default. |
| `\\` | A backslash. |

After the expansion, the first stop is selected. Tab goes to the next and Shift-Tab back. The last Tab leaves the caret at `$0`. A click, an arrow key, Esc, or another app ends it. Lines are typed as Shift-Return, so they do not send a chat message. In an Excel cell that chord is Control-Option-Return, because Shift-Return would commit the cell.

Give the `text` column `multiline: true` when a replacement has several lines. Tab types the expansion whole. The menu bar says which trigger expanded. The first stop is selected once the field has finished taking the keys, a moment later, longer in Notes. Where the field does not report its selection (canvas editors such as PowerPoint), or counts positions differently (the ChatGPT app), arrow keys move the caret, so a shortcut that deletes more than one character can leave the stop.

## Compose

`compose` is a slash command whose name defaults to `/`, so the line reads `//note`. `nameFrom` points at a `text` setting. The writer can set that to `write` and type `/write` instead. `/` or `//` in that setting always means the default `//note`.

```js
settings: [
  { id: "command", title: "Command", type: "text", value: "/",
    help: "What you type after the first /. The default reads //note. Try write for /write." },
  { id: "tone", title: "Tone", type: "choice",
    options: ["Friendly", "Formal", "Direct", "Executive"], value: "Friendly" },
  { id: "length", title: "Length", type: "choice",
    options: ["as short as possible", "a sentence", "a paragraph", "unlimited"], value: "unlimited" }
],
compose: {
  nameFrom: "command",
  title: "Write from a note",
  usage: "<note>",
  examples: [
    { input: "thank Rachel for coming yesterday", output: "Rachel, thank you so much for coming yesterday." },
    { input: "capital of France", output: "Paris" }
  ],
  instruction: "Expand the note into a {tone} message that the writer sends. When expanding or rephrasing, the length is {length}."
}
```

Tab on `//note` sends the note, and up to 500 characters of text before it, to the writing model. What the model writes replaces the note, so it carries on from the text before it. `{setting-id}` in `instruction` is replaced with that setting’s value. A list setting is left as written. With a remote model, the text before the note is sent only from apps the writer allowed.

The note’s first word routes it. tell, ask, offer, suggest, thank, remind… is written as the words the writer says. write, explain, describe… is written out. list and name are answered. Otherwise the model is first asked whether anyone could answer the note from general knowledge: if so, it returns only the answer; if not, the note is the writer’s own words, with the grammar fixed.

`instruction` is 1–3,000 characters. `title` and `usage` are up to 40. `examples` are up to 4 `{ input, output }` pairs (`input` 1–120, `output` 1–300) shown in Options. Compose is not run there, because it needs a model. Put `"compose"` in the header `capabilities`.

## Marks

`analyze(text, settings)` runs in the background after the writer pauses, one paragraph at a time. An unchanged paragraph is not analyzed again. A paragraph that throws, or that takes longer than 250 ms, contributes no marks. The passage is capped at 50,000 UTF-16 units.

`settings` here is every setting, keyed by id, in the same shapes as `ctx.settings`.

```js
settings: [
  { id: "max-words", title: "Max words", type: "number", value: 25 },
  { id: "fix", title: "Fix typos", type: "toggle", value: false }
],
actions: [
  { id: "shorten", title: "Shorten",
    instruction: "Make the text a little shorter without losing meaning. Return only the shortened text." }
],
analyze(text, settings) {
  for (const sentence of keebo.sentences(text)) {
    if (sentence.words > settings["max-words"]) {
      keebo.mark(sentence, "This sentence is long.", { action: "shorten" })
    }
  }
  for (const hit of keebo.proofread(text)) {
    keebo.mark(hit, hit.message, {
      kind: hit.kind,
      replacement: hit.guesses[0],
      apply: settings.fix && hit.kind === "spelling" && !!hit.guesses[0]
    })
  }
}
```

`keebo.mark` is specified under [Functions](#keebomarkspan-message-options). Put `"marks writing"` in the header `capabilities`.

## Prompt style

`style` is added to every suggestion, or only in the apps whose bundle ids you list. The key in the script is `style`. The instruction is 1–300 characters. `vocabulary` is at most 64 words of 1–40 characters. `apps` is at most 50 bundle ids.

```js
style: {
  instruction: "Write in the writer's usual clinical voice. Prefer the vocabulary when it fits.",
  vocabulary: ["follow-up", "workup"],
  apps: ["com.apple.Notes"]
}
```

Put `"prompt style"` in the header `capabilities`. A phrasebook is the other way to steer vocabulary, and it needs no script. See [Phrasebooks](#phrasebooks).

## Actions

`actions` are ⌃⌘/ rewrites. The model receives the instruction and the selection. `{argument}` is the submenu choice. `{setting-id}` is replaced with that setting’s value before the choice is filled in.

```js
settings: [
  { id: "tones", title: "Tones", type: "choices", custom: true,
    options: ["Friendly", "Formal", "Direct", "Executive"],
    value: ["Friendly", "Formal", "Direct", "Executive"] },
  { id: "shorter", title: "Shorten to", type: "choice",
    options: ["a little shorter", "about half", "one sentence"], value: "about half" }
],
actions: [
  { id: "shorten", title: "Shorten", symbol: "arrow.down.right.and.arrow.up.left",
    instruction: "Make the text {shorter} without losing meaning. Return only the shortened text." },
  { id: "tone", title: "Change Tone", symbol: "theatermasks",
    argumentsFrom: "tones",
    instruction: "Rewrite the text in a {argument} tone, preserving meaning. Return only the rewritten text." }
]
```

| Field | Rule |
|---|---|
| `id` | Lowercase letters, digits, and `-`, 1–40. Unique, and different from any selection command’s name. |
| `title` | 1–40 characters. |
| `instruction` | 1–1,000 characters. |
| `arguments` | Up to 12 choices, each 1–40 characters. |
| `argumentsFrom` | The id of a `choices` setting. Use this or `arguments`, not both. |
| `symbol` | An SF Symbol name: lowercase letters, digits, and dots, 1–60 characters. The default icon is a puzzle piece. |
| `model` | A catalog tool-model id for this action alone. See [Models](#models). |
| `category` | The group ⌃⌘/ lists it under. See [Categories](#categories). Optional. |

At most 20 actions. A command listed in ⌃⌘/ appears in the same menu and runs `run(ctx)` instead of the model. Put `"7 actions"` (the count) in the header `capabilities`. Selection commands count toward that number.

### Categories

⌃⌘/ lists actions and selection commands in groups, each under a small heading, and each row is a slash name: `/enrich`, `/base64`. The group is the `category`: a string of 1–24 characters. Without one an action that runs the model is in **Intelligence** and a selection command is in **Transform**, so most extensions need nothing. Set `category` on the extension to put everything it lists in one group, or on a single action or command to move that one. **Intelligence** is listed first and **Transform** second, then any other group in the order they first appear. When every row falls in one group there are no headings.

Words typed after an action’s name go to it as an extra instruction (`/summarise in two paragraphs`), except for an action with choices or its own `model`, and a selection command, which take none.

```js
category: "Language",           // for everything this extension lists in ⌃⌘/
actions: [
  { id: "formal", title: "Make Formal", category: "Intelligence",  // this one is moved
    instruction: "Rewrite the text in a formal tone. Return only the rewritten text." }
]
```

## Models

`model` is the tool model the package’s actions run. A suggestion model is not a tool model. The catalog id the app ships for this is `translategemma-4b-q4`. An action’s own `model` wins over the package model.

```js
model: "translategemma-4b-q4",
actions: [
  { id: "translate", title: "Translate", symbol: "character.book.closed",
    argumentsFrom: "languages",
    instruction: "Translate the following text into {argument}. Output only the translated result:" }
]
```

The other form is a pinned Hugging Face GGUF. The app builds the download address and checks the file. The script never names a URL.

```js
model: {
  name: "Lexy",
  repository: "owner/name",
  revision: "0123456789abcdef0123456789abcdef01234567",
  file: "model.Q4_K_M.gguf",
  bytes: 2489909760,
  sha256: "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
}
```

`repository` is `owner/name`. `revision` is a 40-character commit. `file` ends in `.gguf`. `sha256` is 64 hex characters. `bytes` is the file size, up to 40 GB. Name one of the two forms. A model with no actions is rejected. Put `"translation model"` in the header `capabilities`.

## Network

`network: true` allows `keebo.fetch` from a command. It stays off until the writer allows that extension. Declining leaves it off, and turning it on later asks again. Put `"network"` in the header `capabilities` so the library can say so before install. The call itself is [`keebo.fetch`](#keebofetchurl).

```js
keebo.define({
  id: "you.rates",
  name: "Rates",
  version: "1.0.0",
  author: "You",
  description: "Type /rate, then Tab, for a sample rate.",
  network: true,
  commands: {
    rate: {
      title: "Rate",
      run() {
        keebo.loading(true)
        try {
          return keebo.fetch("https://api.frankfurter.app/latest?from=USD&to=GBP")
        } finally {
          keebo.loading(false)
        }
      }
    }
  }
})
```

## `keebo` functions

Call these from `run` or from `analyze`. Each extension has its own JavaScript context. Spans use UTF-16 offsets, the same indexes JavaScript uses.

A span is `{ text, start, end, words, kind, message, guesses }`. `start` is inclusive and `end` is exclusive.

### `keebo.words(text)`

Words that contain a letter.

```js
run(ctx) { return keebo.words(ctx.text).length + " words" }
```

### `keebo.sentences(text)`

Sentences. `words` on each span is how many words that sentence has.

```js
run(ctx) { return keebo.sentences(ctx.text).length + " sentences" }
```

### `keebo.repetitions(text)`

Content words repeated within a short window. Each span’s `message` says which word.

```js
analyze(text) {
  for (const hit of keebo.repetitions(text)) keebo.mark(hit, hit.message)
}
```

### `keebo.passive(text)`

A form of “to be” followed by a past participle.

```js
analyze(text) {
  for (const hit of keebo.passive(text)) keebo.mark(hit, hit.message, { kind: "passiveVoice" })
}
```

### `keebo.proofread(text)`

The macOS spelling and grammar checker, in the language it detects, in one pass. Read only: nothing is added to the user dictionary. `kind` is `"spelling"` or `"grammar"`. `guesses` holds up to five suggestions. `message` is the checker’s description.

```js
analyze(text, settings) {
  const accepted = new Set((settings.accepted || []).map((row) => (row.word || "").toLowerCase()))
  for (const hit of keebo.proofread(text)) {
    if (hit.kind === "spelling" && accepted.has(hit.text.toLowerCase())) continue
    keebo.mark(hit, hit.message, { kind: hit.kind, replacement: hit.guesses[0] })
  }
}
```

### `keebo.mark(span, message, options)`

Underlines `span` in the paragraph `analyze` was given. A bad span is ignored. `message` is 1–160 characters and cannot contain control characters.

`span` needs numeric `start` and `end` inside that paragraph. A span from `keebo.sentences` or `keebo.proofread` can be passed through.

| `options` | Effect |
|---|---|
| `replacement` | Suggested text, 1–120 characters, no control characters. |
| `kind` | `spelling`, `grammar`, `punctuation`, `repetition`, `passiveVoice`, `cliche`, `inclusive`, or `custom`. The default is `custom`. Spelling and grammar use those colours. |
| `action` | The id of an action this package declares. Accepting the underline runs that action. |
| `apply` | `true` replaces the span in the scratchpad when `replacement` is set. Elsewhere the span is only underlined. |

```js
keebo.mark(sentence, "This sentence is long.", { action: "shorten", kind: "custom" })
```

`analyze` is the only place `keebo.mark` does anything. A command cannot leave marks behind.

### `keebo.random(n)`

A whole number from 0 up to `n`, not including `n`, from the system generator. `n` is a finite number from 1 through 9007199254740992. Anything else returns 0.

```js
run() {
  const faces = ["heads", "tails"]
  return faces[keebo.random(faces.length)]
}
```

### `keebo.latin(text)`

The text in plain Latin letters. `İzmir` becomes `Izmir`, `Café` becomes `Cafe`.

```js
run(ctx) { return keebo.latin(ctx.args) }
```

### `keebo.base64Encode(text)`

Standard Base64 of the UTF-8 text.

```js
run(ctx) { return keebo.base64Encode(ctx.args) }
```

### `keebo.base64Decode(text)`

The UTF-8 text, or `null` when the string is not Base64 of UTF-8. Unknown characters in the alphabet are ignored.

```js
run(ctx) {
  const text = keebo.base64Decode(ctx.args)
  if (text == null) throw new Error("that is not Base64.")
  return text
}
```

### `keebo.date(text, options)`

A date as `YYYY-MM-DD`, on this Mac’s calendar. It throws when it does not understand the text, or the day is not real.

`options.language` reads an ambiguous number. `en` and `en-US` take the month first. Any other language takes the day first. A part over 12 settles the order. With no language, it reads as English.

It understands today, tomorrow, yesterday, `+7` and `-3`; Tuesday, next Tue, and last Thursday; last Thursday of the last month and first Monday of October; 6 October 2026, October 6, 2026, 2026-10-06, 29/01/2026, and 01/29/2026. `next Tuesday` is the coming one, after today. A month named without a year is this year.

```js
run(ctx) {
  return keebo.date(ctx.args || "today", { language: ctx.language })
}
```

### `keebo.notify(title, message, options)`

Posts one notice from a command. Returns `true` when it was accepted. Returns `false` when it was rejected. `analyze` cannot post; the call returns `false`.

| Argument | Rule |
|---|---|
| `title` | Required. 1–80 characters. |
| `message` | Up to 200 characters. Pass `""` when there is nothing more to say. |
| `options.after` | Whole seconds from the moment the command finishes, 0–86400. Omit it, or pass 0, to show the notice as soon as the command finishes. A fraction is rejected. |
| `options.symbol` | An SF Symbol name: a lowercase letter, then lowercase letters, digits, and dots, at most 40 characters. `bell` when omitted. |
| `options.motion` | `rotate`, `scale`, `bounce`, or `shake`. Omit it and the icon stays still. When the notice is shown, the menu bar plays it until the notice is dismissed. A click on the icon stops it. `rotate` spins, `scale` pulses, `bounce` hops, and `shake` rocks the icon on its feet without changing its size. Any symbol can use them. |

A command may post up to 8 notices. A delayed notice is shown when it is due. It goes to the one place chosen in Apps: under the menu bar icon, or Notification Center. A delay does not put a countdown on the icon. That is `keebo.menubar`. Options describes a notice in the example preview and does not post it.

```js
run(ctx) {
  const seconds = 60
  if (!keebo.notify("Time is up", "tea", { after: seconds, symbol: "hourglass" })) {
    throw new Error("that timer could not be set.")
  }
  return ""
}
```

The same call rocks the menu bar icon when the notice appears. It keeps rocking until the notice is dismissed.

```js
run() {
  keebo.notify("Stand up", "time to stretch", { symbol: "figure.walk", motion: "shake" })
  return ""
}
```

### `keebo.ack(symbol, options)`

Plays the menu-bar icon for one second, so a command can confirm it ran without posting a notice. A menu-bar line already showing keeps its text beside the animation. Returns `false` when the symbol or the motion is rejected. `analyze` cannot play it.

`symbol` follows the same rule as `options.symbol` on `notify`. `options.motion` is `rotate`, `scale`, `bounce`, or `shake`. Omit it for `rotate`. `shake` is the same rock as on a notice: the icon tips onto one foot, then the other, and stays the same size. One animation per command; a second call replaces it. This one lasts a second. A notice's motion keeps going until the notice is dismissed.

```js
run() {
  keebo.ack("checkmark.circle", { motion: "scale" })
  return "saved"
}
```

### `keebo.loading(on)`

Shows a spinner at the text caret while a command is still working. Pass `true` before a network call or other wait, and `false` when that work is done. Returns `false` when `on` is not a boolean, or when the call is outside `run`. A later call replaces the earlier one.

Leave it `true` when `run` returns an `ask`. The spinner stays up while the writing model answers.

```js
run() {
  keebo.loading(true)
  try {
    return keebo.fetch("https://api.frankfurter.app/latest?from=USD&to=GBP")
  } finally {
    keebo.loading(false)
  }
}
```

### `keebo.cursor(name)`

Changes the pointer for half a second, wherever it is, including in another app. It does not change the menu-bar animation. Returns `false` when this Mac has no such cursor. `analyze` cannot set it. One call per command; a second call replaces it.

`name` is a system cursor, or any SF Symbol this Mac has (the same shape as `options.symbol` on `notify`, so `hourglass` works).

System cursors: `arrow`, `iBeam`, `iBeamVertical`, `crosshair`, `pointingHand`, `openHand`, `closedHand`, `operationNotAllowed`, `disappearingItem`, `dragCopy`, `dragLink`, `contextualMenu`, and `wait` (the spinning beachball). On macOS 15 and later, also `zoomIn`, `zoomOut`, `columnResize`, and `rowResize`.

```js
run() {
  keebo.cursor("pointingHand")
  return "look"
}
```

### `keebo.menubar(symbol, text, options)`

Puts a line beside the menu-bar icon: the symbol, then the text. Returns `false` when the symbol, the text, or the time is rejected. `analyze` cannot show one. A command may show up to 8. The icon shows the one that ends soonest, and the line leaves when its time is up.

`symbol` follows the same rule as `notify`. `text` is a string of 1–40 characters, or a function. The app calls the function with the whole seconds left, once a second, and shows what it returns (a string, the same limit). The script does not schedule that call. `options.seconds` is how long the line stays, a whole number from 1 to 86400. `options.tip` is the tooltip, up to 200 characters; omit it for none.

```js
run() {
  const clock = (left) => {
    const minutes = Math.floor(left / 60), seconds = left % 60
    return minutes + ":" + (seconds < 10 ? "0" : "") + seconds
  }
  if (!keebo.menubar("hourglass", clock, { seconds: 90, tip: "tea" })) {
    throw new Error("that timer could not be set.")
  }
  return ""
}
```

Options does not show the line. It releases it after the example runs.

### `keebo.fetch(url)`

One HTTPS GET. Returns the response body as text. Throws when the address is refused, the call fails, or this extension is not allowed to use the network. Declare [`network: true`](#network) and the writer has to allow it. `analyze` cannot fetch.

| Limit | |
|---|---|
| Calls | 4 per command |
| Scheme | `https` on port 443 |
| Address | A public host. No user or password in the URL. Loopback, `.local`, and private networks are refused. A redirect that leaves https, or lands on one of those addresses, is refused. |
| Body | At most 256 KB of text |
| Time | 4 seconds |

```js
run() {
  keebo.loading(true)
  try {
    const body = keebo.fetch("https://api.frankfurter.app/latest?from=USD&to=GBP")
    const data = JSON.parse(body)
    return String(data.rates.GBP)
  } finally {
    keebo.loading(false)
  }
}
```

## Sandbox and limits

The script can call `keebo` and ordinary JavaScript. It has no files, no clipboard, no keystrokes, and no network except `keebo.fetch`. Each extension runs on its own background queue. A command that does not finish within five seconds is dropped. The queue is still busy if the script is in a loop; that loop does not stall typing in other extensions. An `analyze` call over 250 ms for one paragraph is dropped. A command’s returned text is at most 10,000 characters.

## Phrasebooks

A phrasebook is JSON. It tells the writing model the field and the terms to prefer. It does not run code, and installing one does not ask for permission.

```json
{
  "schemaVersion": 3,
  "id": "you.payments",
  "name": "Payments",
  "version": "1.0.0",
  "author": "You",
  "description": "Card and bank payment terms.",
  "domain": "Payment systems",
  "terms": ["chargeback", "settlement", "interchange fee", "3-D Secure"]
}
```

`domain` is 1–60 characters. `terms` is 1–500 entries of up to 60 characters. For each suggestion the model is told the field and given up to 40 terms, those sharing a word with the last few sentences first. When the unfinished word has 3 letters or more and starts a word of a term, the rest of that term is offered directly: `dia` offers `gnosis`.

## Templates

A template pack is JSON. The writer types `;` and a template's trigger, then Tab (or `;;` or `,,`, if they chose one instead of `;`). A pack does not run code, and installing one does not ask for permission.

```json
{
  "schemaVersion": 2,
  "id": "you.thanks",
  "name": "Thank-you notes",
  "version": "1.0.0",
  "author": "You",
  "description": "A short thank-you note.",
  "categories": ["Thanks"],
  "templates": [
    {
      "id": "9b2f4c1e-7d3a-4e8b-a1c5-6f0e2d9b8a71",
      "trigger": "thanks",
      "title": "Thank you",
      "text": "Hi ${1:name},\n\nThank you for ${2:your help}.\n\n$0",
      "category": "Thanks",
      "blanks": { "1": { "hint": "their first name" } }
    }
  ]
}
```

Every template has an `id`: a lowercase UUID that stays the same whatever else about the template changes, since usage, remembered values and updates follow it. Make one with `uuidgen | tr '[:upper:]' '[:lower:]'`, and never reuse one.

A pack holds 1–300 templates. A `trigger` is lowercase letters, digits and hyphens, 1–40 characters, and is used once in the pack. A `title` is optional, up to 60 characters. The `text` is 1–4,000 characters. A `category` is optional; a pack has up to 40 categories, each up to 40 characters. Bump `version` on every change: a published version never changes.

In `text`, `${1:name}` is a blank that starts with the words after the colon, `${2|one,two|}` is a choice where the first is the default, and `$0` is where the caret ends. Write `\$`, `\}`, `\|`, `\,` and `\\` for those characters themselves. `blanks` describes a blank by its number: a `hint` (what it holds, which the card shows and the model reads), a `type` (`text`, `paragraph`, `choice`, `many`, `date`, `number` or `optional`), and `remember: false` for one whose words should not be offered again.

[The schema](https://littlekeebo.app/schema/template-pack.schema.json) lists every field, and anything it does not list is refused. A pull request is checked against it; the app checks the rest when it installs a pack (each blank a template describes is one its text has), so install yours from a file in the app first.

## Publishing

Packages in this repository are what the app lists from the community shelf.

1. Add your file to `extensions/` (`.js`), `phrases/` (`.json`) or `templates/` (`.json`). To change a package, edit it and bump its `version`.
2. Run `python3 scripts/build-extension-index.py` at the root of the repository. It refuses a package on the wrong shelf and writes each shelf's `index.json`.
3. Commit the file with the shelf's `index.json` and open a pull request. The check runs on it. Once it is merged, `publish` puts the shelves on the downloads host, signed, and the app installs a package only when its SHA-256 matches the index.

`extensions/wordcount.js`, `phrases/cooking.json` and `templates/thank-you.json` are samples of each kind to copy.
