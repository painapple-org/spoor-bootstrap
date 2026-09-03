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

`install.sh`'s interview already ran before you started and recorded
answers in `.env` for whichever of these it asked: OWNER_TECH_LEVEL,
END_USER_TYPE, WORK_TRACKER, COMMS_CHANNEL. Read `.env` now, before asking
me anything. For any of those four that are already present and
non-empty, treat them as known — read them back to me for confirmation
instead of asking from scratch. Only ask me outright for whichever of
those four are still missing or empty.

Then also check `.env` for PRODUCT_REPO_PATH, AGENT_EMAIL_ADDRESS,
WORK_TRACKER_API_KEY, and COMMS_CHANNEL_TOKEN — install.sh never asks
about these, so expect them to be empty. Ask me for whichever of these
are still missing, one at a time, don't assume answers, and don't start
building any product code until all eight of these are accounted for
(either answered or explicitly deferred by me).

If the end-user type is "non-technical", read
skills/product-tech-stack/SKILL.md and follow the stack it requires —
don't decide a stack yourself.

Once the interview is done, give me the self-provisioning shopping list
from AGENTS.md (my own email address, a comms channel account, a GitHub
account, a work-tracker account/integration, and anything else needed for
the tools we discussed) so I can go create those accounts myself. Don't
try to register for any of them yourself.
```

---

That's the whole first-boot flow: read `AGENTS.md`, read `.env` to see
what `install.sh`'s interview already answered, ask only about what's
still missing, defer to the stack SKILL if relevant, hand back a
provisioning list. Everything after that — actually wiring up the chosen
work tracker and comms channel, writing product code, setting up
scheduling — is follow-on work once the human has provisioned what's on
that list.
