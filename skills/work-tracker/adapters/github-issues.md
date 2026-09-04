# Adapter: GitHub Issues

Reference notes only — see [`README.md`](./README.md) for how these are
meant to be used, and [`../SKILL.md`](../SKILL.md) for the contract, the
state machine and the label vocabulary these map onto.

## The one structural mismatch: there is no state machine

A GitHub issue has exactly two native states, `open` and `closed`, plus a
`state_reason` on the closed one. That's it. There is no status column, no
workflow, nothing that enforces "an issue is in exactly one state".

So the contract's five states have to be **modeled as labels**, with the two
terminal states folded onto `closed`:

- the four live states → one label each, from a single prefixed family
  (a `state:`-style prefix makes them sortable in the label list and
  greppable in a query, and makes "which of these is the state label"
  answerable without a hardcoded list)
- done vs cancelled → `closed`, distinguished by `state_reason`
  (`completed` vs `not_planned`), which `gh issue close --reason` sets

Consequences to design around, because nothing in GitHub will stop them:

- **Two state labels can coexist on one issue.** No constraint prevents it.
  Always remove the outgoing label in the *same* `gh issue edit` call that
  adds the incoming one, and treat "this issue has two state labels" as a
  loud error worth reporting, not something to resolve by picking one.
- **A live issue with no state label at all** is the other half of that:
  anything created through the GitHub web UI by a human won't have one. Your
  unrefined-inbox query should be "open, and has no state label", not "open
  and has the inbox label", or human-filed work is invisible.

  **That query is a trap on a repo whose issues predate this deployment**,
  which is the ordinary case when the agent is being retrofitted onto a
  team's existing tracker rather than starting one. Every open issue they
  already had lacks a state label, so on the first run all of it — a
  fourteen-month-old bug nobody triaged, a design discussion, work a human
  is actively mid-way through — reads as fresh inbox. The
  assigned-to-a-human-is-inert rule catches some of it and not the
  unassigned remainder. Count them before the first run (`gh issue list
  --state open --limit 100 | wc -l`) and settle it with the owner rather
  than discovering it as a wave of refinement comments on their backlog.
  Two workable answers: backfill a state label onto the existing open
  issues once, deliberately, so "no state label" means what it says from
  then on; or scope the inbox query to issues created after a cutoff date
  (`--search 'is:open is:issue created:>=YYYY-MM-DD'`), which needs nothing
  from them but permanently hides pre-existing work from the pipeline.
  Whichever it is, record it in `SKILL.md` as part of the state mapping —
  it changes what the inbox query *means* here.
- **`gh` refuses to add a label that doesn't exist in the repo.** Create the
  whole family once during specialization with `gh label create`, and record
  in `SKILL.md` that they're repo-scoped — a second product repo needs them
  created again.

## Access and identity

`gh` is already installed by `install.sh`, so the CLI is the default access
mechanism and there's no client to write. `gh api` covers anything the CLI
doesn't expose, using the same credential.

The contract requires the agent to act as its own account. Two shapes work:

- **A separate GitHub user account for the agent**, given access to the
  repo. Simplest; `@me` then resolves to the agent in `gh` invocations, and
  `--assignee <agent-login>` is meaningful.
- **A GitHub App / its installation token.** Better isolation and scoping,
  but note that App-authored issues and comments show as a bot actor, and
  **bots cannot be assignees on a repository issue** in the ordinary sense —
  which breaks the contract's assignee-based ownership signal. If the owner
  wants an App, verify assignability in GitHub's own docs before committing
  to it, and fall back to an ownership label if it doesn't hold.

Scope identifier is `OWNER/REPO`. Pass `--repo` explicitly on every
invocation rather than relying on the cwd's git remote: unattended runs and
worktrees don't reliably have the cwd you expect.

## The seven operations

### 1. Query by state + owner

```
gh issue list --repo OWNER/REPO --state open \
  --assignee <agent-login> --label <state-label> --label <refined-label> \
  --json number,title,url,labels,assignees,updatedAt --limit 100
```

`--label` repeated is an **AND**, and there is no `--not-label`. For
anything needing negation ("open, assigned to me, *without* the refined
label") drop to `--search` and GitHub's issue search syntax, which does
support `-label:`:

```
gh issue list --repo OWNER/REPO \
  --search 'is:open assignee:<agent-login> -label:<refined-label>' \
  --json number,title,url,labels
```

Two things about `--search`: it goes through GitHub's search index, so it
can lag a write by seconds (don't use it to verify a change you just made —
read the issue back directly), and search has its own separate, much lower
rate limit than the REST API.

`--limit` defaults to 30. Any "list all of state X" query needs it raised
explicitly or it silently truncates.

### 2. Read one item in full

```
gh issue view <number> --repo OWNER/REPO \
  --json number,title,body,labels,assignees,state,stateReason,comments
```

The `comments` JSON field gives the full comment history with authors, which
is what the contract needs. (`--comments` without `--json` renders them for
human reading instead.)

### 3. Claim

```
gh issue edit <number> --repo OWNER/REPO \
  --add-assignee <agent-login> \
  --add-label <in-progress-label> --remove-label <ready-label>
```

One `gh` call, so the label swap and the assignment land together — but
**this is not atomic against a concurrent run**, and GitHub offers nothing
that is. Mitigate by reading the issue back immediately after the edit and
yielding the item if the assignee set isn't what you expected.

Note that GitHub assignees are a **set**, not a single field. "Assigned to a
human" and "assigned to the agent" are therefore not mutually exclusive, so
the contract's "an item assigned to a human is inert" rule needs a decided
reading here — recommended: any non-agent assignee makes it inert,
regardless of whether the agent is also on it.

### 4. Comment

```
gh issue comment <number> --repo OWNER/REPO --body-file -
```

Pipe the body on stdin. Passing prose through `--body` on a shell command
line invites quoting and interpolation bugs; `--body-file -` doesn't.
Markdown renders natively.

### 5. Transition state

The label swap in operation 3, generalized. For the terminal states:

```
gh issue close <number> --repo OWNER/REPO --reason completed
gh issue close <number> --repo OWNER/REPO --reason "not planned"
```

Remove the live state label in the same pass as closing, so a reopened
issue doesn't come back wearing a stale one.

### 6. Create

```
gh issue create --repo OWNER/REPO --title "..." --body-file - \
  --assignee <login> --label <state-label>
```

### 7. Labels

`--add-label` / `--remove-label` are genuine **diff** operations, so the
contract's warning about APIs that replace the whole label set does **not**
apply to the CLI path. It very much does apply if you reach for REST
directly: `PATCH /repos/{owner}/{repo}/issues/{number}` with a `labels`
array **replaces** the full set. Prefer the CLI, or the dedicated
`.../labels` sub-resource endpoints, over a `PATCH` with `labels`.

## Parent / child links

Not one of the contract's seven operations, but every stage that splits work
into sub-items needs it — and **sub-issues are a separate API, invisible to
`gh issue view`**. Nothing in the default issue payload mentions them, so a
stage that doesn't ask concludes an issue has no children.

The endpoints take an explicit API version header, and `gh api` will not
add one for you:

```sh
gh api repos/OWNER/REPO/issues/<parent-number>/sub_issues \
  -H 'X-GitHub-Api-Version: 2026-03-10'

gh api repos/OWNER/REPO/issues/<child-number>/parent \
  -H 'X-GitHub-Api-Version: 2026-03-10'
```

Adding one has the gotcha worth carrying: the path segment is an issue
**number**, but the `sub_issue_id` in the payload is the child's internal
**id**, a different and much larger integer. Read it off the child first:

```sh
sub_id=$(gh api repos/OWNER/REPO/issues/<child-number> --jq '.id')

gh api --method POST repos/OWNER/REPO/issues/<parent-number>/sub_issues \
  -H 'X-GitHub-Api-Version: 2026-03-10' \
  -F sub_issue_id="$sub_id"
```

`-F` sends it as a number; `-f` would send the string `"12345"` and get a
422. Passing the child's issue number instead of its id is the same class of
failure, except it can *succeed* by linking whichever unrelated issue holds
that id — check the response's `number` against the child you meant.

Removal is the one path that is **singular**, which is easy to miss when
copying the add call:

```sh
gh api --method DELETE repos/OWNER/REPO/issues/<parent-number>/sub_issue \
  -H 'X-GitHub-Api-Version: 2026-03-10' \
  -F sub_issue_id="$sub_id"
```

Both halves of a link must live in the same repository. This surface is new
enough that it has been changing, so if a call 404s, check GitHub's own REST
docs for sub-issues for the current paths and version value before assuming
the credential is at fault.

## Other quirks worth knowing before they bite

- **Issue numbers are per-repo and reused across nothing.** If the
  deployment ever tracks work for two repos, an issue reference must carry
  the repo, not just the number.
- **A PR is an issue.** Some REST issue endpoints and search queries return
  pull requests too. Filter with `is:issue` in search, or check for a
  `pull_request` key on REST results, or the pipeline will try to claim its
  own PRs as work items.
- **Closing is not archiving.** There's no "hide from the board" state
  beyond closed, so cancelled work stays in the closed list forever
  alongside completed work. `state_reason` is the only thing separating
  them; make sure queries that mean "finished successfully" check it.

## If the owner already uses a GitHub Projects board

Projects (v2) has a real single-select `Status` field, which is a much more
faithful mapping for the five states than a label family — one value at a
time, enforced. The cost is that it's a different API: GraphQL node IDs for
the project, the field and each option, resolved before you can set
anything, plus a newer REST surface for Projects that arrived after the
GraphQL one.

Worth choosing **only if the owner is already living on that board**, since
otherwise it's real complexity bought for nothing. If you do, verify the
current Projects API shape in GitHub's own docs rather than from these
notes; it's the youngest and most-changed of the surfaces mentioned here,
and nothing above was verified against it.

Choosing it **replaces** the label family rather than sitting alongside it,
and that retires the three rules above that only exist because labels are
unconstrained: there is no family to create with `gh label create`, two
states cannot coexist, and "open with no state label" stops being the inbox
query — the equivalent is "open and not on the board", which on a
pre-existing repo is a large set of human-owned work rather than an inbox.
Don't carry both designs; the point of using their board is that the state
the pipeline reads and the state the humans look at are the same one. The
team's own non-state labels (a `type:`/`area:`/`priority:` scheme, whatever
they have) are untouched by this and stay theirs — pass them back on every
edit, per operation 7.
