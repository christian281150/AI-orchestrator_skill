from orchestrator import board
from conftest import sh

BOARD = """# Board

| ID | Item | Prio | Wave | Lane | Est h | Deps | Status | Owner | Next | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|
| W0-1 | Repo | P1 | 0 | infra | 4 | - | done | | | merged abc1234, 12 passed |
| W1-1 | Core loop | P1 | 1 | backend | 8 | W0-1 | open | | | |
| W1-2 | Nice extra | P2 | 1 | frontend | 2 | W0-1 | open | | | |
| W2-1 | Later thing | P3 | 2 | backend | 3 | W1-1 | open | | | |
| W2-2 | Parked | P3 | 2 | backend | 50 | - | parked | | | |

## Other table
| a | b |
|---|---|
"""


def write(tmp_path, text=BOARD):
    p = tmp_path / "PROGRESS.md"
    p.write_text(text)
    return p


def test_parse_and_validate_clean(tmp_path):
    rows = board.parse(write(tmp_path))
    assert [r.id for r in rows] == ["W0-1", "W1-1", "W1-2", "W2-1", "W2-2"]
    assert rows[1].deps == ["W0-1"] and rows[0].est == 4
    assert board.validate(rows, r"^(W\d+-\d+|F\d+)$") == []


def test_validate_goes_red(tmp_path):
    bad = BOARD.replace("| merged abc1234, 12 passed |", "| looks fine |")          # done without a hash
    bad = bad.replace("| W1-2 | Nice extra | P2 | 1 | frontend | 2 | W0-1 | open |",
                      "| W1-2 | Nice extra | P2 | 1 | frontend | 2 | W9-9 | in-progress |")  # unknown dep, no owner
    bad = bad.replace("| W2-1 |", "| ZZ1 |")                                           # id pattern
    probs = board.validate(board.parse(write(tmp_path, bad)), r"^(W\d+-\d+|F\d+)$")
    text = "\n".join(probs)
    assert "done without evidence" in text
    assert "unknown id W9-9" in text
    assert "in-progress without an owner" in text
    assert "ZZ1" in text and "does not match" in text


def test_ready_orders_by_priority_and_respects_deps(tmp_path):
    rows = board.parse(write(tmp_path))
    ids = [r.id for r in board.ready(rows)]
    assert ids == ["W1-1", "W1-2"]          # W2-1 waits on W1-1; parked excluded; P1 first


def test_metrics_exclude_parked(tmp_path):
    m = board.metrics(board.parse(write(tmp_path)))
    assert m["est_hours_total"] == 17 and m["est_hours_shipped"] == 4
    assert board.metrics(board.parse(write(tmp_path)), "P1")["shipped_pct"] == round(100 * 4 / 12, 1)


def test_not_done_evidence(repo):
    from orchestrator.config import load
    cfg = load(repo / "orchestration.toml")
    cfg.board.write_text(BOARD)
    rows = board.parse(cfg.board)
    done, ev = board.not_done_evidence(cfg.root, "W1-1", rows, cfg.ledgers)
    assert not done and any("none" in e for e in ev)
    (cfg.ledgers / "W1-1").mkdir(parents=True)
    (cfg.ledgers / "W1-1" / "plan.md").write_text("x")
    sh(repo, "git", "checkout", "-q", "-b", "feat/backend-W1-1-core")
    sh(repo, "git", "commit", "-q", "--allow-empty", "-m", "W1-1: start")
    sh(repo, "git", "checkout", "-q", "main")
    done, ev = board.not_done_evidence(cfg.root, "W1-1", rows, cfg.ledgers)
    joined = "\n".join(ev)
    assert "NOT merged" in joined and "continue from it" in joined
    done, _ = board.not_done_evidence(cfg.root, "W0-1", rows, cfg.ledgers)
    assert done
