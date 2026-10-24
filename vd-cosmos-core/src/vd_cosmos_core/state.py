"""Append-only journal with global expected-head concurrency and SQL invariants."""
import json
import sqlite3

from .commands import authorize_event, COMMANDS, Category
from .errors import FlowError
from .files import confined


SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    previous_id INTEGER NOT NULL,
    kind TEXT NOT NULL,
    command TEXT NOT NULL,
    request_id TEXT,
    operation_id TEXT,
    build_key TEXT,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE INDEX IF NOT EXISTS by_kind ON events(kind, id);
CREATE INDEX IF NOT EXISTS by_build ON events(COALESCE(build_key, json_extract(payload, '$.build')), id);
CREATE TRIGGER IF NOT EXISTS no_update BEFORE UPDATE ON events
BEGIN SELECT RAISE(ABORT, 'append_only'); END;
CREATE TRIGGER IF NOT EXISTS no_delete BEFORE DELETE ON events
BEGIN SELECT RAISE(ABORT, 'append_only'); END;
CREATE TRIGGER IF NOT EXISTS expected_head BEFORE INSERT ON events
WHEN NEW.previous_id != COALESCE((SELECT MAX(id) FROM events), 0)
BEGIN SELECT RAISE(ABORT, 'stale_head'); END;
CREATE UNIQUE INDEX IF NOT EXISTS one_workflow_result ON events(operation_id)
    WHERE kind = 'workflow_result';
CREATE UNIQUE INDEX IF NOT EXISTS one_click ON events(request_id)
    WHERE kind = 'click_intent';
CREATE UNIQUE INDEX IF NOT EXISTS one_bind ON events(build_key)
    WHERE kind = 'bind';
CREATE UNIQUE INDEX IF NOT EXISTS one_session_id ON events(operation_id)
    WHERE kind = 'submit_session_started';
CREATE UNIQUE INDEX IF NOT EXISTS one_session_end ON events(operation_id)
    WHERE kind = 'submit_session_finished';
CREATE TRIGGER IF NOT EXISTS one_active_session BEFORE INSERT ON events
WHEN NEW.kind = 'submit_session_started' AND (
    EXISTS (SELECT 1 FROM events WHERE request_id=NEW.request_id AND kind='click_intent')
    OR EXISTS (SELECT 1 FROM events AS s
        WHERE s.request_id=NEW.request_id AND s.kind='submit_session_started'
        AND NOT EXISTS (SELECT 1 FROM events AS e
            WHERE e.request_id=s.request_id AND e.operation_id=s.operation_id
            AND e.kind='submit_session_finished')))
BEGIN SELECT RAISE(ABORT, 'request_occupied'); END;
CREATE TRIGGER IF NOT EXISTS session_required BEFORE INSERT ON events
WHEN NEW.kind IN ('submit_session_finished', 'click_intent') AND NOT EXISTS (
    SELECT 1 FROM events AS s WHERE s.kind='submit_session_started'
    AND s.request_id=NEW.request_id AND s.operation_id=NEW.operation_id
    AND NOT EXISTS (SELECT 1 FROM events AS e WHERE e.kind='submit_session_finished'
        AND e.operation_id=s.operation_id))
BEGIN SELECT RAISE(ABORT, 'missing_active_session'); END;
CREATE TRIGGER IF NOT EXISTS required_identifiers BEFORE INSERT ON events
WHEN (NEW.kind IN ('submit_session_started','submit_session_finished','click_intent')
      AND (COALESCE(NEW.request_id,'')='' OR COALESCE(NEW.operation_id,'')=''))
  OR (NEW.kind='bind' AND (COALESCE(NEW.build_key,'')='' OR COALESCE(NEW.request_id,'')=''))
BEGIN SELECT RAISE(ABORT, 'missing_identity'); END;
"""


class EventStore:
    def __init__(self, root):
        path = confined(root, "state/state.db")
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.connection = sqlite3.connect(path, timeout=2, isolation_level=None)
            self.connection.row_factory = sqlite3.Row
            self.connection.execute("PRAGMA busy_timeout=2000")
            self.connection.execute("PRAGMA journal_mode=WAL")
            self.connection.executescript(SCHEMA)
        except sqlite3.Error as error:
            if hasattr(self, "connection"):
                self.connection.close()
            raise FlowError(6, classify(error)) from None

    def close(self):
        self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def head(self):
        try:
            return self.connection.execute("SELECT COALESCE(MAX(id),0) FROM events").fetchone()[0]
        except sqlite3.Error:
            raise FlowError(6, 'state_busy') from None

    def events(self, build_key=None, *, after=0, kinds=None, latest=False):
        query, values = 'SELECT * FROM events WHERE id > ?', [after]
        if build_key is not None:
            query += " AND COALESCE(build_key,json_extract(payload,'$.build')) = ?"
            values.append(build_key)
        if kinds:
            query += ' AND kind IN (' + ','.join('?' for _ in kinds) + ')'
            values.extend(kinds)
        query += ' ORDER BY id ' + ('DESC LIMIT 1' if latest else 'ASC')
        try:
            return [dict(row) | {'payload': json.loads(row['payload'])} for row in self.connection.execute(query, values)]
        except (sqlite3.Error, ValueError):
            raise FlowError(6, 'state_busy') from None

    def append(self, context, kind, payload, expected_previous, *, request_id=None,
               operation_id=None, build_ref=None):
        authorize_event(context, kind)
        if type(expected_previous) is not int or expected_previous < 0:
            raise FlowError(2, "invalid_expected_event")
        build_key = json.dumps(build_ref.to_dict(), sort_keys=True) if build_ref else payload.get("build")
        try:
            self.connection.execute("BEGIN IMMEDIATE")
            if self.head() != expected_previous:
                raise FlowError(6, "stale_head")
            cursor = self.connection.execute(
                "INSERT INTO events(previous_id,kind,command,request_id,operation_id,build_key,payload) "
                "VALUES(?,?,?,?,?,?,?)",
                (expected_previous, kind, context.name, request_id, operation_id, build_key,
                 json.dumps(payload, ensure_ascii=False, sort_keys=True)))
            self.connection.execute("COMMIT")
            return cursor.lastrowid
        except (sqlite3.Error, FlowError) as error:
            try:
                if self.connection.in_transaction:
                    self.connection.execute("ROLLBACK")
            except sqlite3.Error:
                raise FlowError(6, "corrupt") from None
            if isinstance(error, FlowError):
                raise
            raise FlowError(6, classify(error)) from None


def classify(error):
    code = getattr(error, 'sqlite_errorcode', 0) & 255
    # Python 3.10 does not expose sqlite_errorcode on every build.
    if code in {getattr(sqlite3, 'SQLITE_BUSY', 5), getattr(sqlite3, 'SQLITE_LOCKED', 6)} or str(error) in {'database is locked', 'database table is locked'}:
        return 'state_busy'
    if isinstance(error, sqlite3.IntegrityError):
        return 'stale_head' if str(error) == 'stale_head' else 'constraint'
    return 'corrupt'


def append_retry(store, context, kind, payload, expected, *, retry=False, **identifiers):
    for attempt in range(4):
        try:
            return store.append(context, kind, payload, expected, **identifiers)
        except FlowError as error:
            if not retry or attempt == 3 or error.reason not in {'stale_head', 'state_busy'}:
                raise
            new_head = store.head()
            intervening = store.events(after=expected)
            if any(e['payload'].get('build') == payload.get('build') or
                   COMMANDS.get(e['command']) in {Category.HUMAN, Category.EXTERNAL} for e in intervening):
                raise
            expected = new_head
