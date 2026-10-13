import subprocess

import pytest

import autoversion


def git(*args, cwd):
    """Run git in a temp repo, failing the test on any git error."""
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    )


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "repo"
    r.mkdir()
    git("init", "-q", cwd=r)
    git("config", "user.email", "test@example.com", cwd=r)
    git("config", "user.name", "Test", cwd=r)
    return r


def write_manifest(mod, version):
    (mod / "__manifest__.py").write_text(
        f'{{\n    "name": "demo",\n    "version": "{version}",\n}}\n'
    )


def make_module(repo, name="demo", version="15.0.1.0.0"):
    mod = repo / "addons" / name
    mod.mkdir(parents=True)
    write_manifest(mod, version)
    return mod


def commit_all(repo, message="init"):
    git("add", ".", cwd=repo)
    git("commit", "-q", "-m", message, cwd=repo)


# --- blocking cases -------------------------------------------------------


def test_py_change_without_bump_blocks(repo, monkeypatch):
    monkeypatch.chdir(repo)
    mod = make_module(repo)
    (mod / "models").mkdir()
    (mod / "models" / "__init__.py").write_text("")
    commit_all(repo)

    (mod / "models" / "model.py").write_text("x = 1\n")
    git("add", ".", cwd=repo)

    assert autoversion.main() == 1


def test_xml_change_without_bump_blocks(repo, monkeypatch):
    monkeypatch.chdir(repo)
    mod = make_module(repo)
    commit_all(repo)

    (mod / "views").mkdir()
    (mod / "views" / "view.xml").write_text("<odoo/>\n")
    git("add", ".", cwd=repo)

    assert autoversion.main() == 1


def test_downgrade_blocked(repo, monkeypatch):
    monkeypatch.chdir(repo)
    mod = make_module(repo, version="15.0.1.0.0")
    commit_all(repo)

    (mod / "model.py").write_text("x = 1\n")
    write_manifest(mod, "15.0.0.9.0")
    git("add", ".", cwd=repo)

    assert autoversion.main() == 1


def test_same_version_blocked(repo, monkeypatch):
    monkeypatch.chdir(repo)
    mod = make_module(repo, version="15.0.1.0.0")
    commit_all(repo)

    (mod / "model.py").write_text("x = 1\n")
    write_manifest(mod, "15.0.1.0.0")  # bumped to itself
    git("add", ".", cwd=repo)

    assert autoversion.main() == 1


def test_non_numeric_version_blocked(repo, monkeypatch):
    monkeypatch.chdir(repo)
    mod = make_module(repo, version="15.0.1.0.0")
    commit_all(repo)

    (mod / "model.py").write_text("x = 1\n")
    write_manifest(mod, "15.0.1.0.rc1")
    git("add", ".", cwd=repo)

    assert autoversion.main() == 1


def test_short_version_blocked(repo, monkeypatch):
    monkeypatch.chdir(repo)
    mod = make_module(repo, version="15.0.0.9.0")
    commit_all(repo)

    (mod / "model.py").write_text("x = 1\n")
    write_manifest(mod, "15.0.1")  # 3 segments: invalid format
    git("add", ".", cwd=repo)

    assert autoversion.main() == 1


def test_long_version_blocked(repo, monkeypatch):
    monkeypatch.chdir(repo)
    mod = make_module(repo, version="15.0.1.0.0")
    commit_all(repo)

    (mod / "model.py").write_text("x = 1\n")
    write_manifest(mod, "15.0.1.0.0.0")  # 6 segments: invalid format
    git("add", ".", cwd=repo)

    assert autoversion.main() == 1


def test_manifest_without_version_blocked(repo, monkeypatch):
    monkeypatch.chdir(repo)
    mod = make_module(repo)
    commit_all(repo)

    (mod / "model.py").write_text("x = 1\n")
    (mod / "__manifest__.py").write_text('{"name": "demo"}\n')
    git("add", ".", cwd=repo)

    assert autoversion.main() == 1


# --- passing cases --------------------------------------------------------


def test_py_change_with_bump_passes(repo, monkeypatch):
    monkeypatch.chdir(repo)
    mod = make_module(repo, version="15.0.1.0.0")
    commit_all(repo)

    (mod / "model.py").write_text("x = 1\n")
    write_manifest(mod, "15.0.1.0.1")
    git("add", ".", cwd=repo)

    assert autoversion.main() == 0


def test_new_module_passes(repo, monkeypatch):
    monkeypatch.chdir(repo)
    mod = make_module(repo, version="15.0.1.0.0")
    (mod / "model.py").write_text("x = 1\n")
    git("add", ".", cwd=repo)

    assert autoversion.main() == 0


def test_non_addons_file_ignored(repo, monkeypatch):
    monkeypatch.chdir(repo)
    (repo / "README.md").write_text("hi\n")
    git("add", ".", cwd=repo)

    assert autoversion.main() == 0


def test_loose_file_in_addons_ignored(repo, monkeypatch):
    monkeypatch.chdir(repo)
    (repo / "addons").mkdir()
    (repo / "addons" / "README.md").write_text("hi\n")
    git("add", ".", cwd=repo)

    assert autoversion.main() == 0


def test_series_change_warns_but_passes(repo, monkeypatch, capsys):
    monkeypatch.chdir(repo)
    mod = make_module(repo, version="16.0.1.0.0")
    commit_all(repo)

    (mod / "model.py").write_text("x = 1\n")
    write_manifest(mod, "17.0.0.0.0")
    git("add", ".", cwd=repo)

    code = autoversion.main()
    out = capsys.readouterr().out

    assert code == 0
    assert "series" in out.lower()
