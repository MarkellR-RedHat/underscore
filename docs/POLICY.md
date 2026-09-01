# Using Underscore music in company videos

This note answers the questions that come up when someone wants to use music from this pipeline in videos published by their employer. It describes how the project is designed and why. It is not legal advice, and company policies differ. Read yours.

## Summary

Music made with Underscore on your own time and equipment belongs to you. The pipeline dedicates it to the public domain under CC0. A company that uses it receives public domain audio: no license to negotiate, no fee, no attribution requirement, and no contract with an employee. That is the same footing as any other public domain material, and it is the reason the model works.

## Who owns the music

Ownership follows the usual rules for creative work.

- Made on your own time, on your own computer, with your own accounts: it is yours.
- Made during work hours, on a company laptop, or with company accounts: treat it as the company's. Most employment agreements say so. You can still use it in company videos; you cannot build a personal catalog out of it.

If you want to own the catalog, keep the two worlds apart. Compose and render at home. Do not use a company subscription for the composing step. Keep the manifests, which record when and how each track was made.

## Why the output is CC0

Two reasons.

First, it removes every question a reviewer might ask. Public domain audio needs no license review, no attribution tracking, and no renewal. An editor can use it in five minutes.

Second, it settles the authorship question before anyone raises it. The code behind each track is written by a language model from a human brief, then rendered, selected, and mastered by the pipeline. Copyright offices have not settled how much protection machine-assisted works receive. Dedicating the output to the public domain means the answer does not matter to anyone who uses the music. The maker gives up nothing they were counting on, because the value of the catalog is in having it, not in restricting it.

The code of the pipeline itself is MIT licensed. That is a separate matter from the music.

## What a company receives

When a company video uses a track from a CC0 catalog, the company receives audio it may use in any way, for any purpose, forever. It does not receive an obligation. There is no vendor, no invoice, and no relationship to disclose in the way a paid arrangement would require.

Some companies keep a list of approved music sources. The right move is to have the catalog added to that list, with a link to the license and to the source files. Telling your manager where the music in your videos comes from is a good habit whether or not the policy requires it.

## Data handling

The composing step can send text to a cloud model. Everything else runs on your machine.

| Mode | What leaves the machine |
|---|---|
| Brief mode | The brief you wrote: durations, moods, tempo. |
| Video mode with a cloud model | The brief, the transcript text, and the scene cut times. |
| Video mode with `--offline-brief`, or with Ollama | Nothing. |

Audio, video frames, and finished tracks never leave the machine in any mode.

If the footage is unreleased or confidential, do not run its transcript through an external model. Use `--offline-brief`, or run the composing step with a local model through Ollama. The music will be slightly less tailored to the words and exactly as usable.

## Practical rules

1. Compose and render on personal hardware if you intend to own the result.
2. Release the catalog under CC0 and keep the license file with every bundle.
3. Keep manifests. They are the record of what was made, when, from which brief, with which seed.
4. Do not put company names, product names, or project codenames in track titles or briefs.
5. Do not send transcripts of unreleased material to cloud services.
6. Tell your manager the music is yours and public domain, and offer to add the catalog to any approved list.

## What this does not cover

This note is about music produced by this pipeline. It does not cover music you did not make, samples with their own licenses, or recordings of other people. Sonic Pi's bundled samples carry their own permissive terms; check the license file in the Sonic Pi installation if you rely on them, or compose with synths only.
