# Security policy

To report a security problem in this repository, or in Little Keebo or the Dream Forces services it belongs to, email **support@dreamforces.com** with "Security" in the subject.

Please do not open a public issue or pull request for it. A few lines are enough: what you found, where, and how to see it. If it involves someone's personal data, describe it rather than attaching it.

## What to expect

- A reply from a person within five working days, saying we have it.
- A decision on whether it is a problem, and what we will do about it, as soon as we know. We will tell you when it is fixed.
- Credit in the fix's notes if you want it, and your name left out if you don't.
- No legal action from us over research that follows the rules below.

## The rules

- Test with your own licence or trial, on your own Mac. Do not look at, change or keep anyone else's data. If you come across some, stop and tell us.
- No load or denial-of-service tests, no scanning of the services at volume, and no social engineering of people who work for us or buy from us.
- Give us time to fix it before you tell anyone else. We would like to agree a date with you; 90 days is the usual.

## What this covers

This repository is Little Keebo's community library: extensions, phrasebooks and template packs, and the workflow that publishes them to downloads.littlekeebo.app. A way for an extension to read files or keys outside its sandbox, to use the network without the writer allowing it, or to get a package past the index's signature check would be a security problem, and so would a way to publish without a merge to `main`. The Mac app, the website, the licensing service and the model downloads are covered by the same address and the same words.

The same words are at https://littlekeebo.app/security/, and the machine-readable version is https://littlekeebo.app/.well-known/security.txt.
