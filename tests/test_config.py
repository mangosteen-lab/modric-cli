import os

from modric_cli import config


def test_save_load_resolve(tmp_path, monkeypatch):
    monkeypatch.setenv("MODRIC_CONFIG", str(tmp_path / "c.json"))
    monkeypatch.delenv("MODRIC_URL", raising=False)
    monkeypatch.delenv("MODRIC_TOKEN", raising=False)
    config.save("https://x.example/", "abc")
    assert config.load() == {"url": "https://x.example/", "token": "abc"}
    url, token = config.resolve()
    assert url == "https://x.example" and token == "abc"   # trailing slash trimmed
    if os.name != "nt":
        assert (os.stat(config.config_path()).st_mode & 0o777) == 0o600


def test_flag_and_env_precedence(tmp_path, monkeypatch):
    monkeypatch.setenv("MODRIC_CONFIG", str(tmp_path / "c.json"))
    config.save("https://file.example", "file-tok")
    monkeypatch.setenv("MODRIC_URL", "https://env.example")
    monkeypatch.setenv("MODRIC_TOKEN", "env-tok")
    assert config.resolve()[0] == "https://env.example"          # env beats file
    assert config.resolve("https://flag.example")[0] == "https://flag.example"  # flag beats env
    assert config.resolve(token_flag="flag-tok")[1] == "flag-tok"
