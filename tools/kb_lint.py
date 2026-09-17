#!/usr/bin/env python3
"""KB の検査（実験用・最小）。

使い方: python tools/kb_lint.py <kbディレクトリ>
終了コード 0 = 合格、1 = 不合格（違反を1行ずつ印字）。

検査の一覧（ID は selftest.py と対応）:
  C1 先頭に frontmatter（type / updated=YYYY-MM-DD）が無い
  C2 状態ファイル（type: state / project）に失効印（★＋日付、「失効」）がある
  C3 プロジェクトの「現在地」が3行を超える／「骨格」が15行を超える／「未決」の節がある
  C4 「YYYY-MM-DD時点」の日付が 180 日より古い（消す動機を機械が持つ）
  C5 リポジトリ内リンク [..](path) の先が存在しない
  C6 同じ型番らしき識別子が2ファイル以上に出る（写しの疑い）
  C7 1ファイルが 20,000 字を超える
"""
import re
import sys
from datetime import date, datetime
from pathlib import Path

MAX_CHARS = 20000
STALE_DAYS = 180
STATUS_MAX_LINES = 3
SKELETON_MAX_LINES = 15

FM_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
EXPIRED_RE = re.compile(r"★\s*20\d\d-\d\d-\d\d|失効")
DATED_RE = re.compile(r"(20\d\d-\d\d-\d\d)時点")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)#\s]+)(?:#[^)]*)?\)")
IDENT_RE = re.compile(r"\b[A-Z]{2,}[A-Z0-9]*-?[0-9]{3,}[A-Z0-9-]*\b")
STATE_TYPES = {"state", "project"}


def parse_frontmatter(text):
    m = FM_RE.match(text)
    if not m:
        return None
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm


def section_lines(text, heading):
    """'## heading' の節の、空でない箇条書き・本文行を返す。無ければ None。"""
    lines = text.splitlines()
    out = None
    for line in lines:
        if line.startswith("## "):
            if out is not None:
                break
            if line[3:].strip() == heading:
                out = []
            continue
        if out is not None and line.strip():
            out.append(line)
    return out


def lint(kb_dir, today=None):
    today = today or date.today()
    kb = Path(kb_dir)
    problems = []
    ident_seen = {}
    for path in sorted(kb.rglob("*.md")):
        rel = path.relative_to(kb).as_posix()
        text = path.read_text(encoding="utf-8")

        if len(text) > MAX_CHARS:
            problems.append(f"C7 {rel}: {len(text)} 字（上限 {MAX_CHARS}）")

        fm = parse_frontmatter(text)
        if not fm or "type" not in fm or not re.fullmatch(r"20\d\d-\d\d-\d\d", fm.get("updated", "")):
            problems.append(f"C1 {rel}: frontmatter に type / updated(YYYY-MM-DD) が無い")
            fm = fm or {}

        if fm.get("type") in STATE_TYPES and EXPIRED_RE.search(text):
            problems.append(f"C2 {rel}: 状態ファイルに失効印がある（上書きすること）")

        if fm.get("type") == "project":
            st = section_lines(text, "現在地")
            if st is None:
                problems.append(f"C3 {rel}: 「現在地」の節が無い")
            elif len(st) > STATUS_MAX_LINES:
                problems.append(f"C3 {rel}: 「現在地」が {len(st)} 行（上限 {STATUS_MAX_LINES}）")
            sk = section_lines(text, "骨格")
            if sk is not None and len(sk) > SKELETON_MAX_LINES:
                problems.append(f"C3 {rel}: 「骨格」が {len(sk)} 行（上限 {SKELETON_MAX_LINES}）")
            if section_lines(text, "未決") is not None:
                problems.append(f"C3 {rel}: 「未決」の節がある（未決はプロジェクトの置き場へ）")

        for m in DATED_RE.finditer(text):
            d = datetime.strptime(m.group(1), "%Y-%m-%d").date()
            if (today - d).days > STALE_DAYS:
                problems.append(f"C4 {rel}: {m.group(1)}時点 の記述が {STALE_DAYS} 日より古い")

        for m in LINK_RE.finditer(text):
            target = m.group(1)
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            if not (path.parent / target).exists():
                problems.append(f"C5 {rel}: リンク先が無い → {target}")

        for ident in set(IDENT_RE.findall(text)):
            ident_seen.setdefault(ident, []).append(rel)

    for ident, files in ident_seen.items():
        if len(files) >= 2:
            problems.append(f"C6 識別子 {ident} が複数ファイルにある（写しの疑い）: {', '.join(files)}")

    return problems


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    problems = lint(argv[1])
    for p in problems:
        print(p)
    print(f"kb_lint: {len(problems)} 件")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
