import json

import pytest

from modric_cli.__main__ import main


def run(server, argv, capsys):
    rc = main(argv)
    out = capsys.readouterr().out
    return rc, out


def test_scripts_list_json(server, capsys):
    server.route("GET", "/api/scripts", [{"script_id": "s1", "path": "a.sh", "script_type": 3}])
    rc, out = run(server, ["scripts", "list"], capsys)
    assert rc == 0
    assert json.loads(out)[0]["path"] == "a.sh"
    assert server.calls[-1]["headers"].get("X-api-token") == "tok-123"


def test_scripts_create_sends_content(server, capsys, tmp_path):
    f = tmp_path / "x.sh"
    f.write_text("echo hi\n")
    server.route("POST", "/api/scripts", {"script_id": "s2", "path": "x.sh"})
    rc, _ = run(server, ["scripts", "create", "--path", "x.sh", "--file", str(f), "--type", "3"],
                capsys)
    assert rc == 0
    body = server.calls[-1]["body"]
    assert body["path"] == "x.sh" and body["content"] == "echo hi\n" and body["script_type"] == 3


def test_jobs_logs_returns_text(server, capsys):
    server.route("GET", "/api/jobs/j1/tasks/2/log", "line1\nERROR boom\n")
    rc, out = run(server, ["jobs", "logs", "j1", "--step", "2"], capsys)
    assert rc == 0 and "ERROR boom" in out


def test_configmaps_update_preserves_secrets(server, capsys):
    # Current map: one non-secret key + one masked secret (value="").
    server.route("GET", "/api/configmaps", [{
        "config_map_id": "cm1", "name": "creds", "description": "",
        "entries": [{"key": "USER", "value": "alice", "sensitive": False, "has_value": True},
                    {"key": "TOKEN", "value": "", "sensitive": True, "has_value": True}]}])
    server.route("PUT", "/api/configmaps/cm1", {"ok": True})
    rc, _ = run(server, ["configmaps", "update", "creds", "--key", "USER=bob"], capsys)
    assert rc == 0
    entries = {e["key"]: e for e in server.calls[-1]["body"]["entries"]}
    assert entries["USER"]["value"] == "bob"                 # updated
    assert entries["TOKEN"]["sensitive"] and entries["TOKEN"]["value"] == ""  # secret preserved


def test_error_surfaces_server_detail(server, capsys):
    server.route("GET", "/api/scripts/nope", {"detail": "script not found"}, status=404)
    with pytest.raises(SystemExit) as exc:
        main(["scripts", "get", "nope"])
    assert exc.value.code == 1
    assert "script not found" in capsys.readouterr().err


def test_delete_requires_yes_when_noninteractive(server, capsys):
    with pytest.raises(SystemExit) as exc:
        main(["scripts", "delete", "s1"])
    assert exc.value.code == 1
    assert "without --yes" in capsys.readouterr().err
    assert not any(c["method"] == "DELETE" for c in server.calls)


def test_delete_with_yes(server, capsys):
    server.route("DELETE", "/api/scripts/s1", None, status=204)
    rc, out = run(server, ["scripts", "delete", "s1", "--yes"], capsys)
    assert rc == 0 and json.loads(out)["deleted"] is True
    assert server.calls[-1]["method"] == "DELETE"


def test_scripts_search_path_and_content_with_context(server, capsys):
    server.route("GET", "/api/scripts", [
        {"script_id": "s1", "path": "deploy/aba.sh", "script_type": 3},
        {"script_id": "s2", "path": "other.sh", "script_type": 3}])
    server.route("GET", "/api/scripts/s1",
                 {"script_id": "s1", "path": "deploy/aba.sh",
                  "content": "echo one\necho MATCH here\necho three\n"})
    server.route("GET", "/api/scripts/s2",
                 {"script_id": "s2", "path": "other.sh", "content": "nope\n"})
    rc, out = run(server, ["scripts", "search", "MATCH", "--content", "-B", "1", "-A", "1"], capsys)
    res = json.loads(out)
    hits = [r for r in res["results"] if r["field"] == "content"]
    assert len(hits) == 1
    assert "MATCH here" in hits[0]["snippet"] and "echo one" in hits[0]["snippet"]


def test_jobs_search_logs_across_steps_with_context(server, capsys):
    server.route("GET", "/api/jobs/j1", {"job_id": "j1", "tasks": [{"name": "a"}, {"name": "b"}]})
    server.route("GET", "/api/jobs/j1/tasks/0/log", "ok\nok2\n")
    server.route("GET", "/api/jobs/j1/tasks/1/log", "before\nERROR boom\nafter\n")
    rc, out = run(server, ["jobs", "search-logs", "j1", "ERROR", "-B", "1", "-A", "1"], capsys)
    res = json.loads(out)
    assert res["returned"] == 1 and res["results"][0]["step"] == 1
    assert "ERROR boom" in res["results"][0]["snippet"]
    assert "before" in res["results"][0]["snippet"]


def test_configmaps_search_matches_key_not_value(server, capsys):
    server.route("GET", "/api/configmaps", [{
        "config_map_id": "cm1", "name": "creds", "description": "prod",
        "entries": [{"key": "API_TOKEN", "value": "", "sensitive": True, "has_value": True}]}])
    rc, out = run(server, ["configmaps", "search", "TOKEN"], capsys)
    res = json.loads(out)
    assert any(r["field"] == "key" and r["snippet"] == "API_TOKEN" for r in res["results"])


def test_upgrade_check_reports_newer(server, capsys):
    server.route("GET", "/repos/mangosteen-lab/modric-cli/releases/latest", {"tag_name": "v9.9.9"})
    rc, out = run(server, ["upgrade", "--check"], capsys)
    res = json.loads(out)
    assert rc == 0 and res["latest"] == "9.9.9" and res["upgrade_available"] is True


def test_upgrade_noop_when_current_is_latest(server, capsys):
    from modric_cli import __version__
    server.route("GET", "/repos/mangosteen-lab/modric-cli/releases/latest",
                 {"tag_name": "v" + __version__})
    rc, out = run(server, ["upgrade"], capsys)
    res = json.loads(out)
    assert res["upgraded"] is False and "up to date" in res["message"]


def test_auth_login_validates_and_saves(server, capsys):
    server.route("GET", "/api/auth/me", {"username": "alice", "email": "a@x.com"})
    rc, out = run(server, ["auth", "login", "--url", "https://modric.test", "--token", "tok-123"],
                  capsys)
    assert rc == 0 and json.loads(out)["username"] == "alice"
