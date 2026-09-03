# STARTUP.md

This is the prompt a human pastes into their agentic harness of choice
(Claude Code, OpenCode, Codex CLI, or another) the very first time they run
it in a freshly cloned `spoor-bootstrap` checkout, right after `install.sh`
finishes. `install.sh` only does mechanical OS-level bootstrap (docker, uv,
gh, the skill-symlink sanity check) — everything from here on (the
interview, generating `.env`, generating this deployment's own conventions
doc, and handing back the self-provisioning shopping list) is driven by the
agent itself, so there's no separate manual "now run the init skill" step.

---

## Paste this into your harness

```
You are running for the first time in a spoor-bootstrap checkout, right
after install.sh finished. Read AGENTS.md in this repo now, in full — it's
the source of truth for what you are and what the first-boot interview
covers. Then come back here and do the following, in order. Don't start
building any product code until all of it is done.

1. Run the first-boot interview AGENTS.md describes: my own technical
   experience level, who the end product is for (a technical or
   non-technical end-user), which work tracker I want to use, and which
   comms channel I want you reachable on. Ask one at a time, don't assume
   answers, and push back gently on a vague answer the way you would in any
   planning conversation — a one-word answer isn't enough to write a real
   .env or conventions doc from.

   If I tell you the product is for a non-technical end-user, read
   skills/product-tech-stack/SKILL.md and follow the stack it requires —
   don't decide a stack yourself.

   Also ask where the target product repo lives (existing repo or a brand
   new one to create) and, if there's a live product already, where its own
   content/docs live — you'll need both for the steps below.

2. Ask about autonomy and stop-and-ask. This repo's default posture (see
   AGENTS.md's "What you are") is: work through a devops pipeline —
   branches, PRs, deploys — largely on your own for routine reversible
   work, and stop and ask before anything destructive or hard to reverse
   (force-push, deleting branches/volumes/backups, `git reset --hard` on
   others' work, credential rotation, DNS/domain changes, touching live
   production data directly). Don't just accept that silently — ask
   explicitly whether it matches my risk tolerance, or whether I want
   anything tightened (e.g. sign-off before any merge, not just before
   destructive ops) or loosened (e.g. a specific carve-out for something
   routine to this product).

3. Ask anything else that's specific to this product and can't be guessed
   from a generic template — a domain name, product/team vocabulary,
   anything you'd want a future session of yourself to already know
   without re-explaining it.

4. Once you have the answers, write `.env` from `.env.example` (copy it if
   `.env` doesn't exist yet; if it already exists, leave it untouched and
   tell me to edit it by hand instead). Fill in every field you now have a
   real answer for: `PRODUCT_REPO_PATH`, `WORK_TRACKER`, `COMMS_CHANNEL`,
   and add clearly-named fields for anything from the interview that
   `.env.example` doesn't already have a slot for (e.g. the tech-level and
   end-user-type answers). Leave real secrets
   (`WORK_TRACKER_API_KEY`, `COMMS_CHANNEL_TOKEN`, `AGENT_EMAIL_ADDRESS`)
   blank with a comment pointing at where each one comes from — don't ask me
   to paste a secret into this chat, I'll edit `.env` directly for those
   once they're provisioned (step 6).

5. Write a conventions doc in the target product repo (that repo's own
   `CLAUDE.md`/`AGENTS.md` if it doesn't have one yet, or a clearly-named
   sibling if it does and you don't want to clobber it). It should record,
   for this specific deployment: the autonomy model and stop-and-ask list
   from step 2 (the one I actually agreed to, not a generic list), the
   git/PR conventions you'll operate under (branch, commit, push, PR,
   self-merge for routine work), and anything from step 3. This is the file
   every future session of yourself should treat as this deployment's own
   source of truth — point at it rather than re-deriving these answers from
   this conversation again.

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

7. Give me the self-provisioning shopping list from AGENTS.md (my own email
   address, a comms channel account, a GitHub account, a work-tracker
   account/integration, and anything else needed for the tools we
   discussed) so I can go create those accounts and paste the resulting
   secrets into `.env` myself. Don't try to register for any of them
   yourself. Fold in the blockers from step 6, and tell me which skill
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
