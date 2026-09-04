#!/usr/bin/env python3
#
# A toy product to check, so the runner next to it can be demonstrated rather
# than described. It is deliberately the smallest thing that has the shape a
# real synthetic check cares about:
#
#   - a public flow with a real side effect      POST /signup
#   - durable state the side effect writes to    an sqlite table
#   - a notification the side effect sends       a JSONL "outbox"
#   - an analytics number a real user moves      GET /stats
#   - a way to read the side effect back         GET /internal/*  (token-gated)
#   - a way to delete test data it created       POST /internal/purge
#
# The last two are what a real product usually has to grow before it can be
# checked properly, and they are the interesting part of adopting this pattern:
# `skills/synthetic-monitoring/SKILL.md`'s evidence and cleanup sections are
# the home for what they have to guarantee.
#
# `PRODUCT_BREAK` injects one specific lie per value, which is how `verify.sh`
# proves the check catches each one. A real product must never ship anything
# like it - it exists here because a check nobody has watched fail is a check
# nobody knows works.
#
#   none          behaves correctly
#   side_effect   answers 201 and writes nothing         (the classic 200-that-lies)
#   notification  writes the row, sends no notification  (a half-working flow)
#   pollution     counts synthetic signups as real       (test data reaching analytics)
#   slow          works, but takes SLOW_SECONDS to do it
#   error         answers 500
#
# Stdlib only, no persistence beyond a temp directory, single-threaded: it is a
# fixture, not a starting point for a product.

import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BREAK = os.environ.get("PRODUCT_BREAK", "none")
SLOW_SECONDS = float(os.environ.get("PRODUCT_SLOW_SECONDS", "6"))
EVIDENCE_TOKEN = os.environ.get("PRODUCT_EVIDENCE_TOKEN", "toy-evidence-token")
# The product's own rule for recognizing the checker's traffic. The checker
# builds addresses from SYNTHETIC_TEST_MARKER; this is the other half of that
# agreement, and the two being one agreement rather than two conventions is the
# whole point of the marker.
MARKER = os.environ.get("PRODUCT_SYNTHETIC_MARKER", "synthetic")
STATE_DIR = Path(os.environ.get("PRODUCT_STATE_DIR", "/tmp/example-product"))
OWNER_INBOX = "owner@example.invalid"


def connect():
	connection = sqlite3.connect(STATE_DIR / "product.db")
	connection.row_factory = sqlite3.Row
	return connection


def init_state():
	STATE_DIR.mkdir(parents=True, exist_ok=True)
	with connect() as connection:
		connection.execute(
			"""
			CREATE TABLE IF NOT EXISTS signups (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				email TEXT NOT NULL,
				name TEXT NOT NULL,
				is_synthetic INTEGER NOT NULL,
				created_at TEXT NOT NULL
			)
			"""
		)
	outbox = STATE_DIR / "outbox.jsonl"
	if not outbox.exists():
		outbox.write_text("")


def is_synthetic(email):
	return email.split("@")[0].startswith(MARKER)


def send_notification(email, name, synthetic):
	# A real product sends this to the business's own inbox, which is why the
	# subject carries the marker: a human reading that inbox has to be able to
	# tell a checked flow from a real lead at a glance.
	prefix = "[SYNTHETIC] " if synthetic else ""
	message = {
		"to": OWNER_INBOX,
		"subject": f"{prefix}New signup: {email}",
		"body": f"{name} <{email}> signed up.",
		"sent_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
	}
	with (STATE_DIR / "outbox.jsonl").open("a") as handle:
		handle.write(json.dumps(message) + "\n")


def read_outbox():
	lines = (STATE_DIR / "outbox.jsonl").read_text().splitlines()
	return [json.loads(line) for line in lines if line.strip()]


class Handler(BaseHTTPRequestHandler):
	protocol_version = "HTTP/1.1"

	def log_message(self, format, *args):  # noqa: A002 - signature is the stdlib's
		sys.stderr.write("%s - %s\n" % (self.address_string(), format % args))

	def reply(self, status, payload):
		body = json.dumps(payload).encode()
		self.send_response(status)
		self.send_header("Content-Type", "application/json")
		self.send_header("Content-Length", str(len(body)))
		self.end_headers()
		self.wfile.write(body)

	def read_json(self):
		length = int(self.headers.get("Content-Length") or 0)
		if not length:
			return {}
		return json.loads(self.rfile.read(length).decode())

	def authorized(self):
		if self.headers.get("X-Evidence-Token") == EVIDENCE_TOKEN:
			return True
		self.reply(403, {"error": "evidence endpoints need X-Evidence-Token"})
		return False

	def do_GET(self):
		route = urlparse(self.path)
		query = parse_qs(route.query)

		if route.path == "/health":
			self.reply(200, {"ok": True})
			return

		if route.path == "/stats":
			with connect() as connection:
				# The pollution break is here rather than at write time on
				# purpose: the row is correctly flagged, and the *reader*
				# ignores the flag. That is how test data actually reaches a
				# business's numbers - not by being unmarked, but by a query
				# that forgot the marker exists.
				if BREAK == "pollution":
					total = connection.execute("SELECT COUNT(*) FROM signups").fetchone()[0]
				else:
					total = connection.execute(
						"SELECT COUNT(*) FROM signups WHERE is_synthetic = 0"
					).fetchone()[0]
			self.reply(200, {"real_signups": total})
			return

		if route.path == "/internal/signups":
			if not self.authorized():
				return
			email = (query.get("email") or [""])[0]
			with connect() as connection:
				rows = connection.execute(
					"SELECT id, email, name, is_synthetic, created_at FROM signups WHERE email = ?",
					(email,),
				).fetchall()
			self.reply(200, {"rows": [dict(row) for row in rows]})
			return

		if route.path == "/internal/outbox":
			if not self.authorized():
				return
			to = (query.get("to") or [""])[0]
			about = (query.get("about") or [""])[0]
			messages = [
				message
				for message in read_outbox()
				if (not to or message["to"] == to) and (not about or about in message["subject"])
			]
			self.reply(200, {"messages": messages})
			return

		self.reply(404, {"error": "no such route"})

	def do_POST(self):
		route = urlparse(self.path)

		if route.path == "/signup":
			if BREAK == "error":
				self.reply(500, {"error": "injected failure"})
				return
			if BREAK == "slow":
				time.sleep(SLOW_SECONDS)

			payload = self.read_json()
			email = (payload.get("email") or "").strip().lower()
			name = (payload.get("name") or "").strip()
			if not email or not name:
				self.reply(400, {"error": "email and name are required"})
				return

			if BREAK == "side_effect":
				# The failure this whole pattern exists for: a perfectly
				# healthy-looking 201 with nothing behind it.
				self.reply(201, {"ok": True, "id": None})
				return

			synthetic = is_synthetic(email)
			with connect() as connection:
				cursor = connection.execute(
					"INSERT INTO signups (email, name, is_synthetic, created_at) VALUES (?, ?, ?, ?)",
					(email, name, int(synthetic), datetime.now(timezone.utc).isoformat(timespec="seconds")),
				)
				new_id = cursor.lastrowid
			if BREAK != "notification":
				send_notification(email, name, synthetic)
			self.reply(201, {"ok": True, "id": new_id})
			return

		if route.path == "/internal/purge":
			if not self.authorized():
				return
			email = (self.read_json().get("email") or "").strip().lower()
			if not email or not is_synthetic(email):
				# The product refuses to purge anything that isn't marked as
				# the checker's own. A cleanup affordance that will delete an
				# arbitrary address is a new way to lose real data, which is
				# strictly worse than the pollution it was added to prevent.
				self.reply(400, {"error": "purge only accepts a synthetic-marked address"})
				return
			with connect() as connection:
				deleted = connection.execute("DELETE FROM signups WHERE email = ?", (email,)).rowcount
			remaining = [message for message in read_outbox() if email not in message["subject"]]
			with (STATE_DIR / "outbox.jsonl").open("w") as handle:
				for message in remaining:
					handle.write(json.dumps(message) + "\n")
			self.reply(200, {"deleted_rows": deleted})
			return

		self.reply(404, {"error": "no such route"})


def main():
	port = int(os.environ.get("PRODUCT_PORT", "8099"))
	init_state()
	server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
	print(f"example product listening on 127.0.0.1:{port}, PRODUCT_BREAK={BREAK}", file=sys.stderr)
	server.serve_forever()


if __name__ == "__main__":
	main()
