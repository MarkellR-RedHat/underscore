# INTERNAL PLANNING NOTE

**Delete this file before this repository is made public.** It describes the
whole system and the plan around it. Each public repository stands on its own
and should describe only itself.

## Portfolio cut, September 1, 2026

The family is five tools: **Touchstone, Galley, Underscore, Backdrop, Rot.**

- Inbox folds into Galley as an input: `galley topics <notes dir>` emits briefs. Not a repository.
- Caption folds into Backdrop as its first stage: a timed, glossary-corrected transcript. SRT, chapters, and the description draft are exports of Backdrop, not a product.
- Localize is dropped. If a second language is ever needed, it is a Galley output mode.
- Walkthrough is deferred: the spec is kept, nothing is built, and it stays off the site until it has a first real use (the Touchstone UI, 2027).
- The loop is **Galley -> Backdrop (+ Underscore) -> Rot -> back into Galley.** Rot's failures and people's questions both enter Galley as briefs.
- Build order: finish Galley, then Backdrop, then Rot.
- The inbox, caption, walkthrough, and localize repositories stay private as specs until Markell says archive or delete. Anything worth keeping from their READMEs was lifted into Galley and Backdrop first.

## The five

| Tool | Role in the loop | Status |
|---|---|---|
| Touchstone | Version verdicts for inference engines. The origin of the measured-verdict philosophy the others borrow. | built, launching 2027 |
| Galley | Topic paragraph and reference folder in; sourced post, diagrams, and derivatives out, with citation, style, and brand gates. Takes topics from a notes directory (the former Inbox) and can emit a second language as an output mode (the former Localize). Stage (talks) is an output mode too. | in progress |
| Underscore | Measured, public domain music beds for video. | built, catalog rendering |
| Backdrop | Stage one is the timed, glossary-corrected transcript (the former Caption), exported as SRT, chapters, and a description draft. Then relevant animated clips from the words, sharing archetype geometry with Galley. | planned, next after Galley |
| Rot | Runs the code in published material on a schedule and reports drift. Radar, its module, watches upstream releases. Failures return to Galley as briefs. | planned, after Backdrop |

## Shared principles

Local execution. The user's own accounts for any language model step (a
command line tool they already run, an API key, or a local model), always
replaceable and optional where the design allows. Deterministic output from
the same input and seed. Gates at the end of every run. Reproducibility
recorded in a manifest. Permissive licenses: MIT for code, CC0 for generated
media where that applies.

Once three tools exist, extract the shared core (brief schema, brand profiles,
gate framework, model seam, review page) into one library. Not before.

## Rules for every repository in the set

- Every commit is authored and committed as MarkellRawls <markell.rawls@yahoo.com>. No co-author trailers of any kind.
- No tool, model, or vendor names in commit messages.
- No em dashes in documentation.
- Nothing from any employer: no names, logos, internal data, or unreleased material. Brand profiles come from published guidelines only.
- Personal time, personal hardware, personal accounts.
