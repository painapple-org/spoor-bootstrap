# STARTUP.md

This is the prompt a human pastes into their agentic harness of choice
(Claude Code, OpenCode, Codex CLI, or another) the very first time they run
it in a freshly cloned `spoor-bootstrap` checkout, right after `install.sh`
finishes. `install.sh` only does mechanical OS-level bootstrap (docker, uv,
the `gh` binary, the skill-symlink sanity check); everything from here on —
the interview, generating `.env`, authenticating `gh`, generating this
deployment's own conventions doc, and handing back the self-provisioning
shopping list — is driven by the agent itself, from this one prompt.

Note what that means for `gh`: `install.sh` deliberately installs the
binary without logging it in, so the first-boot flow below is where a
working git identity actually gets established — step 5, before anything
in this flow tries to push.

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

   Four things that aren't obvious from `.env.example` alone:

   - Anything from the interview that has no slot there — the autonomy
     model, product vocabulary, a domain name — goes in the conventions doc
     in step 6, not into `.env` under a name you made up.
   - Leave every secret blank, with a comment pointing at where it comes
     from. Don't ask me to paste a secret into this chat; I'll edit `.env`
     directly for those once they're provisioned (step 8).
   - `chmod 600 .env` right after creating it, and tell me you did. A copy
     inherits `.env.example`'s mode, which is world-readable because it
     holds nothing but field names — while `.env` ends up holding this
     deployment's tracker token and comms-channel token. Every other local
     account and service on the box can read a world-readable file, and
     gitignoring it does nothing about that. Do this at creation rather
     than at step 8 when the secrets actually land: a file that starts out
     0600 is never briefly wrong, and there is no second moment to
     remember.
   - Leave `CONVENTIONS_DOC_PATH` blank here: step 6 is what fills it in,
     once you've actually decided where that doc lives.

5. Establish a working git identity, and prove it works, before you try to
   push anything. Everything from step 6 on ships through a branch and a
   PR, so this is the step that makes that possible — don't discover it's
   missing halfway through your first push.

   `install.sh` installed the `gh` binary and nothing more: it never
   authenticated it. Do that now, with me sitting here — right now is the
   only moment in this deployment's life when an interactive login is
   available at all, since every later run is scheduled or unattended with
   no terminal to prompt on.

   a. Run `gh auth status`. If it already reports an authenticated
      account, tell me which account and what scopes, and move on to (c).

   b. If it doesn't, walk me through `gh auth login` here in the chat —
      tell me which prompts to expect and which answers you need (github.com
      vs. an enterprise host, HTTPS vs. SSH, browser vs. pasting a token),
      then have me run it and re-check `gh auth status` yourself. If I'd
      rather use a credential this box already has (an SSH key already
      loaded, an existing credential helper), that's fine too for the
      *push* — verify *that* instead of insisting on a particular
      mechanism. What matters is that something works.

      Opening and merging the PR is a separate credential from pushing,
      though: that goes through the hosting provider's API, so `gh` (or
      whatever you'll call the API with) needs a token of its own even if
      the push itself rides an SSH key. Check both, not just the one that
      happens to work first.

      Do not create a GitHub account for me, and don't try to register one
      for yourself — that's mine to do, per AGENTS.md's self-provisioning
      section.

   c. **Whose account this is, is not a blocker here.** My own GitHub
      account is a perfectly good answer for now. A GitHub account that is
      *yours*, separate from mine, is on the step-8 shopping list because
      it's the better end state and AGENTS.md's self-provisioning section
      says why — but it is an upgrade to a git identity that already works,
      not a prerequisite for your first PR. When I do provision it, swapping
      it in is a *later*, deliberate re-run of step 7 scoped to that one
      section, nothing more — not something step 7's first pass touches,
      which is why that step tells you to leave the section alone today.

   d. Authenticating to GitHub is not the same as being able to write to
      *my* repo, so verify the thing you actually need: from the product
      repo at `PRODUCT_REPO_PATH`, run a `git push --dry-run` of a
      throwaway branch name against its remote. That contacts the remote
      and gets refused if the account lacks write access, while writing
      nothing.

      **Check first that there is somewhere to run it from.**
      `.env.example` defines `PRODUCT_REPO_PATH` as a path *or a clone
      target*, so on a first boot it often isn't a directory on this box
      yet — and the command above needs a working tree. If it isn't one,
      make it one before running the check: clone the remote to that path
      for an existing repo, or for a brand-new one (a valid answer to the
      interview's repo question) create the repo on my hosting account,
      then clone it to that path.

      Either way the repo has to end up with a remote you can reach — a
      local `git init` with no remote will fail this check rather than pass
      it — and it has to exist at all, since step 6 has nowhere to land
      otherwise. If you can't get there, say so rather than skipping the
      check. Creating the *repo* on my hosting account is fine to do for me
      if I ask you to and you have the access — it's creating an *account*
      that's mine alone, per (b).

      **Then do the same for this bootstrap checkout's own `origin`**, not
      just the product repo. Steps 6 and 7 both ship PRs *here*, so this
      repo's remote is as load-bearing as the product repo's, and it is a
      different repo with its own permissions — write access to one implies
      nothing about the other. Same `git push --dry-run` of a throwaway
      branch name, run from this checkout. Check the PR-opening credential
      against this repo too, per (b).

      Note what `install.sh` did and didn't establish here, so you don't
      mistake it for this check: it compared `origin`'s URL against
      upstream's and refused only on a literal match, and if it couldn't
      read an `origin` at all it logged NOT VERIFIED and continued. It
      never contacted the remote and never tested write access. This is
      the first time anything does.

      If the dry-run against this checkout's `origin` fails, or `origin`
      is missing or still upstream's URL, stop and tell me, and see (f):
      the fix is a remote I own, and README.md's "Path to a running
      instance" owns the choice between the three shapes that remote can
      take: a private repo I create, a public fork, or a plain git remote
      with no PR mechanism at all.
      **If `origin` is a public GitHub fork, say so explicitly now, before
      step 6 commits anything** — steps 6 and 7 write real operational
      detail about my deployment into tracked files here (see step 7), a
      fork of a public repo can never be made private, and this is the
      last moment before that becomes permanently public. Determine that
      rather than assuming it: `gh repo view --json isFork,visibility`
      against this checkout's `origin` answers both halves in one call
      (or the equivalent API read on another host). `install.sh`'s URL
      comparison cannot — a private repo I created and a public fork both
      pass it identically.

   e. Write down what actually worked in the `Auth` section of
      skills/git-pr-conventions/SKILL.md: the exact push invocation that
      succeeded, which account it authenticates as, any protocol quirk you
      hit, what you found when you checked the PR-opening credential in
      (b) — including "it turned out to be the same one", which is a
      finding about this deployment and not a general guarantee — and
      **whether this remote has a PR-opening mechanism at all.**

      That last one is a real question here, not a formality. A plain git
      remote — a bare repo on a box, a self-hosted host whose API nobody
      has turned on — has no PR object at all, and step 6 hard-requires
      opening one. Check it rather than inferring it from the push
      working: the push and the API are different paths, which is the same
      reason (b) makes you check two credentials. If it turns out there is
      no PR mechanism on this remote, bring me the substitute before step
      6 and record *that* — the `Auth` section's own guidance says what a
      substitute has to preserve, including how the default branch gets
      advanced without the local fast-forward that's hazardous here.

      That section is the one home for all of it, and step 7 has
      nothing left to add to it — it's answered here because here is where
      it gets verified for real. Follow skills/specialize-skills/SKILL.md's
      "How to specialize one file" rules for how to write it, including
      deleting the `TODO(specialize)` marker — once *every* bullet under it
      is answered, not once the first few are.

      This is an edit to a tracked file in *this* repo, so it doesn't get
      to stay in your working tree. Step 6 ships it, and says why it ships
      there rather than here.

   f. If none of this can be made to work — no account you're willing to
      use, no network, a repo neither of us can push to, or no PR
      mechanism on this remote at all — **stop and tell me, and don't
      route around it.** Don't commit straight to the default branch
      instead. Write step 6's doc, leave it uncommitted, tell me plainly
      that the first PR is blocked on git auth and nothing else, and pick
      step 6 back up the moment it's fixed.

      The no-PR-mechanism case is the one on that list that behaves
      differently: it doesn't block the push, only step 6's PR. It's still
      not a licence to commit to the default branch — tell me what you'd
      use instead, per (e), and get my agreement before step 6 rather than
      picking a substitute on your own.

6. Write a conventions doc in the target product repo (that repo's own
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
   - **the product's stack, but only if `END_USER_TYPE` is technical.** For
     a non-technical end-user, skills/product-tech-stack/SKILL.md is the one
     home for the stack and nothing gets copied out of it. For a technical
     one that SKILL doesn't apply and the choice is yours on the merits —
     which leaves the decision with no home at all unless it's recorded
     here. Record what you chose and the reason, not just the list.
   - **any conflict between that SKILL's stack and a product repo that
     already exists in a different one.** That SKILL's "When the product
     repo already exists and doesn't match" section is the home for how the
     conflict resolves; this doc is the home for *this* deployment's
     instance of it — which pieces already match, which don't, and the
     reading we agreed. Ask me before writing it down; don't record an
     agreement I didn't make.
   - **what you're allowed to do unattended versus what needs my sign-off**
     on the running deployment specifically — e.g. restarting an unhealthy
     container, clearing disk of your own artifacts, rolling back a bad
     deploy — per the monitoring section of
     skills/deploy-and-monitor/SKILL.md. Be concrete about the boundary;
     a vague "fix what breaks" is what leaves a future session guessing.
   - **where the business's own content and docs live**, from the second
     half of the interview's repo question — a wiki, a drive folder, a docs
     directory in the product repo, a CMS. That answer has no `.env` slot
     and no other destination, so this doc is its home; without it recorded
     here it gets collected and silently dropped, and a later ideation or
     refinement pass has nothing non-generic to ground a proposal in.
     Record it even when the answer is "nothing written down anywhere" —
     that's a real answer and worth knowing.
   - **every repo the product spans, if it's more than one**, and which of
     them `PRODUCT_REPO_PATH` names. That variable is singular — see its own
     comment in `.env.example` for why that's a limitation with a documented
     fallback rather than an assumption — so it can only ever point at the
     primary one. If my product is split across repos, list them here with
     one line each on what lives where, and say plainly that a skill saying
     "the product repo" means the primary one unless it names another.
     Nothing else can record this, and a future session that only reads
     `.env` will otherwise believe there is exactly one.
   - anything from step 3.

   This is the file every future session of yourself should treat as this
   deployment's own source of truth for all of the above — point at it
   rather than re-deriving these answers from this conversation again.

   **Ship it the same way you'll ship everything else**: branch off the
   product repo's default branch, commit, push, open a PR, and merge it
   yourself — or run the agreed substitute from step 5(e), if this remote
   has no PR mechanism — per skills/git-pr-conventions/SKILL.md, using the
   identity and the invocation you verified and wrote down in step 5. Don't
   commit straight to the default branch — this is the first change that
   establishes the convention, so it shouldn't be the one exception to it.
   Show me the PR link (or, on the substitute, whatever it produces in its
   place).

   **Then ship step 5(e)'s edit too — same loop, different repo.** That
   auth answer went into a tracked file in this bootstrap checkout, whose
   `origin` you verified you can push to and open a PR against in step
   5(d) — that verification, not `install.sh`, is what makes this possible.
   (`install.sh` only refuses an `origin` whose URL is literally upstream's;
   it never tested write access.) Branch off this repo's default branch,
   commit, push to `origin`, open a PR, merge it yourself — or run the
   agreed substitute from step 5(e), if this remote has no PR mechanism. Two
   shipped changes by the end of this step, then: one in the product repo
   for the doc above, one here for the auth answer.

   **Name the target repo explicitly on every PR and merge command you run
   against this checkout.** `gh` resolves a clone's base repo to its
   network parent, so from a fork of this template `gh pr create` defaults
   to opening the PR against `painapple-org/spoor-bootstrap` — someone
   else's public repo, which you cannot merge and which would publish this
   deployment's specifics into a public PR. Pass `--repo <my-owner>/<my-repo>`
   (and `--head <my-owner>:<branch>` where the command takes one) on every
   `gh pr create`/`gh pr merge` here, and check the URL the command printed
   names my repo before you merge. This is the same class of mistake
   skills/git-pr-conventions/SKILL.md's "Which repo are you even in?"
   warns about for scratch clones; that section is its home.

   It happens in this step rather than back in step 5 for one reason: every
   commit carries the process trailer, and the trailer's literal text is
   agreed right here. Step 5 is where the auth answer gets verified and
   written down; this is the earliest point it can be *committed* without
   inventing a trailer neither of us agreed to.

7. Now specialize the skill stubs. Read skills/specialize-skills/SKILL.md
   and follow it. The skills under skills/ ship deliberately generic, with
   an explicit `TODO(specialize)` marker everywhere a real answer depends
   on my tracker, my comms channel, my host or my product — the answers you
   just collected in steps 1-6 are exactly what those markers are waiting
   for. Work through every stub that SKILL lists, in the order it gives.

   One marker is already gone by the time you get here: the `Auth` section
   of skills/git-pr-conventions/SKILL.md, which step 5 answered against a
   real push. Don't re-open it in this pass. If it somehow still carries a
   marker, that means step 5's verification never happened — go back and do
   it rather than filling it in from what you assume worked. A later,
   deliberate scoped re-run *is* how that section changes, per 5(c): when I
   provision a GitHub account of your own, verify a real push as that
   account and rewrite the section from what actually worked.

   One part of this pass is writing rather than filling in a blank, so
   don't let it disappear into the marker list: specializing
   skills/work-pipeline means deciding which pipeline stages this
   deployment actually runs, and then writing one prompt file per stage
   kept — that's the biggest deliverable of the whole pass: one substantial
   file for every stage in the set we agree on, reactive and proactive
   alike, rather than a line each. They live in prompts/ in this repo; read
   prompts/README.md for where they go, how they're named and what each one
   has to contain, and start each from
   prompts/STAGE_TEMPLATE.md. Tell me which stages you're proposing before
   you write them. If you can't finish them all today, that's fine — say
   which ones are still to write and carry them into step 8 as outstanding
   work, rather than leaving an empty file or a stub prompt a scheduled run
   could pick up and act on.

   Two things I care about here: don't invent a specific to make a file look
   finished (a marker that still says "unknown" is better than a confident
   wrong value), and don't leave a marker unanswered that you could have
   answered by just running a command and checking. Where something is
   genuinely blocked on an account I haven't created yet, leave the marker,
   name the blocker in one line, and carry it into step 8.

   **Before you commit any of it, tell me what it contains.** A specialized
   pass writes real operational detail about my business into tracked files
   here: which identities on my comms channel may instruct you, which
   account your pushes authenticate as and at what permission level, my
   tracker's scope identifier and host specifics, which of my branches must
   never be force-pushed. None of it is a credential — those stay in `.env`,
   which is gitignored — but all of it is identifying detail about a
   specific deployment, and where it lands is decided by whatever `origin`
   is. Summarize in a couple of lines what this pass is about to commit and
   which repo it goes to, and if that repo is a public fork say so plainly
   and get my go-ahead first, per step 5(d) — which is also where the check
   for that lives (`gh repo view --json isFork,visibility` against this
   checkout's `origin`). Read the answer off that rather than inferring it
   from what `origin`'s URL looks like.

   **Then ship the pass.** Everything you just rewrote is a tracked file in
   this bootstrap repo, and specialization that exists only in one
   uncommitted working tree has no revert point, no reviewable diff and no
   backup — which is the whole reason step 6 went through a PR instead of
   committing to the default branch. So: branch off this repo's default
   branch, commit, push to `origin`, open a PR, merge it yourself — or run
   the agreed substitute from step 5(e), if this remote has no PR mechanism —
   per skills/git-pr-conventions/SKILL.md, exactly as in step 6, including
   naming the target repo explicitly on the PR and merge commands, for the
   reason step 6 gives.

   One PR for the whole pass, not one per skill file — one substitute for
   the whole pass, likewise, on a remote that has no PRs. The scoped
   one-file re-run this step is built for — when a step-8 provisioning
   blocker clears and a marker becomes answerable — gets its own PR (or its
   own substitute) at that point, and that's what keeps each of those
   independently revertable. Splitting today's single pass into one PR per
   stub buys nothing: every file in it was written from the same interview
   answers, in one sitting, with nothing between them worth bisecting.

   One thing to notice while you're here: you're editing the primary
   checkout, and that's only acceptable because I'm sitting next to you.
   Those later re-runs are unattended, and
   skills/git-pr-conventions/SKILL.md's "Which repo are you even in?"
   section is the one home for how they have to be done instead.

8. Give me the self-provisioning shopping list exactly as AGENTS.md's
   "Self-provisioning: the shopping list" section defines it — that section
   owns what's on it and why, so don't work from a list restated here — so
   I can go create those accounts and paste the resulting secrets into
   `.env` myself. Don't try to register for any of them yourself, per that
   same section. Fold in the blockers from step 7, and tell me which skill
   stubs are still incomplete because of them — I'd rather know that now
   than find out when a stage silently does the wrong thing.

   That section splits the list into more than accounts, so use all of its
   categories rather than handing me only the signup list. Anything I left
   genuinely undecided in this conversation — a tracker I haven't picked, a
   proactive stage I wasn't sure I wanted, whether an existing codebase
   ever gets migrated — goes on it as an open decision with what it blocks,
   not quietly resolved by you and not dropped. Same for work you found and
   couldn't finish. If it turns out I don't have a git hosting account at
   all, say so plainly as the item everything else is waiting on rather
   than phrasing it as an upgrade to something I already have.
```

---

That's the whole first-boot flow: read `AGENTS.md`, interview, defer to the
stack SKILL if relevant, agree on an autonomy model, write `.env`, get a git
identity that actually pushes to both repos, ship the conventions doc and the
auth answer through real PRs, specialize the skill stubs and ship those
through one more, hand back a provisioning list. Three shipped changes, in
two repos: the product repo gets the conventions doc, this one gets the
edits first boot makes to itself. Three *PRs*, on a remote that has them —
on one that doesn't, each is the substitute agreed in step 5(e) instead,
which is why that step settles the question before step 6 ships anything.

The ordering is deliberate: nothing in it depends on something a later step
promises to deliver, which is why git auth sits ahead of the first push
rather than inside the specialization pass, and why nothing is committed
before the step that agrees the commit trailer every commit carries.

Everything after that — actually wiring up the chosen work tracker and comms
channel, writing product code, setting up scheduling — is follow-on work
once the human has provisioned what's on that list and pasted the resulting
secrets into `.env`. Step 7 is expected to be re-run, scoped to a single
file, each time one of those provisioning blockers clears and a
`TODO(specialize)` marker becomes answerable; each of those re-runs ships as
its own PR, from a scratch clone rather than the primary checkout, since by
then nobody is sitting there watching.
