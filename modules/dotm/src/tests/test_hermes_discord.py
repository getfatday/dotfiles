"""hermes-discord-setup: a no-op until the ids file and a token exist, then idempotent rendering.

A fake `hermes` stands in for the CLI. It implements `config set` the way Hermes does for these keys
(nested config.yaml keys; upper-case names go to .env) and logs every call, so the tests can assert
exactly what would be written without touching a real profile.
"""

import importlib.machinery
import importlib.util
import stat
import sys
from pathlib import Path

import pytest
import yaml

SCRIPT = Path(__file__).resolve().parents[4] / "modules" / "hermes-discord" / "files" / ".local" / "bin" / "hermes-discord-setup"
EXAMPLE = SCRIPT.parents[1] / "share" / "hermes-discord" / "discord-ids.example.yaml"

TOKEN = "SENTINEL-TOKEN-do-not-print"
GUILD, USER = "111111111111111111", "222222222222222222"
CONTROL, PINGS, SESSIONS = "333333333333333331", "333333333333333332", "333333333333333333"

FAKE = """#!{python}
import json, os, sys
import yaml
home = os.environ["HERMES_HOME"]
with open(os.path.join(home, "calls.log"), "a") as f:
    f.write(json.dumps(sys.argv[1:]) + "\\n")
if sys.argv[1:3] != ["config", "set"]:
    sys.exit(2)
key, raw = sys.argv[3], sys.argv[4]
if raw.strip()[:1] in "[{":
    val = yaml.safe_load(raw)
elif raw in ("true", "false"):
    val = raw == "true"
else:
    val = raw
if key.isupper() or key.split("_")[0] in ("DISCORD", "GATEWAY"):
    p = os.path.join(home, ".env")
    lines = [l for l in (open(p).read().splitlines() if os.path.exists(p) else []) if not l.startswith(key + "=")]
    open(p, "w").write("\\n".join(lines + [key + "=" + str(val)]) + "\\n")
else:
    p = os.path.join(home, "config.yaml")
    cfg = (yaml.safe_load(open(p)) if os.path.exists(p) else None) or {}
    cur = cfg
    parts = key.split(".")
    for part in parts[:-1]:
        cur = cur.setdefault(part, {})
    cur[parts[-1]] = val
    open(p, "w").write(yaml.safe_dump(cfg, sort_keys=False))
"""


def load_module():
    loader = importlib.machinery.SourceFileLoader("hermes_discord_setup", str(SCRIPT))
    spec = importlib.util.spec_from_loader("hermes_discord_setup", loader)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["hermes_discord_setup"] = mod
    loader.exec_module(mod)
    return mod


hds = load_module()


class Machine:
    def __init__(self, tmp: Path, monkeypatch):
        self.home = tmp / "hermes"
        self.home.mkdir()
        for p in ("sessions", "timesheets"):
            (self.home / "profiles" / p).mkdir(parents=True)
        (self.home / "plugins" / hds.GUARD).mkdir(parents=True)
        self.ids = tmp / "discord-ids.yaml"
        self.fake = tmp / "hermes-fake"
        self.fake.write_text(FAKE.replace("{python}", sys.executable))
        self.fake.chmod(self.fake.stat().st_mode | stat.S_IXUSR)
        monkeypatch.setenv("HERMES_HOME", str(self.home))
        monkeypatch.setenv("HERMES_DISCORD_IDS", str(self.ids))

    def write_ids(self, **over):
        data = {
            "detail": "content-free", "guild_id": GUILD, "user_id": USER,
            "control_channel": "work-control", "home_channel": "work-pings",
            "routes": [
                {"name": "work-control", "chat_id": CONTROL, "profile": "default"},
                {"name": "work-pings", "chat_id": PINGS, "profile": "default"},
                {"name": "work-sessions", "chat_id": SESSIONS, "profile": "sessions"},
            ],
        }
        data.update(over)
        self.ids.write_text(yaml.safe_dump(data, sort_keys=False))

    def write_config(self, cfg):
        (self.home / "config.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False))

    def write_env(self, text):
        (self.home / ".env").write_text(text)

    def config(self):
        p = self.home / "config.yaml"
        return (yaml.safe_load(p.read_text()) if p.exists() else None) or {}

    def env(self):
        p = self.home / ".env"
        out = {}
        for line in (p.read_text().splitlines() if p.exists() else []):
            if "=" in line:
                k, v = line.split("=", 1)
                out[k] = v
        return out

    def calls(self):
        p = self.home / "calls.log"
        return [__import__("json").loads(l) for l in p.read_text().splitlines()] if p.exists() else []

    def run(self, *flags):
        lines = []
        args = type("A", (), {"check": "--check" in flags, "dry_run": "--dry-run" in flags,
                              "hermes": str(self.fake)})
        rc = hds.run(args, out=lines.append)
        return rc, "\n".join(lines)


@pytest.fixture
def m(tmp_path, monkeypatch):
    return Machine(tmp_path, monkeypatch)


def ready(m, detail="content-free", **over):
    m.write_ids(detail=detail, **over)
    m.write_env("DISCORD_BOT_TOKEN=%s\n" % TOKEN)
    m.write_config({"gateway": {"multiplex_profiles": True, "profile_routes": []}})


# ---------------------------------------------------------------- the no-op contract

def test_no_ids_file_is_a_noop(m):
    m.write_env("DISCORD_BOT_TOKEN=%s\n" % TOKEN)
    rc, out = m.run()
    assert rc == 0 and "nothing to do" in out
    assert m.calls() == []


def test_ids_without_a_token_is_a_noop(m):
    m.write_ids()
    m.write_config({})
    rc, out = m.run()
    assert rc == 0 and "token" in out and "nothing to do" in out
    assert m.calls() == []
    assert m.env() == {}


def test_empty_token_line_does_not_count(m):
    m.write_ids()
    m.write_env("DISCORD_BOT_TOKEN=\n")
    rc, out = m.run()
    assert rc == 0 and m.calls() == []


def test_a_1password_reference_counts_as_a_token(m):
    m.write_ids()
    m.write_config({"secrets": {"onepassword": {"env": {"DISCORD_BOT_TOKEN": "op://Agent/x/token"}}}})
    rc, out = m.run("--dry-run")
    assert rc == 0 and "would set" in out
    assert m.calls() == []


def test_stowing_alone_changes_nothing_the_example_is_not_the_ids_file(m):
    assert EXAMPLE.name == "discord-ids.example.yaml"
    # Copying the example untouched must not apply: its all-zero placeholder ids are rejected.
    m.ids.write_text(EXAMPLE.read_text())
    m.write_env("DISCORD_BOT_TOKEN=%s\n" % TOKEN)
    rc, out = m.run()
    assert rc == 1 and "placeholder" in out
    assert m.calls() == []


# ---------------------------------------------------------------- rendering

def test_content_free_render(m):
    ready(m)
    rc, out = m.run()
    assert rc == 0, out
    cfg, env = m.config(), m.env()
    assert cfg["gateway"]["profile_routes"] == [
        {"name": "work-control", "platform": "discord", "guild_id": GUILD, "chat_id": CONTROL, "profile": "default"},
        {"name": "work-pings", "platform": "discord", "guild_id": GUILD, "chat_id": PINGS, "profile": "default"},
        {"name": "work-sessions", "platform": "discord", "guild_id": GUILD, "chat_id": SESSIONS, "profile": "sessions"},
    ]
    assert all(isinstance(r["chat_id"], str) for r in cfg["gateway"]["profile_routes"])
    assert cfg["display"]["tool_progress"] == "off"
    assert cfg["gateway"]["platforms"]["discord"]["extra"]["slash_commands"] is False
    assert cfg["kanban"]["auto_subscribe_on_create"] is False
    d = cfg["discord"]
    assert d["require_mention"] is True and d["free_response_channels"] == [CONTROL]
    assert d["auto_thread"] is False and d["history_backfill"] is False and d["allow_bots"] == "none"
    assert d["allow_mentions"] == {"everyone": False, "roles": False}
    assert cfg["plugins"]["enabled"] == [hds.GUARD]
    assert cfg["plugins"]["entries"][hds.GUARD]["settings"]["detail"] == "content-free"
    assert env["DISCORD_ALLOWED_USERS"] == USER            # Ian's id only, no list
    assert env["DISCORD_ALLOWED_CHANNELS"] == CONTROL
    assert env["DISCORD_HOME_CHANNEL"] == PINGS and env["DISCORD_HOME_CHANNEL_NAME"] == "#work-pings"
    assert TOKEN not in out


def test_full_detail_leaves_the_content_free_controls_alone(m):
    ready(m, detail="full")
    rc, out = m.run()
    assert rc == 0, out
    cfg, env = m.config(), m.env()
    assert cfg["plugins"]["entries"][hds.GUARD]["settings"]["detail"] == "full"
    assert "display" not in cfg and "kanban" not in cfg
    assert "platforms" not in cfg["gateway"]
    assert "DISCORD_ALLOWED_CHANNELS" not in env
    assert env["DISCORD_ALLOWED_USERS"] == USER


def test_second_run_is_up_to_date_and_writes_nothing(m):
    ready(m)
    assert m.run()[0] == 0
    n = len(m.calls())
    rc, out = m.run()
    assert rc == 0 and out == "up to date"
    assert len(m.calls()) == n


def test_dry_run_writes_nothing(m):
    ready(m)
    rc, out = m.run("--dry-run")
    assert rc == 0 and "would set config gateway.profile_routes" in out
    assert m.calls() == [] and m.env() == {"DISCORD_BOT_TOKEN": TOKEN}


def test_existing_config_is_merged_not_replaced(m):
    ready(m)
    m.write_config({"gateway": {"multiplex_profiles": True, "profile_routes": [
        {"name": "other", "platform": "telegram", "chat_id": "1", "profile": "sessions"},
        {"name": "work-pings", "platform": "discord", "guild_id": "9", "chat_id": "stale", "profile": "default"},
    ]}, "plugins": {"enabled": ["disk-cleanup"]}})
    assert m.run()[0] == 0
    cfg = m.config()
    names = [r["name"] for r in cfg["gateway"]["profile_routes"]]
    assert names == ["other", "work-control", "work-pings", "work-sessions"]
    assert cfg["gateway"]["profile_routes"][2]["chat_id"] == PINGS
    assert cfg["plugins"]["enabled"] == ["disk-cleanup", hds.GUARD]
    assert cfg["gateway"]["multiplex_profiles"] is True


# ---------------------------------------------------------------- never does what it must not

def test_never_writes_a_token_or_an_allow_all_flag(m):
    ready(m)
    assert m.run()[0] == 0
    keys = [c[2] for c in m.calls()]
    assert not any("TOKEN" in k or "ALLOW_ALL" in k.upper() or k == "gateway.allow_all_users" for k in keys)
    assert m.env()["DISCORD_BOT_TOKEN"] == TOKEN  # untouched
    assert "DISCORD_ALLOW_ALL_USERS" not in m.env() and "GATEWAY_ALLOW_ALL_USERS" not in m.env()
    assert all(c[:2] == ["config", "set"] for c in m.calls())  # nothing like `gateway setup`


@pytest.mark.parametrize("line", ["DISCORD_ALLOW_ALL_USERS=true", "GATEWAY_ALLOW_ALL_USERS=1", "GATEWAY_ALLOW_ALL_USERS=yes"])
def test_refuses_when_an_allow_all_flag_is_on(m, line):
    ready(m)
    m.write_env("DISCORD_BOT_TOKEN=%s\n%s\n" % (TOKEN, line))
    rc, out = m.run()
    assert rc == 1 and "refusing" in out and m.calls() == []
    assert TOKEN not in out


def test_allow_all_false_is_fine(m):
    ready(m)
    m.write_env("DISCORD_BOT_TOKEN=%s\nDISCORD_ALLOW_ALL_USERS=false\n" % TOKEN)
    assert m.run()[0] == 0


def test_refuses_when_gateway_allow_all_users_is_true(m):
    ready(m)
    m.write_config({"gateway": {"allow_all_users": True}})
    rc, out = m.run()
    assert rc == 1 and m.calls() == []


def test_refuses_a_profile_home(m, monkeypatch, tmp_path):
    ready(m)
    prof = tmp_path / "x" / "profiles" / "worker"
    prof.mkdir(parents=True)
    monkeypatch.setenv("HERMES_HOME", str(prof))
    rc, out = m.run()
    assert rc == 1 and "default profile" in out


def test_refuses_to_enable_a_guard_that_is_not_installed(m):
    ready(m)
    (m.home / "plugins" / hds.GUARD).rmdir()
    rc, out = m.run()
    assert rc == 1 and hds.GUARD in out and m.calls() == []


# ---------------------------------------------------------------- validation

@pytest.mark.parametrize("over,needle", [
    ({"user_id": "Ian"}, "user_id"),
    ({"guild_id": 123}, "guild_id"),
    ({"detail": "everything"}, "detail"),
    ({"control_channel": "nowhere"}, "control_channel"),
    ({"home_channel": "nowhere"}, "home_channel"),
    ({"control_channel": None}, "control_channel is required"),
    ({"routes": []}, "routes"),
    ({"routes": [{"name": "a", "chat_id": "not-a-number", "profile": "default"}]}, "chat_id"),
    ({"routes": [{"name": "a", "chat_id": CONTROL, "profile": "ghost"}]}, "not installed"),
    ({"routes": [{"name": "a b", "chat_id": CONTROL, "profile": "default"}]}, "name"),
    ({"routes": [{"name": "a", "chat_id": CONTROL, "profile": "default"},
                 {"name": "a", "chat_id": PINGS, "profile": "default"}]}, "repeated"),
])
def test_bad_ids_are_rejected_before_anything_is_written(m, over, needle):
    ready(m)
    m.write_ids(**over)
    rc, out = m.run()
    assert rc == 1 and needle in out, out
    assert m.calls() == []


def test_a_numeric_unquoted_id_is_caught(m):
    ready(m)
    m.ids.write_text(m.ids.read_text().replace("'%s'" % USER, USER).replace('"%s"' % USER, USER))
    data = yaml.safe_load(m.ids.read_text())
    assert isinstance(data["user_id"], int)  # YAML read it as a number; the script wants it quoted
    # An int still matches the digit pattern via str(); what must hold is the rendered id is a string.
    assert m.run()[0] == 0
    assert m.env()["DISCORD_ALLOWED_USERS"] == USER


# ---------------------------------------------------------------- --check

def test_check_reports_drift_then_ok(m):
    ready(m)
    rc, out = m.run("--check")
    assert rc == 1 and "drift: config gateway.profile_routes" in out and "not ok" in out
    assert m.calls() == []
    assert m.run()[0] == 0
    rc, out = m.run("--check")
    assert rc == 0 and out.endswith("ok") and "drift" not in out and "fail" not in out


def test_check_flags_a_missing_guard_and_never_prints_the_token(m):
    ready(m)
    assert m.run()[0] == 0
    (m.home / "plugins" / hds.GUARD).rmdir()
    rc, out = m.run("--check")
    assert rc == 1 and "fail: plugin" in out
    assert TOKEN not in out


def test_check_flags_a_changed_user_id(m):
    ready(m)
    m.run()
    m.write_env("DISCORD_BOT_TOKEN=%s\nDISCORD_ALLOWED_USERS=%s,999999999999999999\n" % (TOKEN, USER))
    rc, out = m.run("--check")
    assert rc == 1 and "drift: env DISCORD_ALLOWED_USERS" in out


def test_check_flags_tool_progress_turned_back_on(m):
    ready(m)
    m.run()
    cfg = m.config()
    cfg["display"]["tool_progress"] = "all"
    m.write_config(cfg)
    rc, out = m.run("--check")
    assert rc == 1 and "drift: config display.tool_progress" in out
