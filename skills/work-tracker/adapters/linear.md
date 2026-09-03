# Adapter: Linear

Reference notes only — see [`README.md`](./README.md) for how these are
meant to be used, and [`../SKILL.md`](../SKILL.md) for the contract, the
state machine and the label vocabulary these map onto.

## Why it fits the contract well

Linear has native per-team **workflow states**, and each one carries a
`type` from a fixed vocabulary — `triage`, `backlog`, `unstarted`,
`started`, `completed`, `canceled` — independent of whatever the team
renamed the column to. That gives the contract's five states a real home,
and gives you a rename-proof way to ask "is this still open".

A reasonable mapping, to be confirmed against the owner's actual board:

- unrefined-inbox → a `backlog`-type state
- ready → an `unstarted`-type state
- in-progress → a `started`-type state
- in-review → a **second** `started`-type state (Linear allows several
  states per type, which is what makes a distinct review column possible)
- done / cancelled → the `completed` and `canceled` states

Prefer `state: { type: { nin: ["completed", "canceled"] } }` over listing
state names whenever the question is "open work". Filtering by `name` breaks
silently the day someone renames a column in the UI; filtering by `type`
doesn't.

## Access and identity

Two mechanisms, both real:

- **Linear's MCP server**, if the harness supports MCP. Much less code, and
  covers the common operations. Its tool surface is narrower than the API
  though: things like archiving have been missing from it. **Check the raw
  GraphQL API before concluding an operation is impossible** — "no MCP tool
  for it" is not the same as "not supported".
- **GraphQL directly**, at Linear's `/graphql` endpoint. Worth having
  available even alongside MCP, for exactly the gap above. A thin helper
  over `urllib`/`httpx` with one function per query is enough; there's no
  need for a generated client.

Auth header shape differs by credential type and this is an easy hour to
lose: a **personal API key** goes in `Authorization` **as-is, with no
`Bearer ` prefix**, while an **OAuth access token** uses
`Authorization: Bearer <token>`.

The credential must belong to the agent's own Linear user, per the
contract — that's what makes `assignee` a real ownership signal and what
makes the agent's own comments distinguishable from a human's by author.

Scope identifier is the **team key** (the short prefix in issue
identifiers). Resolve UUIDs from it at runtime; don't record UUIDs.

## The seven operations

### 1. Query by state + owner

`issues(filter: { ... })` with comparator objects — each leaf takes an
operator (`eq`, `neq`, `in`, `nin`, `gte`, `lte`), not a bare value:

```graphql
query($teamKey: String!) {
  issues(filter: {
    team: { key: { eq: $teamKey } }
    state: { name: { eq: "<ready-state>" } }
    assignee: { name: { eq: "<agent-user-name>" } }
    labels: { name: { eq: "<refined-label>" } }
  }) {
    nodes { id identifier url title labels { nodes { name } } }
  }
}
```

`or: [ { ... }, { ... } ]` nests inside a filter for disjunctions. Date
filters take a `DateTimeOrDuration` — an ISO-8601 timestamp works; the
duration string form is documented but verify its syntax in Linear's docs
before relying on it.

Two things to get right here:

- **Matching an assignee by display `name` is fragile.** It's a mutable
  profile field, and a human renaming themselves silently empties the
  query. Resolve the agent's user id once per run
  (`users(filter: { ... }) { nodes { id } }`) and filter on the id, or use
  the API's "is me" assignee predicate if it's present in the schema —
  verify that against Linear's schema rather than assuming it.
- **`issues()` is paginated and does not tell you it truncated.** Any query
  that means "all of them" needs `first: 100, after: $cursor` plus
  `pageInfo { hasNextPage endCursor }` and a loop. Without it you get one
  page and a plausible-looking wrong answer, which is the worst shape of
  bug for a pipeline that decides what to work on from the result.

### 2. Read one item in full

`issue(id: ...)` accepts **either** the UUID **or** the human identifier
(`TEAM-123`), which is a genuine convenience — a URL scraped from a comment
can be used directly.

GraphQL returns nothing you didn't select, so "in full" is your
responsibility: request `description`, `comments { nodes { body createdAt
user { name } } }`, `labels { nodes { id name } }`, `state { name type }`,
`assignee { id name }`, and the relation fields you care about. A stage that
forgot to select `comments` sees an issue with no history, not an error.

### 3. Claim

One mutation sets both state and assignee, so the claim is **genuinely
atomic** here — this is Linear's biggest advantage over the alternatives:

```graphql
mutation($id: String!, $stateId: String!, $assigneeId: String!) {
  issueUpdate(id: $id, input: { stateId: $stateId, assigneeId: $assigneeId }) {
    success
    issue { identifier url state { name } }
  }
}
```

`stateId` is a **per-team UUID**. Resolve it by name at runtime:

```graphql
workflowStates(filter: { team: { key: { eq: $teamKey } }, name: { eq: $stateName } }) {
  nodes { id }
}
```

Never hardcode a state UUID. It's per-team, it's meaningless in any other
workspace, and it makes the file unusable for the next deployment.

### 4. Comment

```graphql
mutation($issueId: String!, $body: String!) {
  commentCreate(input: { issueId: $issueId, body: $body }) {
    success
    comment { id }
  }
}
```

Body is markdown. Pass real newlines in the variable, not escaped `\n`
sequences — this bites particularly through MCP.

### 5. Transition state

`issueUpdate` with just `stateId`, resolved as above. Unlike Jira there's no
transition graph to satisfy: any state can be set from any state.

### 6. Create

`issueCreate(input: { teamId, title, description, assigneeId, stateId })`.
`teamId` is required and is the UUID, not the key — resolve it from the key
via `teams(filter: { key: { eq: $teamKey } })`. Omitting `stateId` lands the
issue in the team's first backlog-category state, which is usually what you
want for a newly-filed idea, but decide it rather than inherit it.

### 7. Labels

**This is the API the contract's replace-semantics warning is about.**
There is no add-one-label mutation. `issueUpdate(input: { labelIds: [...] })`
**replaces the entire set**, so adding one label means: read
`labels { nodes { id } }`, append, write the whole array back. Skipping the
read silently strips every other label on the issue.

`issueRemoveLabel(id: $issueId, labelId: $labelId)` exists for the
single-removal case and avoids the read-modify-write.

Label ids are workspace- or team-scoped UUIDs; resolve them by name at
runtime the same way as state ids. Note that Linear labels can be grouped,
and a label in a group may be mutually exclusive with its siblings —
worth checking how the owner's labels are organized before assuming two
can coexist.

## Other quirks worth knowing before they bite

- **Parent/child relations are not in the generic "relations" surface.** A
  sub-issue's link to its parent is the dedicated `parent` / `children`
  field, and a query that inspects issue relations generically will report
  no parent for an issue that plainly has one in the UI. Select `parent { id
  identifier }` and `children { nodes { id } }` explicitly.
- **A parent filter given a human identifier can silently return an empty
  set** even when real sub-issues exist. If a "does this have children"
  check comes back empty and you have any reason to doubt it, re-run it
  with the parent's **UUID** before acting on the answer. This one has
  caused real wrong conclusions.
- **The `Refined`-style eligibility label and the ready state are two
  separate conditions.** Linear will happily let a labelled issue sit in
  the wrong column, where the pipeline's query can never see it, forever.
  Because the failure is invisible rather than loud, it's worth a note in
  the team's own issue template — see the contract's label section.
- **`updatedAt` is not a timeline of work.** It moves on any touch,
  including the agent's own comment. Don't build "what happened in the last
  N days" from it; use `history { nodes { createdAt toState { name } } }`
  for state transitions, or the underlying git/PR dates for shipped work.
- **Rate limits are per-credential and differ between personal API keys and
  OAuth.** Read the current numbers from Linear's own rate-limit docs; the
  responses also carry the remaining budget in headers, which is the
  honest source at runtime. No number is reproduced here on purpose.
- **Archiving is distinct from cancelling.** Cancelled issues remain in
  normal queries (filtered by state type); archived ones drop out. If the
  owner wants a clean board, archiving is the operation — and it's one of
  the things more likely to be reachable via GraphQL than via MCP.
