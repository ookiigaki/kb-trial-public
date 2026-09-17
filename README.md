# kb-trial — GitHub 関門の実験用リポジトリ（使い捨て）

目的：Claude のセッションから git で書き込めるか、検査を通らない変更を main に入れない関門が成立するかを確かめる。
中身はダミー。本物の KB は入れない。

- `kb/` … KB の形の見本（状態ファイル・プロジェクト・生活の決定）
- `tools/kb_lint.py` … 検査。`python tools/kb_lint.py kb` で 0 なら合格
- `tools/selftest.py` … 検査に故意の誤りを注入して全部鳴るか確かめる
- `tools/propose.sh` … 書き込みの手順を1本にしたもの（ブランチ→コミット→push→PR）
- `.github/workflows/kb-check.yml` … PR と push と毎日1回、selftest と lint を走らせる。ステータス名は `kb-check`
- `ruleset.json` … main を守るルールセット（インポート用）
