"""Tests for dotm.security module."""

from pathlib import Path

from dotm.security import scan_file, scan_module


def test_detects_private_key(tmp_path):
    f = tmp_path / "key.pem"
    f.write_text("-----BEGIN RSA PRIVATE KEY-----\ndata\n-----END RSA PRIVATE KEY-----\n")
    findings = scan_file(f)
    assert len(findings) == 1
    assert findings[0][1] == "Private key"


def test_detects_aws_key(tmp_path):
    f = tmp_path / "config"
    f.write_text("aws_access_key_id = AKIAIOSFODNN7EXAMPLE\n")
    findings = scan_file(f)
    assert any("AWS" in name for _, name, _ in findings)


def test_detects_github_pat(tmp_path):
    f = tmp_path / "token"
    f.write_text("GITHUB_TOKEN=ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh1234\n")
    findings = scan_file(f)
    assert any("GitHub" in name for _, name, _ in findings)


def test_detects_openai_key(tmp_path):
    f = tmp_path / ".env"
    f.write_text("OPENAI_API_KEY=sk-abcdefghijklmnopqrstuvwxyz1234567890123456789012\n")
    findings = scan_file(f)
    assert any("OpenAI" in name for _, name, _ in findings)


def test_detects_api_key_pattern(tmp_path):
    f = tmp_path / "config.yml"
    f.write_text("api_key: abcdefghijklmnopqrstuvwxyz12345678\n")
    findings = scan_file(f)
    assert any("API key" in name for _, name, _ in findings)


def test_clean_file(tmp_path):
    f = tmp_path / ".gitconfig"
    f.write_text("[user]\n  name = Test User\n  email = test@example.com\n")
    findings = scan_file(f)
    assert findings == []


def test_skips_binary_files(tmp_path):
    f = tmp_path / "image.png"
    f.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
    findings = scan_file(f)
    assert findings == []


def test_scan_module(tmp_path):
    mod_dir = tmp_path / "test-module"
    mod_dir.mkdir()
    (mod_dir / "config.yml").write_text("name: test\n")
    (mod_dir / "secret.txt").write_text("-----BEGIN RSA PRIVATE KEY-----\ndata\n")
    findings = scan_module(mod_dir)
    assert len(findings) == 1
    assert findings[0][0] == mod_dir / "secret.txt"


def test_scan_module_clean(tmp_path):
    mod_dir = tmp_path / "clean-module"
    mod_dir.mkdir()
    (mod_dir / "config.yml").write_text("homebrew_packages:\n  - curl\n")
    findings = scan_module(mod_dir)
    assert findings == []
