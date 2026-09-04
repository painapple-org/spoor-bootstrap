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

A reasonable mapping, to be confirmed against the owner's actual workflow:

- unrefined-inbox → a `new`-category status (a default board's `To Do`, or
  the project's Triage status if it has one)
- ready → a second `new`-category status
- in-progress → an `indeterminate`-category status (`In Progress`)
- in-review → a **second** `indeterminate`-category status, which the owner
  may need to *add* to the workflow — a default Jira workflow often has no
  distinct review column, and adding one also means adding the transitions
  that reach it
- done / cancelled → two separate `done`-category statuses (typically a
  `Done` and a `Won't Do`)

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

There's no first-party CLI. Official language SDKs exist; so does an
Atlassian MCP server. If the harness supports MCP, that's the lowest-effort
path — but the same caution as any MCP surface applies: it wraps a subset,
and it has had its own pagination bugs, so check the raw REST API before
concluding something can't be done.

Scope identifier is the **project key** (the prefix in issue keys).

### Setting up the shell for the commands below

Every REST command in this file is one `curl`, written against three shell
variables so it can be copied and run as-is. Export them once from the
`.env` values named above:

```sh
export JIRA_BASE="$WORK_TRACKER_BASE_URL"                    # https://<site>.atlassian.net
export JIRA_AUTH="$AGENT_EMAIL_ADDRESS:$WORK_TRACKER_API_KEY"
export JIRA_PROJECT=<KEY>
```

`curl -u "$JIRA_AUTH"` is the Basic auth pair described above. Confirm the
credential works, and get the agent's own `accountId` (needed by every
assignment call), with:

```sh
curl -sS -u "$JIRA_AUTH" -H 'Accept: application/json' \
  "$JIRA_BASE/rest/api/3/myself"
```

Bodies below are passed with `-d @- <<JSON`. An unquoted heredoc delimiter
lets `$JIRA_PROJECT` and friends expand inside the JSON; a quoted one
(`<<'JSON'`) suppresses that, and is used where the payload contains no
variables. Building the JSON with `jq -n` instead is worth it for anything
whose text comes from a variable, since prose interpolated straight into a
heredoc breaks the document on the first `"`.

### The third-party CLI, if you'd rather not write curl

`ankitpokhrel/jira-cli` is not from Atlassian and is not installed by
`install.sh`, but it covers most of the contract in one command each and —
the real reason to consider it — it takes **plain text** for comments and
descriptions, building the ADF that operation 4 below otherwise makes you
construct by hand. It authenticates from a `JIRA_API_TOKEN` environment
variable plus a `jira init` run that records the site and project.

```sh
jira issue list -q "project = $JIRA_PROJECT AND assignee = currentUser() AND status = \"In Progress\"" --plain
jira issue view ISSUE-1 --comments 20
jira issue assign ISSUE-1 "$(jira me)"
jira issue move ISSUE-1 "In Progress"
jira issue comment add ISSUE-1 --comment "..."
jira issue create -t Task -s "..." -b "..." -l <refined-label>
```

It's a wrapper over the same REST API, so everything below still describes
what actually happens — and anything it doesn't expose is reachable with the
`curl` calls directly. Decide which path this deployment uses and record it
in [`../SKILL.md`](../SKILL.md) rather than mixing both.

## The seven operations

### 1. Query by state + owner

JQL, via the search endpoint. `assignee = currentUser()` resolves against
the credential in use, which is exactly right given the contract already
requires the agent to hold its own account:

```sh
curl -sS -u "$JIRA_AUTH" -X POST "$JIRA_BASE/rest/api/3/search/jql" \
  -H 'Content-Type: application/json' -H 'Accept: application/json' -d @- <<JSON
{
  "jql": "project = $JIRA_PROJECT AND assignee = currentUser() AND status = \"<in-progress-status>\" AND labels = <refined-label> ORDER BY updated DESC",
  "fields": ["summary", "status", "labels", "assignee", "updated", "parent"],
  "maxResults": 100
}
JSON
```

The response is `{"issues": [...], "nextPageToken": "..."}`. Add
`"nextPageToken": "<value from the previous response>"` to the body to get
the next page, and stop when the key is **absent** from the response — an
absent token is the only end-of-results signal, there is no total count.
The tokens are short-lived, so don't persist one between runs; start from
page one instead.

JQL supports the negation the contract needs and GitHub's CLI doesn't:
`AND labels != <label>` — but note the trap that in JQL a `!=` comparison
**excludes issues where the field is empty**. "Doesn't have the refined
label" is `AND (labels != <label> OR labels IS EMPTY)`, and the same shape
applies to any optional field. Getting this wrong makes freshly-created
work invisible.

On the endpoint itself: the long-standing `/rest/api/3/search` was
**deprecated and removed**, replaced by the `/rest/api/3/search/jql` used
above, and pagination moved from `startAt` to the opaque `nextPageToken`.
The endpoint also returns a minimal field set unless you pass `fields`
explicitly, which is why every example here does. This is the most churned
part of this API: if a call above 404s or returns an unexpected envelope,
check Atlassian's own issue-search docs for the current path before
assuming your payload is wrong.

### 2. Read one item in full

Two calls, because the issue payload's embedded comment data is
truncated/paginated — a stage that reads only the issue sees a partial
history, which for a contract where comments carry the previous run's plan
and the human's answers is a silent correctness bug, not a cosmetic one:

```sh
curl -sS -u "$JIRA_AUTH" -H 'Accept: application/json' \
  "$JIRA_BASE/rest/api/3/issue/ISSUE-1?fields=summary,description,status,labels,assignee,parent,issuelinks"

curl -sS -u "$JIRA_AUTH" -H 'Accept: application/json' \
  "$JIRA_BASE/rest/api/3/issue/ISSUE-1/comment?maxResults=100&orderBy=created"
```

Both accept the issue key or the numeric issue id interchangeably. The
comment call paginates on `startAt`/`total`, not on a token — the two
endpoints genuinely differ here.

### 3. Claim

Not atomic, and worse than the alternatives here: assignment and status are
different operations. Jira Cloud identifies users by an opaque `accountId`,
not by username or email — a privacy-driven change that broke a lot of
older scripts. Get the agent's own from `/rest/api/3/myself` above, or
someone else's by search:

```sh
curl -sS -u "$JIRA_AUTH" -H 'Accept: application/json' --get \
  --data-urlencode 'query=person@example.com' \
  "$JIRA_BASE/rest/api/3/user/search"
```

Assign (a 204 with no body on success):

```sh
curl -sS -u "$JIRA_AUTH" -X PUT "$JIRA_BASE/rest/api/3/issue/ISSUE-1/assignee" \
  -H 'Content-Type: application/json' -d '{"accountId": "<accountId>"}'
```

Then transition, per operation 5. **Do the assignment first**, so a crash
between the two leaves the item owned but not yet marked in progress,
rather than in progress and owned by nobody.

The transition POST can also carry the assignee in its own `fields`, which
collapses the claim to one call — the payload in operation 5 shows it. That
only works if `assignee` is on the transition's screen; if it isn't, the
call 400s naming the field, and the two-call form above is the answer.

### 4. Comment

**The v3 API expects the body in Atlassian Document Format (ADF)** — a
structured JSON document, not markdown and not a plain string. This is the
single most common surprise when moving from the older v2 API. A plain
string here is a 400.

```sh
curl -sS -u "$JIRA_AUTH" -X POST "$JIRA_BASE/rest/api/3/issue/ISSUE-1/comment" \
  -H 'Content-Type: application/json' -H 'Accept: application/json' -d @- <<'JSON'
{
  "body": {
    "type": "doc",
    "version": 1,
    "content": [
      {"type": "paragraph", "content": [
        {"type": "text", "text": "Plain sentence, then "},
        {"type": "text", "text": "bold words", "marks": [{"type": "strong"}]},
        {"type": "text", "text": " and a link.", "marks": [
          {"type": "link", "attrs": {"href": "https://example.com"}}
        ]}
      ]},
      {"type": "paragraph", "content": [{"type": "text", "text": "Second paragraph."}]}
    ]
  }
}
JSON
```

The shape to internalise: one `doc` with `version: 1`, whose `content` is a
list of block nodes; a `paragraph`'s own `content` is a list of `text`
nodes; emphasis is a **mark on a text node**, never inline syntax. Writing
`**bold**` in a `text` node renders those asterisks literally. A blank line
between paragraphs is two `paragraph` nodes, not a `\n`. The same
requirement applies to `description` and to any textarea custom field.

If ADF is more friction than it's worth, **v2 is still available and takes
a plain string** — same path, different version segment:

```sh
curl -sS -u "$JIRA_AUTH" -X POST "$JIRA_BASE/rest/api/2/issue/ISSUE-1/comment" \
  -H 'Content-Type: application/json' -d '{"body": "Plain text, wiki markup honoured."}'
```

Pick one and record it in [`../SKILL.md`](../SKILL.md); discovering the
choice mid-run is how a comment footer ends up formatted two ways.

### 5. Transition state

The structural mismatch above, in two calls. First ask what's available
*from the current status*, and pick by destination rather than by the
transition's own name:

```sh
curl -sS -u "$JIRA_AUTH" -H 'Accept: application/json' \
  "$JIRA_BASE/rest/api/3/issue/ISSUE-1/transitions"
```

That returns `{"transitions": [{"id": "31", "name": "Start work", "to":
{"name": "In Progress", "statusCategory": {"key": "indeterminate"}}}, ...]}`.
Select the id by `to.name`:

```sh
target='<in-progress-status>'
tid=$(curl -sS -u "$JIRA_AUTH" -H 'Accept: application/json' \
  "$JIRA_BASE/rest/api/3/issue/ISSUE-1/transitions" \
  | jq -r --arg to "$target" '.transitions[] | select(.to.name == $to) | .id')
```

An empty `$tid` is the loud-failure case described above: report the
available `to.name` values rather than guessing an id. Then execute it —
also a 204 with no body, and the place to fold in the assignment from
operation 3:

```sh
curl -sS -u "$JIRA_AUTH" -X POST "$JIRA_BASE/rest/api/3/issue/ISSUE-1/transitions" \
  -H 'Content-Type: application/json' -d @- <<JSON
{
  "transition": {"id": "$tid"},
  "fields": {"assignee": {"accountId": "<accountId>"}}
}
JSON
```

The terminal states are transitions like any other — there is no separate
close or resolve call. If the workflow sets `resolution` on the way to a
`done`-category status through a transition screen, it goes in the same
`fields` object: `"resolution": {"name": "Won't Do"}`.

### 6. Create

```sh
curl -sS -u "$JIRA_AUTH" -X POST "$JIRA_BASE/rest/api/3/issue" \
  -H 'Content-Type: application/json' -H 'Accept: application/json' -d @- <<JSON
{
  "fields": {
    "project": {"key": "$JIRA_PROJECT"},
    "issuetype": {"name": "<issue-type-name>"},
    "summary": "One-line title",
    "labels": ["<refined-label>"],
    "assignee": {"accountId": "<accountId>"},
    "description": {
      "type": "doc", "version": 1,
      "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Body."}]}]
    }
  }
}
JSON
```

Returns `{"id": "...", "key": "$JIRA_PROJECT-123", "self": "..."}`. Note
the issue lands in whatever status the workflow's initial step is — you
cannot pass a status on create, so a create-then-transition pair is the only
way to file something anywhere other than the entry column.

Two things that make this fail confusingly, both answered by createmeta:

- **A field must be present on the project's create screen to be settable.**
  Passing one that isn't gets you a 400 naming the field, which reads like
  the field doesn't exist.
- **The issue type is per-project** and named by the project's own
  configuration. Look it up; don't assume `Task` exists.

```sh
curl -sS -u "$JIRA_AUTH" -H 'Accept: application/json' \
  "$JIRA_BASE/rest/api/3/issue/createmeta/$JIRA_PROJECT/issuetypes"

curl -sS -u "$JIRA_AUTH" -H 'Accept: application/json' \
  "$JIRA_BASE/rest/api/3/issue/createmeta/$JIRA_PROJECT/issuetypes/<issueTypeId>"
```

The bare `/rest/api/3/issue/createmeta` that older scripts use is
deprecated in favour of those two per-project paths.

### 7. Labels

Jira labels are add/remove operations on an update document, so the
contract's replace-semantics warning does **not** apply on this path:

```sh
curl -sS -u "$JIRA_AUTH" -X PUT "$JIRA_BASE/rest/api/3/issue/ISSUE-1" \
  -H 'Content-Type: application/json' -d @- <<'JSON'
{"update": {"labels": [{"add": "<incoming-label>"}, {"remove": "<outgoing-label>"}]}}
JSON
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

## Parent / child links

Not one of the contract's seven operations, but every stage that splits work
into sub-items needs it, and **hierarchy here is three different
mechanisms**: sub-tasks and (on team-managed projects) the epic link both
live on the `parent` field, while everything else is `issuelinks` with a
link type. Neither comes back unless requested.

Set or move a parent — an ordinary field edit, so `fields` is correct here
even though operation 7 prefers `update`:

```sh
curl -sS -u "$JIRA_AUTH" -X PUT "$JIRA_BASE/rest/api/3/issue/ISSUE-2" \
  -H 'Content-Type: application/json' -d @- <<'JSON'
{"fields": {"parent": {"key": "ISSUE-1"}}}
JSON
```

Passing `"parent": null` detaches it. The same `parent` key works inside
operation 6's create payload, which is cheaper than creating then linking.

"Find this issue's children" is a **JQL query, not a field read** — there is
no children array on the issue:

```sh
curl -sS -u "$JIRA_AUTH" -X POST "$JIRA_BASE/rest/api/3/search/jql" \
  -H 'Content-Type: application/json' -H 'Accept: application/json' -d @- <<'JSON'
{"jql": "parent = ISSUE-1 ORDER BY created ASC", "fields": ["summary", "status", "assignee"]}
JSON
```

Non-hierarchical relations (blocks, duplicates, relates-to) are a separate
endpoint, with the link type names coming from the instance's own
configuration rather than a fixed vocabulary:

```sh
curl -sS -u "$JIRA_AUTH" -H 'Accept: application/json' \
  "$JIRA_BASE/rest/api/3/issueLinkType"

curl -sS -u "$JIRA_AUTH" -X POST "$JIRA_BASE/rest/api/3/issueLink" \
  -H 'Content-Type: application/json' -d @- <<'JSON'
{
  "type": {"name": "Blocks"},
  "inwardIssue": {"key": "ISSUE-2"},
  "outwardIssue": {"key": "ISSUE-1"}
}
JSON
```

`inward` vs `outward` decides direction, and which is which depends on the
link type's own `inward`/`outward` description strings from that first call
— read them rather than guessing, since getting it backwards produces a link
that reads as the exact opposite of what was meant.

## Other quirks worth knowing before they bite

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
