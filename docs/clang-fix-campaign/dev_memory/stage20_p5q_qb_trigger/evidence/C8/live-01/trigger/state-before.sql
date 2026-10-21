BEGIN TRANSACTION;
CREATE TABLE campaign_change_ids (
  submission_key TEXT NOT NULL PRIMARY KEY
                 CHECK (length(submission_key) = 64
                        AND submission_key NOT GLOB '*[^0-9a-f]*'),
  change_id      TEXT NOT NULL UNIQUE
                 CHECK (length(change_id) = 41
                        AND substr(change_id, 1, 1) = 'I'
                        AND substr(change_id, 2) NOT GLOB '*[^0-9a-f]*'),
  source         TEXT NOT NULL CHECK (source = 'commit_msg_hook'),
  hook_sha256    TEXT NOT NULL
                 CHECK (length(hook_sha256) = 64
                        AND hook_sha256 NOT GLOB '*[^0-9a-f]*'),
  created_at     TEXT NOT NULL
);
CREATE TABLE campaign_gate_events (
  event_id            INTEGER PRIMARY KEY AUTOINCREMENT,
  campaign_unit_key   TEXT NOT NULL,
  round_index         INTEGER,
  arch_norm           TEXT,
  verdict             TEXT,
  invocation_event_id INTEGER,
  event_type          TEXT NOT NULL,
  payload_json        TEXT NOT NULL,
  created_at          TEXT NOT NULL,
  FOREIGN KEY (campaign_unit_key) REFERENCES campaign_units (campaign_unit_key)
);
INSERT INTO "campaign_gate_events" VALUES(1,'p5q-c8-libtirpc-20261021',NULL,NULL,NULL,NULL,'DERIVE','{"author_date":"2026-10-21T09:01:33Z","author_identity":"C8 Synthetic Fixture <p5q-c8@example.invalid>","committer_date":"2026-10-21T09:01:33Z","committer_identity":"C8 Synthetic Fixture <p5q-c8@example.invalid>","derived_commit_sha":"7623cb042a74f4dfb2d3fe0dc4db0cf3863dd3f0","message_brief":"SYNTHETIC C6-01/C8: reuse fetched commit; no derive executed","verified_tree_sha":"9ef054c6187444dedb07aab80fb04279f5683bf4"}','2026-10-21T09:01:35.899542+00:00');
INSERT INTO "campaign_gate_events" VALUES(2,'p5q-c8-libtirpc-20261021',NULL,NULL,NULL,NULL,'PUSH','{"at":"2026-10-21T09:01:33Z","pushed_sha":"7623cb042a74f4dfb2d3fe0dc4db0cf3863dd3f0","ref":"refs/heads/sandbox/p5q-c8-libtirpc","ref_class":"sandbox","result":"ok","url":null}','2026-10-21T09:01:36.033486+00:00');
CREATE TABLE campaign_qb_events (
  event_id              INTEGER PRIMARY KEY AUTOINCREMENT,
  request_seq           INTEGER NOT NULL,
  event_type            TEXT NOT NULL
                        CHECK (event_type IN ('SUBMITTED','BUILD_BOUND','RESULT')),
  qb_build_id           TEXT,
  status                TEXT,
  accepted              INTEGER,
  sbs_target_echo       TEXT,
  per_arch_status_json  TEXT,
  qb_result_sha256      TEXT,
  qb_result_ref         TEXT,
  degraded              INTEGER NOT NULL DEFAULT 0,
  created_at            TEXT NOT NULL,
  FOREIGN KEY (request_seq) REFERENCES campaign_qb_requests (request_seq)
);
CREATE TABLE campaign_qb_profiles (
  branch          TEXT NOT NULL PRIMARY KEY,   -- campaign_units.branch
  profile_json    TEXT NOT NULL,               -- 规范化 JSON(键排序、紧凑分隔符、ensure_ascii=False)
  profile_sha256  TEXT NOT NULL
                  CHECK (length(profile_sha256) = 64
                         AND profile_sha256 NOT GLOB '*[^0-9a-f]*'),
  created_at      TEXT NOT NULL
);
CREATE TABLE campaign_qb_requests (
  request_seq       INTEGER PRIMARY KEY AUTOINCREMENT,
  request_id        TEXT NOT NULL UNIQUE,
  campaign_unit_key TEXT NOT NULL,
  sbs_target        TEXT NOT NULL,
  created_at        TEXT NOT NULL,
  FOREIGN KEY (campaign_unit_key) REFERENCES campaign_units (campaign_unit_key)
);
CREATE TABLE campaign_rounds (
  campaign_unit_key TEXT NOT NULL,
  round_index       INTEGER NOT NULL CHECK (round_index >= 1),
  edit_spec_ref     TEXT NOT NULL,
  edit_spec_sha256  TEXT NOT NULL,
  created_at        TEXT NOT NULL,
  PRIMARY KEY (campaign_unit_key, round_index),
  UNIQUE (campaign_unit_key, edit_spec_sha256),
  UNIQUE (campaign_unit_key, round_index, edit_spec_sha256),
  FOREIGN KEY (campaign_unit_key) REFERENCES campaign_units (campaign_unit_key)
);
INSERT INTO "campaign_rounds" VALUES('p5q-c8-libtirpc-20261021',1,'/home/linhao/Toolchain/development/LogAnalysisSkill/synthetic:C6-01/C8','eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee','2026-10-21T09:01:35.051076+00:00');
CREATE TABLE campaign_status_log (
  log_id            INTEGER PRIMARY KEY AUTOINCREMENT,
  campaign_unit_key TEXT NOT NULL,
  status            TEXT NOT NULL,
  reason            TEXT,
  arch_norm         TEXT,
  created_at        TEXT NOT NULL,
  FOREIGN KEY (campaign_unit_key) REFERENCES campaign_units (campaign_unit_key)
);
INSERT INTO "campaign_status_log" VALUES(1,'p5q-c8-libtirpc-20261021','SANDBOX_PUSHED',NULL,NULL,'2026-10-21T09:01:36.165973+00:00');
CREATE TABLE campaign_units (
  campaign_unit_key        TEXT PRIMARY KEY,
  ci_system                TEXT NOT NULL,
  source_build_id          TEXT NOT NULL,
  project                  TEXT NOT NULL,
  branch                   TEXT NOT NULL,
  spec_name                TEXT NOT NULL,
  base_commit              TEXT NOT NULL,
  submission_identity_key  TEXT NOT NULL,
  toolchain_profile        TEXT NOT NULL,
  ci_evidence_ref          TEXT,
  ci_evidence_sha256       TEXT,
  primary_arch             TEXT,
  max_rounds               INTEGER NOT NULL CHECK (max_rounds >= 1),
  max_build_invocations    INTEGER NOT NULL CHECK (max_build_invocations >= 1),
  failed_arches            TEXT NOT NULL,
  created_at               TEXT NOT NULL,
  schema_version           TEXT NOT NULL,
  CHECK (
    (primary_arch IS NULL AND ci_evidence_ref IS NULL
      AND ci_evidence_sha256 IS NULL)
    OR
    (primary_arch IS NOT NULL AND ci_evidence_ref IS NOT NULL
      AND ci_evidence_sha256 IS NOT NULL)
  )
);
INSERT INTO "campaign_units" VALUES('p5q-c8-libtirpc-20261021','quickbuild','1','platform/upstream/libtirpc','tizen_base','libtirpc','7623cb042a74f4dfb2d3fe0dc4db0cf3863dd3f0','p5q-c8-libtirpc-20261021','clang','/home/linhao/Toolchain/development/LogAnalysisSkill/docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C8/preparation/synthetic-basis.json','b996028b53b84eacf326cfd142347aa3011883f164d925d26702f45100e12574','standard-aarch64',3,9,'["standard-aarch64"]','2026-10-21T09:01:34.940739+00:00','campaign/v1');
CREATE TABLE campaign_verifications (
  link_id                 INTEGER PRIMARY KEY AUTOINCREMENT,
  campaign_unit_key       TEXT NOT NULL,
  arch_raw                TEXT NOT NULL,
  arch_norm               TEXT NOT NULL,
  verification_id         TEXT NOT NULL UNIQUE,
  round_index             INTEGER NOT NULL,
  edit_spec_sha256        TEXT NOT NULL,
  campaign_schema_version TEXT NOT NULL,
  created_at              TEXT NOT NULL,
  UNIQUE (campaign_unit_key, arch_norm, round_index),
  FOREIGN KEY (campaign_unit_key, round_index, edit_spec_sha256)
    REFERENCES campaign_rounds (campaign_unit_key, round_index, edit_spec_sha256),
  FOREIGN KEY (campaign_unit_key) REFERENCES campaign_units (campaign_unit_key),
  FOREIGN KEY (verification_id) REFERENCES verification_records (verification_id)
);
INSERT INTO "campaign_verifications" VALUES(1,'p5q-c8-libtirpc-20261021','standard-aarch64','aarch64','p5q-c8-libtirpc-20261021-v0',1,'eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee','campaign/v1','2026-10-21T09:01:33Z');
INSERT INTO "campaign_verifications" VALUES(2,'p5q-c8-libtirpc-20261021','standard-armv7l','armv7l','p5q-c8-libtirpc-20261021-v1',1,'eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee','campaign/v1','2026-10-21T09:01:33Z');
INSERT INTO "campaign_verifications" VALUES(3,'p5q-c8-libtirpc-20261021','standard-x86_64','x86_64','p5q-c8-libtirpc-20261021-v2',1,'eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee','campaign/v1','2026-10-21T09:01:33Z');
CREATE TABLE submissions (
            submission_key TEXT PRIMARY KEY,
            verification_id TEXT NOT NULL,
            submitted_at TEXT NOT NULL,
            action TEXT NOT NULL,
            gerrit_change_id TEXT,
            FOREIGN KEY (verification_id) REFERENCES verification_records (verification_id)
        );
CREATE TABLE unit_status_log (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit_key TEXT NOT NULL,
            status TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            verification_id TEXT,
            reason TEXT,
            FOREIGN KEY (verification_id) REFERENCES verification_records (verification_id)
        );
INSERT INTO "unit_status_log" VALUES(1,'p5q-c8-libtirpc-20261021-aarch64','GERRIT_READY','2026-10-21T09:01:35.155328+00:00','p5q-c8-libtirpc-20261021-v0','verification passed');
INSERT INTO "unit_status_log" VALUES(2,'p5q-c8-libtirpc-20261021-armv7l','GERRIT_READY','2026-10-21T09:01:35.406494+00:00','p5q-c8-libtirpc-20261021-v1','verification passed');
INSERT INTO "unit_status_log" VALUES(3,'p5q-c8-libtirpc-20261021-x86_64','GERRIT_READY','2026-10-21T09:01:35.656971+00:00','p5q-c8-libtirpc-20261021-v2','verification passed');
CREATE TABLE verification_records (
            verification_id TEXT PRIMARY KEY,
            result TEXT NOT NULL CHECK (result = 'PASS'),
            timestamp TEXT NOT NULL,
            failure_key TEXT NOT NULL,
            base_commit TEXT NOT NULL,
            verified_commit_sha TEXT NOT NULL,
            verified_tree_sha TEXT NOT NULL,
            canonical_diff_sha256 TEXT NOT NULL,
            patch_sha256 TEXT NOT NULL,
            edit_spec_sha256 TEXT NOT NULL,
            project TEXT NOT NULL,
            branch TEXT NOT NULL,
            spec_name TEXT NOT NULL,
            arch TEXT NOT NULL,
            gbs_conf_sha256 TEXT NOT NULL,
            build_log_sha256 TEXT NOT NULL,
            worktree_path TEXT NOT NULL,
            command_line TEXT NOT NULL
        );
INSERT INTO "verification_records" VALUES('p5q-c8-libtirpc-20261021-v0','PASS','2026-10-21T09:01:33Z','p5q-c8-libtirpc-20261021-aarch64','7623cb042a74f4dfb2d3fe0dc4db0cf3863dd3f0','7623cb042a74f4dfb2d3fe0dc4db0cf3863dd3f0','9ef054c6187444dedb07aab80fb04279f5683bf4','dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd','dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd','eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee','platform/upstream/libtirpc','tizen_base','libtirpc','standard-aarch64','ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff','bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb','/home/linhao/Toolchain/p5q-live-validation/p5q-c8/synthetic-not-built/aarch64','SYNTHETIC P5Q-C6-01/C8 fixture; no gbs build executed');
INSERT INTO "verification_records" VALUES('p5q-c8-libtirpc-20261021-v1','PASS','2026-10-21T09:01:33Z','p5q-c8-libtirpc-20261021-armv7l','7623cb042a74f4dfb2d3fe0dc4db0cf3863dd3f0','7623cb042a74f4dfb2d3fe0dc4db0cf3863dd3f0','9ef054c6187444dedb07aab80fb04279f5683bf4','dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd','dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd','eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee','platform/upstream/libtirpc','tizen_base','libtirpc','standard-armv7l','ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff','bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb','/home/linhao/Toolchain/p5q-live-validation/p5q-c8/synthetic-not-built/armv7l','SYNTHETIC P5Q-C6-01/C8 fixture; no gbs build executed');
INSERT INTO "verification_records" VALUES('p5q-c8-libtirpc-20261021-v2','PASS','2026-10-21T09:01:33Z','p5q-c8-libtirpc-20261021-x86_64','7623cb042a74f4dfb2d3fe0dc4db0cf3863dd3f0','7623cb042a74f4dfb2d3fe0dc4db0cf3863dd3f0','9ef054c6187444dedb07aab80fb04279f5683bf4','dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd','dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd','eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee','platform/upstream/libtirpc','tizen_base','libtirpc','standard-x86_64','ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff','bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb','/home/linhao/Toolchain/p5q-live-validation/p5q-c8/synthetic-not-built/x86_64','SYNTHETIC P5Q-C6-01/C8 fixture; no gbs build executed');
CREATE INDEX idx_unit_status_log_latest
            ON unit_status_log (unit_key, timestamp, log_id);
CREATE UNIQUE INDEX ux_convergence_per_invocation
  ON campaign_gate_events (invocation_event_id)
  WHERE event_type = 'CONVERGENCE' AND invocation_event_id IS NOT NULL;
CREATE INDEX ix_gate_unit_type
  ON campaign_gate_events (campaign_unit_key, event_type, event_id);
CREATE INDEX ix_status_unit
  ON campaign_status_log (campaign_unit_key, log_id);
CREATE INDEX ix_qb_req_unit
  ON campaign_qb_requests (campaign_unit_key, request_seq);
CREATE INDEX ix_qb_ev_req
  ON campaign_qb_events (request_seq, event_id);
CREATE INDEX ix_qb_ev_build
  ON campaign_qb_events (qb_build_id);
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('unit_status_log',3);
INSERT INTO "sqlite_sequence" VALUES('campaign_verifications',3);
INSERT INTO "sqlite_sequence" VALUES('campaign_gate_events',2);
INSERT INTO "sqlite_sequence" VALUES('campaign_status_log',1);
COMMIT;
