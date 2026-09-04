# Adapter: Jira

Reference notes only — see [`README.md`](./README.md) for how these are
meant to be used, and [`../SKILL.md`](../SKILL.md) for the contract, the
state machine and the label vocabulary these map onto.

These notes are for **Jira Cloud** and its REST API v3. Jira Server / Data
Center is a different product with a different API version and a different
auth model; if the owner is on a self-hosted instance, none of the endpoint
paths or auth details below should be trusted without checking their
version's own docs.

Jira also churns its API more than the alternatives here — one search
endpoint was removed outright and replaced within recent memory. Treat every
path in this file as "was true when written, confirm it": issue one real
call against the owner's instance during specialization and record what
actually worked.

## The one structural mismatch: you can't set a status

Jira has native statuses, which look like a clean fit — but **there is no
"set this issue's status to X" operation**. Status changes happen only by
executing a **transition**, and only transitions that the project's workflow
permits *from the issue's current status* are available. So the contract's
"transition an item's state" verb becomes two calls:

1. `GET /rest/api/3/issue/{issueIdOrKey}/transitions` — returns the
   transitions available right now, each with an `id` and the status it
   leads `to`.
2. `POST /rest/api/3/issue/{issueIdOrKey}/transitions` with
   `{"transition": {"id": "<id>"}}`.

Three consequences:

- **Never hardcode a transition id.** They're per-workflow, and the same
  logical move can have different ids in different projects or for
  different issue types.
- **Look up the transition by its destination status, not by its own
  name.** A transition's name is often a verb someone chose once ("Start
  work"); its `to.name` / `to.statusCategory` is the thing you actually
  care about.
- **A missing transition is a permission or workflow condition, not a
  bug in your code.** If the move you want isn't in the GET response, the
  agent's own account isn't allowed to make it from here. Fail loudly and
  report *the list of transitions that were available* — that's the
  information the human needs, and guessing an id instead produces a
  confusing 400.

Statuses also carry a coarse **status category** (`statusCategory.key` of
`new` / `indeterminate` / `done`). Like Linear's state `type`, it's the
rename-proof way to ask "is this open", and worth preferring over status
names wherever the question is that coarse.

Mapping the five states: the four live ones map to four workflow statuses,
which the owner may need to *add* to their workflow — a default Jira
workflow often doesn't have a distinct review column. Done vs cancelled are
usually two separate `done`-category statuses (a Done and a Won't Do), and
Jira additionally has a `resolution` field that some workflows set on
transition; check which of the two the owner's board actually distinguishes
on before deciding which one your queries read.

## Access and identity

REST v3 over HTTPS at the site's `/rest/api/3/` base. The site itself is
per-customer, so the `https://<site>.atlassian.net` half of every path in
this file is read from `WORK_TRACKER_BASE_URL` in `.env` — never hardcoded
here or in the client, per [`../SKILL.md`](../SKILL.md)'s note on the three
`WORK_TRACKER*` keys.

Authenticated with **HTTP Basic using the account's email address plus an
API token** (not the account password). The token is
`WORK_TRACKER_API_KEY`. The email has no `.env` slot of its own on purpose:
it reads from `AGENT_EMAIL_ADDRESS`, since Basic auth's username has to be
the account the token was minted by, and that account is the agent's own.
Record that as the answer to the second-auth-value marker in
[`../SKILL.md`](../SKILL.md) — which is the home for the decision — rather
than leaving a client to infer it. Both values belong to the agent's own
Atlassian account, per the contract.

There's no first-party CLI worth depending on. Official language SDKs exist;
so does an Atlassian MCP server. If the harness supports MCP, that's the
lowest-effort path — but the same caution as any MCP surface applies: it
wraps a subset, and it has had its own pagination bugs, so check the raw
REST API before concluding something can't be done.

Scope identifier is the **project key** (the prefix in issue keys).

## The seven operations

### 1. Query by state + owner

JQL, via the search endpoint. `assignee = currentUser()` resolves against
the credential in use, which is exactly right given the contract already
requires the agent to hold its own account:

```
project = <KEY>
  AND assignee = currentUser()
  AND status = "<in-progress-status>"
  AND labels = <refined-label>
ORDER BY updated DESC
```

JQL supports the negation the contract needs and GitHub's CLI doesn't:
`AND labels != <label>` — but note the trap that in JQL a `!=` comparison
**excludes issues where the field is empty**. "Doesn't have the refined
label" is `AND (labels != <label> OR labels IS EMPTY)`, and the same shape
applies to any optional field. Getting this wrong makes freshly-created
work invisible.

On the endpoint itself: the long-standing `/rest/api/3/search` was
**deprecated and removed**, replaced by `/rest/api/3/search/jql`, and
pagination moved from `startAt` to an opaque **`nextPageToken`** carried in
the response. Also, that endpoint returns a minimal field set unless you
ask: pass `fields` explicitly (`summary,status,labels,assignee,updated`) or
you'll get back issues with almost nothing on them. Confirm the current
path, the parameter names and the pagination contract in Atlassian's own
issue-search docs before writing the client — this is the single most
churned part of this API and the part these notes are least willing to
vouch for.

### 2. Read one item in full

`GET /rest/api/3/issue/{issueIdOrKey}` for the fields, and comments as a
**separate** call: `GET /rest/api/3/issue/{issueIdOrKey}/comment`. The
issue payload's embedded comment data is truncated/paginated, so a stage
that reads only the issue will see a partial history — which, for a
contract where comments carry the previous run's plan and the human's
answers, is a silent correctness bug rather than a cosmetic one.

### 3. Claim

Not atomic, and worse than the alternatives here: assignment and status are
different operations. Assign via
`PUT /rest/api/3/issue/{issueIdOrKey}/assignee` with the target's
`accountId` (Jira Cloud identifies users by opaque `accountId`, not by
username or email — a privacy-driven change that broke a lot of older
scripts), then perform the transition.

A transition POST *can* carry `fields` and an assignee update in the same
request, which collapses it to one call — verify the exact payload shape in
Atlassian's docs for the transitions endpoint, since it's also where
transition-screen required fields have to be supplied.

Do the assignment first, so a crash between the two leaves the item owned
but not yet marked in progress, rather than in progress and owned by nobody.

### 4. Comment

`POST /rest/api/3/issue/{issueIdOrKey}/comment`.

**The v3 API expects the body in Atlassian Document Format (ADF)** — a
structured JSON document — not a markdown or plain string. This is the
single most common surprise when moving from the older v2 API, which
accepted a plain string. A minimal ADF paragraph document is short enough to
construct by hand, but get the exact shape from Atlassian's ADF
documentation; a malformed document is rejected, and the same requirement
applies to `description` and any textarea custom field. If ADF turns out to
be more friction than it's worth for comment-writing, v2 remains available
and accepts plain strings — that's a decision to make and record, not to
discover mid-run.

### 5. Transition state

Covered above — it's the structural mismatch, not a footnote.

### 6. Create

`POST /rest/api/3/issue` with `fields` containing at minimum the project,
the issue type and the summary. Two things that make this fail confusingly:

- **A field must be present on the project's create screen to be settable.**
  Passing a field that isn't gets you a 400 naming the field, which reads
  like the field doesn't exist. `GET /rest/api/3/issue/createmeta` (verify
  the current path) is how you find out what's actually accepted.
- **The issue type is per-project** and named by the project's own
  configuration. Look it up; don't assume "Task" exists.

### 7. Labels

Jira labels are add/remove operations on an update document, so the
contract's replace-semantics warning does **not** apply on this path:

```
PUT /rest/api/3/issue/{issueIdOrKey}
{"update": {"labels": [{"add": "<label>"}, {"remove": "<other-label>"}]}}
```

It *does* apply if you use `{"fields": {"labels": [...]}}` instead, which
replaces the whole set. Prefer the `update` form.

Two divergences from GitHub-style labels:

- **Labels are free-text and are not pre-registered.** A typo creates a new
  label silently rather than erroring, so nothing catches
  `refned`. Validate against the agreed set from `SKILL.md` in your own code
  before writing — this is the one place a wrapper genuinely earns its keep.
- **Labels cannot contain spaces.** Any multi-word label name from the
  contract's vocabulary needs a hyphen or underscore form decided during
  specialization.

## Other quirks worth knowing before they bite

- **Hierarchy is three different mechanisms.** Sub-tasks and (on
  team-managed projects) the epic link both live on the `parent` field;
  everything else is `issuelinks` with a link type. Neither comes back
  unless requested, and "find this issue's children" is a JQL query
  (`parent = <KEY>`), not a field read.
- **Company-managed vs team-managed projects behave differently** — most
  visibly around workflows, statuses and epic/parent handling. Record which
  kind the owner's project is in `SKILL.md`, because it changes the answers
  above.
- **Permissions are granular and silent.** A missing permission usually
  presents as an empty list or an absent option rather than a 403: an
  unavailable transition, a field that won't set, an issue that doesn't
  appear in a JQL result the human can plainly see in the UI. When a query
  returns surprisingly little, "the agent's account can't see it" belongs
  near the top of the hypothesis list.
- **Notification noise.** Jira mails watchers on comments and transitions by
  default, and a pipeline that comments on every pass will bury the owner.
  Some endpoints accept a notify-suppression parameter and some don't;
  worth checking early, because the complaint arrives fast.
