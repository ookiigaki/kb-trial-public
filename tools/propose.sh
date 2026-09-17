#!/usr/bin/env bash
# 書き込みの手順を1本にしたもの：ブランチ→コミット→push→PR作成→（任意）自動マージ。
# 使い方: tools/propose.sh "<コミットとPRの題>"
# 前提: GITHUB_TOKEN が環境にあり、origin が https://github.com/<owner>/<repo>.git であること。
set -euo pipefail

title="${1:?題を渡す}"
branch="propose/$(date -u +%Y%m%d-%H%M%S)"
remote_url="$(git remote get-url origin)"
slug="$(echo "$remote_url" | sed -E 's#(git@github.com:|https://github.com/)##; s#\.git$##')"
base="$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#origin/##' || echo main)"

python3 tools/selftest.py
python3 tools/kb_lint.py kb

git checkout -b "$branch"
git add -A
git commit -m "$title"
git push -u origin "$branch"

pr_json="$(curl -sS -X POST \
  -H "Authorization: Bearer ${GITHUB_TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/${slug}/pulls" \
  -d "$(python3 -c 'import json,sys;print(json.dumps({"title":sys.argv[1],"head":sys.argv[2],"base":sys.argv[3],"body":"kb-check が緑なら自動で入る。"}))' "$title" "$branch" "$base")")"
pr_url="$(echo "$pr_json" | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d.get("html_url") or d)')"
pr_node="$(echo "$pr_json" | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d.get("node_id",""))')"
echo "PR: $pr_url"

# 自動マージ（リポジトリ設定 Allow auto-merge が ON のときだけ通る。失敗しても PR は残る）
if [ -n "$pr_node" ]; then
  curl -sS -X POST -H "Authorization: Bearer ${GITHUB_TOKEN}" https://api.github.com/graphql \
    -d "$(python3 -c 'import json,sys;print(json.dumps({"query":"mutation($id:ID!){enablePullRequestAutoMerge(input:{pullRequestId:$id,mergeMethod:SQUASH}){clientMutationId}}","variables":{"id":sys.argv[1]}}))' "$pr_node")" \
    | python3 -c 'import json,sys;d=json.load(sys.stdin);print("auto-merge:", "ON" if "errors" not in d else d["errors"][0]["message"])'
fi
git checkout "$base"
