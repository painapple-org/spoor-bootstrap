# STARTUP.md

This is the prompt a human pastes into their agentic harness of choice
(Claude Code, OpenCode, Codex CLI, or another) the very first time they run
it in a freshly cloned `spoor-bootstrap` checkout, after `install.sh` has
finished. It kicks off the first-boot interview described in
[`AGENTS.md`](./AGENTS.md).

---

## Paste this into your harness

```
You are running for the first time in a spoor-bootstrap checkout. Read
AGENTS.md in this repo now, in full, before doing anything else — it's
your entrypoint instructions.

Then run the first-boot interview it describes: ask me my own technical
experience level, ask who the end product we're building is for (a
technical or non-technical end-user), ask which work tracker I want to
use, and ask which comms channel I want you reachable on. Ask these one
at a time, don't assume answers, and don't start building any product
code until the interview is done.

If I tell you the product is for a non-technical end-user, read
skills/product-tech-stack/SKILL.md and follow the stack it requires —
don't decide a stack yourself.

Once the interview is done, give me the self-provisioning shopping list
from AGENTS.md (my own email address, a comms channel account, a GitHub
account, a work-tracker account/integration, and anything else needed for
the tools we discussed) so I can go create those accounts myself. Don't
try to register for any of them yourself.
```

---

That's the whole first-boot flow: read `AGENTS.md`, interview, defer to
the stack SKILL if relevant, hand back a provisioning list. Everything
after that — actually wiring up the chosen work tracker and comms channel,
writing product code, setting up scheduling — is follow-on work once the
human has provisioned what's on that list.
