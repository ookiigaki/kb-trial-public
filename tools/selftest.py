#!/usr/bin/env python3
"""検査に故意の誤りを注入し、検査 C1〜C7 がそれぞれ鳴ることを確かめる。
1つでも鳴らなければ終了コード 1（検査が壊れている＝本番の検査を信用してはいけない）。
きれいな入力で 0 件になることも確かめる（偽陽性の検出）。
"""
import sys
import tempfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import kb_lint  # noqa: E402

TODAY = date(2026, 9, 17)

CLEAN = {
    "profile.md": "---\ntype: state\nupdated: 2026-09-17\n---\n# P\n- 名前: X\n",
    "projects/j.md": (
        "---\ntype: project\nupdated: 2026-09-17\n---\n# J\n\n## 現在地\n- a\n- b\n\n## 骨格\n- x\n\n## 置き場\n- [決定](../decisions/life.md)\n"
    ),
    "decisions/life.md": "---\ntype: log\nupdated: 2026-09-17\n---\n# L\n## 2026-09-17｜x\n- y\n",
}

INJECTIONS = {
    "C1": {"profile.md": "# frontmatter なし\n- 名前: X\n"},
    "C2": {"profile.md": "---\ntype: state\nupdated: 2026-09-17\n---\n- 配列 US ★2026-08-18に失効\n"},
    "C3": {"projects/j.md": "---\ntype: project\nupdated: 2026-09-17\n---\n## 現在地\n- 1\n- 2\n- 3\n- 4\n\n## 未決\n- z\n"},
    "C4": {"profile.md": "---\ntype: state\nupdated: 2026-09-17\n---\n- 体重 2025-01-01時点 90kg\n"},
    "C5": {"projects/j.md": "---\ntype: project\nupdated: 2026-09-17\n---\n## 現在地\n- [原文](../nowhere.md)\n"},
    "C6": {
        "profile.md": "---\ntype: state\nupdated: 2026-09-17\n---\n- ノート PC RZ09-0510\n",
        "projects/j.md": "---\ntype: project\nupdated: 2026-09-17\n---\n## 現在地\n- RZ09-0510 で設計\n",
    },
    "C7": {"profile.md": "---\ntype: state\nupdated: 2026-09-17\n---\n" + ("あ" * 20001)},
}


def write_tree(root, files):
    for rel, body in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")


def main():
    failures = []
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "kb"
        write_tree(root, CLEAN)
        clean = kb_lint.lint(root, today=TODAY)
        if clean:
            failures.append(f"きれいな入力で鳴った（偽陽性）: {clean}")

    for check_id, files in INJECTIONS.items():
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "kb"
            write_tree(root, CLEAN)
            write_tree(root, files)
            problems = kb_lint.lint(root, today=TODAY)
            if not any(p.startswith(check_id + " ") for p in problems):
                failures.append(f"{check_id} が鳴らない。出たもの: {problems}")

    for f in failures:
        print("NG", f)
    print(f"selftest: 注入 {len(INJECTIONS)} 件中 {len(INJECTIONS) - sum(1 for f in failures if not f.startswith('きれい'))} 件検出、"
          f"偽陽性 {'あり' if any(f.startswith('きれい') for f in failures) else 'なし'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
