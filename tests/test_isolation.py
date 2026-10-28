from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_no_old_project_operations_in_runtime():
    # Deliberately don't scan docs: old project appears in hard-denylist prose.
    p = list((ROOT / "api/flamingo_next_api").glob("*.py")) + list((ROOT / "web/app").glob("*.tsx")) + [ROOT / "compose.yaml"]
    blocked=("manhwa.nodepilot.dev","recap-studio-production.up.railway.app", "github.com/qwazi12/manhwa")
    for f in p:
        s=f.read_text()
        assert all(word not in s for word in blocked),f.name

def test_no_old_remote_or_secrets_committed():
    from subprocess import run
    p=run(["git","remote","-v"],cwd=ROOT,text=True,capture_output=True,check=True)
    assert "qwazi12/manhwa" not in p.stdout, "Forbidden old project remote"
    assert "recap-studio-production" not in p.stdout, "Forbidden old backend remote"
    assert not (ROOT/".env").exists()
    # Scan project files only; Python certifi ships public CA certificates.
    files = run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.splitlines()
    assert not any(name.endswith(".pem") for name in files)
