// keebo {"id":"example.wordcount","name":"Word Count","version":"1.0.0","author":"Little Keebo","description":"Type /wc, then Tab, for the number of words in the line. /wc sentences counts sentences.","icon":"text.alignleft","tags":["commands"],"capabilities":["1 command"]}
//
// A sample extension: one command. Copy it, change the id, name and command, and see EXTENSIONS.md.

keebo.define({
  id: "example.wordcount",
  name: "Word Count",
  version: "1.0.0",
  author: "Little Keebo",
  description: "Type /wc, then Tab, for the number of words in the line. /wc sentences counts sentences.",
  icon: "text.alignleft",
  commands: {
    wc: {
      title: "Word count",
      usage: "[sentences]",
      examples: ["", "sentences"],
      run(ctx) {
        if (ctx.args === "sentences") return keebo.sentences(ctx.text).length + " sentences";
        return keebo.words(ctx.text).length + " words";
      }
    }
  }
})
