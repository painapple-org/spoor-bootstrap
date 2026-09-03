# STARTUP.md

This is the prompt a human pastes into their agentic harness of choice
(Claude Code, OpenCode, Codex CLI, or another) the very first time they run
it in a freshly cloned `spoor-bootstrap` checkout, right after `install.sh`
finishes. `install.sh` only does mechanical OS-level bootstrap (docker, uv,
gh, the skill-symlink sanity check); everything from here on — the
interview, generating `.env`, generating this deployment's own conventions
doc, and handing back the self-provisioning shopping list — is driven by the
agent itself, from this one prompt.

---

## Paste this into your harness

```
You are running for the first time in a spoor-bootstrap checkout, right
after install.sh finished. Read AGENTS.md in this repo now, in full — it's
the source of truth for what you are and what the first-boot interview
covers. Then come back here and do the following, in order. Don't start
building any product code until all of it is done.

1. Run the first-boot interview exactly as AGENTS.md's "The first-boot
   interview" section lists it — that section is the complete set of
   questions, so work from it rather than from any list here. Ask one at a
   time, don't assume answers, and push back gently on a vague answer the
   way you would in any planning conversation — a one-word answer isn't
   enough to write a real .env or conventions doc from.

2. Ask about autonomy and stop-and-ask. You've already read the default
   guardrail list in AGENTS.md's "Default guardrails" section — that list
   is in force right now and is the starting point for this conversation.
   Don't restate it back to me item by item, and don't treat it as
   provisional: walk me through what it means in practice for this product,
   then ask explicitly whether I want anything tightened (e.g. sign-off
   before any merge, not just before destructive ops) or a specific,
   named carve-out loosened for something genuinely routine here.
   Anything I don't explicitly change stays as AGENTS.md has it.

3. Ask anything else that's specific to this product and can't be guessed
   from a generic template — a domain name, product/team vocabulary,
   anything you'd want a future session of yourself to already know
   without re-explaining it.

4. Once you have the answers, write `.env` from `.env.example` (copy it if
   `.env` doesn't exist yet; if it already exists, leave it untouched and
   tell me to edit it by hand instead). Read `.env.example` for the field
   list — it's the schema and the one home for what each key means, so use
   its names exactly as they are, don't invent new ones, and don't work
   from a list of keys restated here. Fill in every field you now have a
   real answer for.

   Three things that aren't obvious from `.env.example` alone:

   - Anything from the interview that has no slot there — the autonomy
     model, product vocabulary, a domain name — goes in the conventions doc
     in step 5, not into `.env` under a name you made up.
   - Leave every secret blank, with a comment pointing at where it comes
     from. Don't ask me to paste a secret into this chat; I'll edit `.env`
     directly for those once they're provisioned (step 7).
   - Leave `CONVENTIONS_DOC_PATH` blank here: step 5 is what fills it in,
     once you've actually decided where that doc lives.

5. Write a conventions doc in the target product repo (that repo's own
   `CLAUDE.md`/`AGENTS.md` if it doesn't have one yet, or a clearly-named
   sibling if it does and you don't want to clobber it).

   **Record its path in `CONVENTIONS_DOC_PATH` in `.env` as soon as you've
   decided it, before writing the doc's content.** That variable is the one
   home for where this doc lives; every skill that says "go read the
   conventions doc" resolves it from there. Skipping this leaves those
   skills pointing at a file no future session can name — so if you can't
   write the variable, stop and tell me rather than proceeding.

   It should record, for this specific deployment:

   - the autonomy model and stop-and-ask list from step 2 — specifically,
     what I asked to *change* from AGENTS.md's default guardrails, and the
     fact that everything I didn't change still stands as written there.
     Don't copy that list in; point at AGENTS.md as its home and record the
     deltas.
   - the git/PR conventions you'll operate under (branch, commit, push, PR,
     self-merge for routine work), including this deployment's branch
     naming convention and its default branch name.
   - **the commit process trailer** — the literal trailer line that goes in
     the commit body naming which process produced the commit, per step 2
     of skills/git-pr-conventions/SKILL.md. Ask me if we haven't agreed
     one; that skill points here for the exact text.
   - **the tracker comment marker convention** — the literal footer line
     ending every work-item comment you write, so a later run can tell your
     own prior notes from a human's, per the tracker-agnostic contract in
     skills/work-tracker/SKILL.md.
   - **what you're allowed to do unattended versus what needs my sign-off**
     on the running deployment specifically — e.g. restarting an unhealthy
     container, clearing disk of your own artifacts, rolling back a bad
     deploy — per the monitoring section of
     skills/deploy-and-monitor/SKILL.md. Be concrete about the boundary;
     a vague "fix what breaks" is what leaves a future session guessing.
   - anything from step 3.

   This is the file every future session of yourself should treat as this
   deployment's own source of truth for all of the above — point at it
   rather than re-deriving these answers from this conversation again.

   **Ship it the same way you'll ship everything else**: branch off the
   product repo's default branch, commit, push, open a PR, and merge it
   yourself, per skills/git-pr-conventions/SKILL.md. Don't commit straight
   to the default branch — this is the first change that establishes the
   convention, so it shouldn't be the one exception to it. Show me the PR
   link.

6. Now specialize the skill stubs. Read skills/specialize-skills/SKILL.md
   and follow it. The skills under skills/ ship deliberately generic, with
   an explicit `TODO(specialize)` marker everywhere a real answer depends
   on my tracker, my comms channel, my host or my product — the answers you
   just collected in steps 1-5 are exactly what those markers are waiting
   for. Work through every stub that SKILL lists, in the order it gives.

   Two things I care about here: don't invent a specific to make a file look
   finished (a marker that still says "unknown" is better than a confident
   wrong value), and don't leave a marker unanswered that you could have
   answered by just running a command and checking. Where something is
   genuinely blocked on an account I haven't created yet, leave the marker,
   name the blocker in one line, and carry it into step 7.

7. Give me the self-provisioning shopping list exactly as AGENTS.md's
   "Self-provisioning: the shopping list" section defines it — that section
   owns what's on it and why, so don't work from a list restated here — so
   I can go create those accounts and paste the resulting secrets into
   `.env` myself. Don't try to register for any of them yourself, per that
   same section. Fold in the blockers from step 6, and tell me which skill
   stubs are still incomplete because of them — I'd rather know that now
   than find out when a stage silently does the wrong thing.
```

---

That's the whole first-boot flow: read `AGENTS.md`, interview, defer to the
stack SKILL if relevant, agree on an autonomy model, write `.env`, generate
the conventions doc, specialize the skill stubs, hand back a provisioning
list. Everything after that — actually wiring up the chosen work tracker and
comms channel, writing product code, setting up scheduling — is follow-on
work once the human has provisioned what's on that list and pasted the
resulting secrets into `.env`. Step 6 is expected to be re-run, scoped to a
single file, each time one of those provisioning blockers clears and a
`TODO(specialize)` marker becomes answerable.
