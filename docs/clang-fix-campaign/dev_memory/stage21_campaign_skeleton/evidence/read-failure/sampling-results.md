# Sampling Results

| Group | Runs | Pass | Fail | Skip | 1-min load range |
|---|---:|---:|---:|---:|---|
| regular-late | 50 | 47 | 3 | 0 | 1.17 .. 40.77 |
| regular-c8 | 20 | 19 | 1 | 0 | 0.47 .. 14.14 |
| stress-late | 0 | 0 | 0 | 0 | None .. None |
| setup-errors-late | 27 | 0 | 27 | 0 | 8.83 .. 14.57 |

Setup errors are wrapper failures before fixture execution, excluded from read-failure rates.
Each command.json preserves argv, UTC, load samples, exact assertion and fixed failure categories.

## Failed Executions

### regular-late / run-40

Evidence: `regular-late/run-40/command.json`

```json
{
  "group": "regular-late",
  "run": 40,
  "exit_code": 1,
  "file": "regular-late/run-40/command.json",
  "agent_stopped": [],
  "harness_failures": []
}
```

```text
tmp_path = PosixPath('/tmp/skel-read-failure-3af2f4ek/regular-late/run-40/test_real_cli_browser_submit_b0')
mode = 'late-build'

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "mode",
        ["build", "error-created", "error-no-build", "no-navigation", "delayed-build", "late-build"],
    )
    def test_real_cli_browser_submit_bind_pending_pass(tmp_path, mode):
        command, env = node_command()
        playwright, chromium = browser_paths()
        # Reuse state fixture only, not its fake-agent monkeypatch or CLI shortcuts.
        with pytest.MonkeyPatch.context() as mp:
            campaign = Campaign(tmp_path, mp)
        campaign.project["configuration_path"] = (
            "root/CI_TIZEN/TIZEN/Tizen/Tizen-Base-Toolchain/RBS/TRIGGER"
        )
        campaign.data["qb"]["browser"].update(
            node=str(ROOT / "tests/fixtures/p5q_node_entry.py"),
            playwright_module=playwright,
            chromium=chromium,
        )
        campaign.save()
        evidence = Path(os.environ.get("P5Q_C5A_EVIDENCE", str(tmp_path / "evidence"))) / mode
        evidence.mkdir(parents=True, exist_ok=True)
        config, received = tmp_path / "local-server.json", evidence / "server-requests.json"
        env.update(P5Q_TEST_SERVER=str(config), P5Q_TEST_NODE=json.dumps(command))
        server = subprocess.Popen(
            [*command, str(ROOT / "tests/node/p5q_fake_quickbuild.mjs"), str(config), str(received)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        commands = []
    
        def server_command(value):
            server.stdin.write(json.dumps(value) + "\n")
            server.stdin.flush()
            assert line(server) == {"ok": True}
    
        def cli(name, *args, expected_exit=0):
            env["P5Q_TEST_AGENT_LOG"] = str(evidence / f"agent-{len(commands)}.json")
            argv = [
                sys.executable,
                str(ROOT / "tests/fixtures/p5q_cli_clock.py"),
                name,
                *args,
                "--state-db",
                str(tmp_path / "state.db"),
                "--state-root",
                str(tmp_path / "state"),
                "--config",
                str(campaign.config),
            ]
            run = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, text=True, timeout=150)
            ended = time.time()
            agent_log = Path(env["P5Q_TEST_AGENT_LOG"])
            close_seconds = None
            if agent_log.exists():
                lifecycle = json.loads(agent_log.read_text())
                close_started = lifecycle["close_started_unix_ms"]
                if close_started is not None:
                    close_seconds = ended - close_started / 1000
            commands.append(
                {
                    "argv": argv,
                    "exit": run.returncode,
                    "stdout": run.stdout,
                    "stderr": run.stderr,
                    "close_to_cli_exit_seconds": close_seconds,
                }
            )
            (evidence / "commands.json").write_text(
                json.dumps(commands, ensure_ascii=False, indent=2) + "\n"
            )
            server_command({})
            if close_seconds is not None:
                assert 0 <= close_seconds < 5
            elif name == "qb-result-fetch" or not commands[:-1]:
                pytest.fail("missing close timing for browser invocation")
            assert run.returncode == expected_exit, run.stdout + run.stderr
            return json.loads(run.stdout)[0]
    
        try:
            assert line(server) == {"ready": True}
            server_command({"mode": mode})
>           triggered = cli(
                "qb-trigger",
                "--verification-ids",
                "u1-v0,u1-v1,u1-v2",
                expected_exit=5 if mode in {"error-no-build", "late-build"} else 0,
            )

tests/unit/test_p5q_c5a_integration.py:107: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

name = 'qb-trigger', expected_exit = 5
args = ('--verification-ids', 'u1-v0,u1-v1,u1-v2')
argv = ['/home/linhao/Toolchain/development/LogAnalysisSkill/.venv/bin/python', '/home/linhao/Toolchain/development/LogAnalysisSkill/tests/fixtures/p5q_cli_clock.py', 'qb-trigger', '--verification-ids', 'u1-v0,u1-v1,u1-v2', '--state-db', ...]
run = CompletedProcess(args=['/home/linhao/Toolchain/development/LogAnalysisSkill/.venv/bin/python', '/home/linhao/Toolchain...577d2979a51093d5", "status": "QB_REQUESTED"}]\n', stderr='已打开 QuickBuild 登录窗口,请在窗口中登录;若提示登录失败,可在窗口中重新输入;登录后工具会自动继续。\n')

    def cli(name, *args, expected_exit=0):
        env["P5Q_TEST_AGENT_LOG"] = str(evidence / f"agent-{len(commands)}.json")
        argv = [
            sys.executable,
            str(ROOT / "tests/fixtures/p5q_cli_clock.py"),
            name,
            *args,
            "--state-db",
            str(tmp_path / "state.db"),
            "--state-root",
            str(tmp_path / "state"),
            "--config",
            str(campaign.config),
        ]
        run = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, text=True, timeout=150)
        ended = time.time()
        agent_log = Path(env["P5Q_TEST_AGENT_LOG"])
        close_seconds = None
        if agent_log.exists():
            lifecycle = json.loads(agent_log.read_text())
            close_started = lifecycle["close_started_unix_ms"]
            if close_started is not None:
                close_seconds = ended - close_started / 1000
        commands.append(
            {
                "argv": argv,
                "exit": run.returncode,
                "stdout": run.stdout,
                "stderr": run.stderr,
                "close_to_cli_exit_seconds": close_seconds,
            }
        )
        (evidence / "commands.json").write_text(
            json.dumps(commands, ensure_ascii=False, indent=2) + "\n"
        )
        server_command({})
        if close_seconds is not None:
>           assert 0 <= close_seconds < 5
E           assert 5.487124443054199 < 5

tests/unit/test_p5q_c5a_integration.py:98: AssertionError
```

### regular-late / run-41

Evidence: `regular-late/run-41/command.json`

```json
{
  "group": "regular-late",
  "run": 41,
  "exit_code": 1,
  "file": "regular-late/run-41/command.json",
  "agent_stopped": [
    {
      "file": "c5a/late-build/agent-0.json",
      "facts": {
        "action": "AGENT_STOPPED",
        "failure_category": "UNKNOWN"
      }
    }
  ],
  "harness_failures": []
}
```

```text
tmp_path = PosixPath('/tmp/skel-read-failure-3af2f4ek/regular-late/run-41/test_real_cli_browser_submit_b0')
mode = 'late-build'

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "mode",
        ["build", "error-created", "error-no-build", "no-navigation", "delayed-build", "late-build"],
    )
    def test_real_cli_browser_submit_bind_pending_pass(tmp_path, mode):
        command, env = node_command()
        playwright, chromium = browser_paths()
        # Reuse state fixture only, not its fake-agent monkeypatch or CLI shortcuts.
        with pytest.MonkeyPatch.context() as mp:
            campaign = Campaign(tmp_path, mp)
        campaign.project["configuration_path"] = (
            "root/CI_TIZEN/TIZEN/Tizen/Tizen-Base-Toolchain/RBS/TRIGGER"
        )
        campaign.data["qb"]["browser"].update(
            node=str(ROOT / "tests/fixtures/p5q_node_entry.py"),
            playwright_module=playwright,
            chromium=chromium,
        )
        campaign.save()
        evidence = Path(os.environ.get("P5Q_C5A_EVIDENCE", str(tmp_path / "evidence"))) / mode
        evidence.mkdir(parents=True, exist_ok=True)
        config, received = tmp_path / "local-server.json", evidence / "server-requests.json"
        env.update(P5Q_TEST_SERVER=str(config), P5Q_TEST_NODE=json.dumps(command))
        server = subprocess.Popen(
            [*command, str(ROOT / "tests/node/p5q_fake_quickbuild.mjs"), str(config), str(received)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        commands = []
    
        def server_command(value):
            server.stdin.write(json.dumps(value) + "\n")
            server.stdin.flush()
            assert line(server) == {"ok": True}
    
        def cli(name, *args, expected_exit=0):
            env["P5Q_TEST_AGENT_LOG"] = str(evidence / f"agent-{len(commands)}.json")
            argv = [
                sys.executable,
                str(ROOT / "tests/fixtures/p5q_cli_clock.py"),
                name,
                *args,
                "--state-db",
                str(tmp_path / "state.db"),
                "--state-root",
                str(tmp_path / "state"),
                "--config",
                str(campaign.config),
            ]
            run = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, text=True, timeout=150)
            ended = time.time()
            agent_log = Path(env["P5Q_TEST_AGENT_LOG"])
            close_seconds = None
            if agent_log.exists():
                lifecycle = json.loads(agent_log.read_text())
                close_started = lifecycle["close_started_unix_ms"]
                if close_started is not None:
                    close_seconds = ended - close_started / 1000
            commands.append(
                {
                    "argv": argv,
                    "exit": run.returncode,
                    "stdout": run.stdout,
                    "stderr": run.stderr,
                    "close_to_cli_exit_seconds": close_seconds,
                }
            )
            (evidence / "commands.json").write_text(
                json.dumps(commands, ensure_ascii=False, indent=2) + "\n"
            )
            server_command({})
            if close_seconds is not None:
                assert 0 <= close_seconds < 5
            elif name == "qb-result-fetch" or not commands[:-1]:
                pytest.fail("missing close timing for browser invocation")
            assert run.returncode == expected_exit, run.stdout + run.stderr
            return json.loads(run.stdout)[0]
    
        try:
            assert line(server) == {"ready": True}
            server_command({"mode": mode})
>           triggered = cli(
                "qb-trigger",
                "--verification-ids",
                "u1-v0,u1-v1,u1-v2",
                expected_exit=5 if mode in {"error-no-build", "late-build"} else 0,
            )

tests/unit/test_p5q_c5a_integration.py:107: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

name = 'qb-trigger', expected_exit = 5
args = ('--verification-ids', 'u1-v0,u1-v1,u1-v2')
argv = ['/home/linhao/Toolchain/development/LogAnalysisSkill/.venv/bin/python', '/home/linhao/Toolchain/development/LogAnalysisSkill/tests/fixtures/p5q_cli_clock.py', 'qb-trigger', '--verification-ids', 'u1-v0,u1-v1,u1-v2', '--state-db', ...]
run = CompletedProcess(args=['/home/linhao/Toolchain/development/LogAnalysisSkill/.venv/bin/python', '/home/linhao/Toolchain..._FAILED"}]\n', stderr='已打开 QuickBuild 登录窗口,请在窗口中登录;若提示登录失败,可在窗口中重新输入;登录后工具会自动继续。\nQB_AGENT_STOPPED category=UNKNOWN\n')

    def cli(name, *args, expected_exit=0):
        env["P5Q_TEST_AGENT_LOG"] = str(evidence / f"agent-{len(commands)}.json")
        argv = [
            sys.executable,
            str(ROOT / "tests/fixtures/p5q_cli_clock.py"),
            name,
            *args,
            "--state-db",
            str(tmp_path / "state.db"),
            "--state-root",
            str(tmp_path / "state"),
            "--config",
            str(campaign.config),
        ]
        run = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, text=True, timeout=150)
        ended = time.time()
        agent_log = Path(env["P5Q_TEST_AGENT_LOG"])
        close_seconds = None
        if agent_log.exists():
            lifecycle = json.loads(agent_log.read_text())
            close_started = lifecycle["close_started_unix_ms"]
            if close_started is not None:
                close_seconds = ended - close_started / 1000
        commands.append(
            {
                "argv": argv,
                "exit": run.returncode,
                "stdout": run.stdout,
                "stderr": run.stderr,
                "close_to_cli_exit_seconds": close_seconds,
            }
        )
        (evidence / "commands.json").write_text(
            json.dumps(commands, ensure_ascii=False, indent=2) + "\n"
        )
        server_command({})
        if close_seconds is not None:
>           assert 0 <= close_seconds < 5
E           assert 13.619728326797485 < 5

tests/unit/test_p5q_c5a_integration.py:98: AssertionError
```

### regular-late / run-42

Evidence: `regular-late/run-42/command.json`

```json
{
  "group": "regular-late",
  "run": 42,
  "exit_code": 1,
  "file": "regular-late/run-42/command.json",
  "agent_stopped": [],
  "harness_failures": []
}
```

```text
tmp_path = PosixPath('/tmp/skel-read-failure-3af2f4ek/regular-late/run-42/test_real_cli_browser_submit_b0')
mode = 'late-build'

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "mode",
        ["build", "error-created", "error-no-build", "no-navigation", "delayed-build", "late-build"],
    )
    def test_real_cli_browser_submit_bind_pending_pass(tmp_path, mode):
        command, env = node_command()
        playwright, chromium = browser_paths()
        # Reuse state fixture only, not its fake-agent monkeypatch or CLI shortcuts.
        with pytest.MonkeyPatch.context() as mp:
            campaign = Campaign(tmp_path, mp)
        campaign.project["configuration_path"] = (
            "root/CI_TIZEN/TIZEN/Tizen/Tizen-Base-Toolchain/RBS/TRIGGER"
        )
        campaign.data["qb"]["browser"].update(
            node=str(ROOT / "tests/fixtures/p5q_node_entry.py"),
            playwright_module=playwright,
            chromium=chromium,
        )
        campaign.save()
        evidence = Path(os.environ.get("P5Q_C5A_EVIDENCE", str(tmp_path / "evidence"))) / mode
        evidence.mkdir(parents=True, exist_ok=True)
        config, received = tmp_path / "local-server.json", evidence / "server-requests.json"
        env.update(P5Q_TEST_SERVER=str(config), P5Q_TEST_NODE=json.dumps(command))
        server = subprocess.Popen(
            [*command, str(ROOT / "tests/node/p5q_fake_quickbuild.mjs"), str(config), str(received)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        commands = []
    
        def server_command(value):
            server.stdin.write(json.dumps(value) + "\n")
            server.stdin.flush()
            assert line(server) == {"ok": True}
    
        def cli(name, *args, expected_exit=0):
            env["P5Q_TEST_AGENT_LOG"] = str(evidence / f"agent-{len(commands)}.json")
            argv = [
                sys.executable,
                str(ROOT / "tests/fixtures/p5q_cli_clock.py"),
                name,
                *args,
                "--state-db",
                str(tmp_path / "state.db"),
                "--state-root",
                str(tmp_path / "state"),
                "--config",
                str(campaign.config),
            ]
            run = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, text=True, timeout=150)
            ended = time.time()
            agent_log = Path(env["P5Q_TEST_AGENT_LOG"])
            close_seconds = None
            if agent_log.exists():
                lifecycle = json.loads(agent_log.read_text())
                close_started = lifecycle["close_started_unix_ms"]
                if close_started is not None:
                    close_seconds = ended - close_started / 1000
            commands.append(
                {
                    "argv": argv,
                    "exit": run.returncode,
                    "stdout": run.stdout,
                    "stderr": run.stderr,
                    "close_to_cli_exit_seconds": close_seconds,
                }
            )
            (evidence / "commands.json").write_text(
                json.dumps(commands, ensure_ascii=False, indent=2) + "\n"
            )
            server_command({})
            if close_seconds is not None:
                assert 0 <= close_seconds < 5
            elif name == "qb-result-fetch" or not commands[:-1]:
                pytest.fail("missing close timing for browser invocation")
            assert run.returncode == expected_exit, run.stdout + run.stderr
            return json.loads(run.stdout)[0]
    
        try:
            assert line(server) == {"ready": True}
            server_command({"mode": mode})
>           triggered = cli(
                "qb-trigger",
                "--verification-ids",
                "u1-v0,u1-v1,u1-v2",
                expected_exit=5 if mode in {"error-no-build", "late-build"} else 0,
            )

tests/unit/test_p5q_c5a_integration.py:107: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/unit/test_p5q_c5a_integration.py:75: in cli
    run = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, text=True, timeout=150)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/lib/python3.12/subprocess.py:550: in run
    stdout, stderr = process.communicate(input, timeout=timeout)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/lib/python3.12/subprocess.py:1209: in communicate
    stdout, stderr = self._communicate(input, endtime, timeout)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/lib/python3.12/subprocess.py:2116: in _communicate
    self._check_timeout(endtime, orig_timeout, stdout, stderr)
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <Popen: returncode: -9 args: ['/home/linhao/Toolchain/development/LogAnalysi...>
endtime = 585026.88944954, orig_timeout = 150, stdout_seq = [], stderr_seq = []
skip_check_and_raise = False

    def _check_timeout(self, endtime, orig_timeout, stdout_seq, stderr_seq,
                       skip_check_and_raise=False):
        """Convenience for checking if a timeout has expired."""
        if endtime is None:
            return
        if skip_check_and_raise or _time() > endtime:
>           raise TimeoutExpired(
                    self.args, orig_timeout,
                    output=b''.join(stdout_seq) if stdout_seq else None,
                    stderr=b''.join(stderr_seq) if stderr_seq else None)
E           subprocess.TimeoutExpired: Command '['/home/linhao/Toolchain/development/LogAnalysisSkill/.venv/bin/python', '/home/linhao/Toolchain/development/LogAnalysisSkill/tests/fixtures/p5q_cli_clock.py', 'qb-trigger', '--verification-ids', 'u1-v0,u1-v1,u1-v2', '--state-db', '/tmp/skel-read-failure-3af2f4ek/regular-late/run-42/test_real_cli_browser_submit_b0/state.db', '--state-root', '/tmp/skel-read-failure-3af2f4ek/regular-late/run-42/test_real_cli_browser_submit_b0/state', '--config', '/tmp/skel-read-failure-3af2f4ek/regular-late/run-42/test_real_cli_browser_submit_b0/config.yaml']' timed out after 150 seconds

/usr/lib/python3.12/subprocess.py:1253: TimeoutExpired
```

### regular-c8 / run-15

Evidence: `regular-c8/run-15/command.json`

```json
{
  "group": "regular-c8",
  "run": 15,
  "exit_code": 1,
  "file": "regular-c8/run-15/command.json",
  "agent_stopped": [
    {
      "file": "c8/injected-missing-root-membership.json",
      "facts": {
        "action": "AGENT_STOPPED",
        "failure_category": "FETCH_CONTINUE_FAILED"
      }
    }
  ],
  "harness_failures": [
    {
      "file": "c8/injected-missing-root-membership.json",
      "case": "injected-missing-root-membership",
      "facts": {
        "class_name": "TargetClosedError",
        "agent_code": null,
        "category": "OTHER_FRAMEWORK_ERROR"
      }
    }
  ]
}
```

```text
tmp_path = PosixPath('/tmp/skel-read-failure-3af2f4ek/regular-c8/run-15/test_post_submit_read_signatur0')

    @pytest.mark.integration
    def test_post_submit_read_signatures(tmp_path: Path) -> None:
        node, env = node_command()
        paths = browser_paths()
        output = Path(os.environ.get("P5Q_C8_INVESTIGATION", str(tmp_path)))
        output.mkdir(parents=True, exist_ok=True)
        command = [*node, str(ROOT / "tests/node/p5q_c8_investigation.mjs"), *paths, str(output)]
        result = subprocess.run(command, env=env, text=True, capture_output=True, timeout=600)
        (output / "node.stdout.txt").write_text(result.stdout)
        (output / "node.stderr.txt").write_text(result.stderr)
>       assert result.returncode == 0, result.stdout + result.stderr
E       AssertionError: CASE_COMPLETE control
E         CASE_COMPLETE idle-script-navigation
E         CASE_COMPLETE racing-script-navigation
E         CASE_COMPLETE racing-meta-refresh
E         CASE_COMPLETE racing-wicket-navigation
E         已打开 QuickBuild 登录窗口,请在窗口中登录;若提示登录失败,可在窗口中重新输入;登录后工具会自动继续。
E         已打开 QuickBuild 登录窗口,请在窗口中登录;若提示登录失败,可在窗口中重新输入;登录后工具会自动继续。
E         已打开 QuickBuild 登录窗口,请在窗口中登录;若提示登录失败,可在窗口中重新输入;登录后工具会自动继续。
E         已打开 QuickBuild 登录窗口,请在窗口中登录;若提示登录失败,可在窗口中重新输入;登录后工具会自动继续。
E         已打开 QuickBuild 登录窗口,请在窗口中登录;若提示登录失败,可在窗口中重新输入;登录后工具会自动继续。
E         已打开 QuickBuild 登录窗口,请在窗口中登录;若提示登录失败,可在窗口中重新输入;登录后工具会自动继续。
E         QB_AGENT_STOPPED category=FETCH_CONTINUE_FAILED
E         INVESTIGATION_STOPPED AssertionError
E         
E       assert 1 == 0
E        +  where 1 = CompletedProcess(args=['/home/linhao/.local/bin/node', '/home/linhao/Toolchain/development/LogAnalysisSkill/tests/node...提示登录失败,可在窗口中重新输入;登录后工具会自动继续。\nQB_AGENT_STOPPED category=FETCH_CONTINUE_FAILED\nINVESTIGATION_STOPPED AssertionError\n').returncode

tests/unit/test_p5q_c8_investigation.py:26: AssertionError
```

### setup-errors-late / run-01

Evidence: `setup-errors-late/run-01/command.json`

```json
{
  "group": "setup-errors-late",
  "run": 1,
  "exit_code": 1,
  "file": "setup-errors-late/run-01/command.json",
  "agent_stopped": [],
  "harness_failures": []
}
```

```text
self = PosixPath('/tmp/skel-read-failure-o4ll2wot/regular-late/run-01')
mode = 448, parents = False, exist_ok = False

    def mkdir(self, mode=0o777, parents=False, exist_ok=False):
        """
        Create a new directory at this given path.
        """
        try:
>           os.mkdir(self, mode)
E           FileNotFoundError: [Errno 2] No such file or directory: '/tmp/skel-read-failure-o4ll2wot/regular-late/run-01'

/usr/lib/python3.12/pathlib.py:1313: FileNotFoundError
```
