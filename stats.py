#!/usr/bin/env python3
"""Add up the download counts of a repository's releases.

GitHub keeps only a running total per release file. This writes, into the
directory given as the only argument:

* stats.json  - the totals now: overall, per release and per group.
* history.csv - one row per day with the overall total. Today's row is added
  to the file that is already there, or replaced if the day already has one.

Configured by environment variables (set by action.yml): REPOSITORY,
GITHUB_TOKEN, EXCLUDE (regex of file names not to count) and GROUP (regex
with named groups; each group counts the downloads per value it matched).
"""

import csv
import json
import os
import re
import sys
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


def releases(repo: str, token: str):
    """Every release of *repo*, page by page."""
    url = f"{os.environ.get('GITHUB_API_URL', 'https://api.github.com')}/repos/{repo}/releases?per_page=100"
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    while url:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers)) as r:
            yield from json.load(r)
            link = re.search(r'<([^>]+)>;\s*rel="next"', r.headers.get("Link", ""))
            url = link and link.group(1)


def short(n: int) -> str:
    """519143 -> "519k", 1234567 -> "1.2M"."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M".replace(".0M", "M")
    return f"{n // 1_000}k" if n >= 1_000 else str(n)


def count(all_releases, exclude, group) -> dict:
    per_release: dict[str, int] = {}
    groups: dict[str, Counter] = defaultdict(Counter)
    for release in all_releases:
        if release["draft"]:
            continue
        total = 0
        for asset in release["assets"]:
            if exclude and exclude.search(asset["name"]):
                continue
            n = asset["download_count"]
            total += n
            match = group.search(asset["name"]) if group else None
            for key, value in (match.groupdict() if match else {}).items():
                if value:
                    groups[key][value] += n
        per_release[release["tag_name"]] = total
    total = sum(per_release.values())
    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total": total,
        "total_short": short(total),
        "releases": dict(sorted(per_release.items(), key=lambda kv: -kv[1])),
        "groups": {k: dict(c.most_common()) for k, c in sorted(groups.items())},
    }


def main() -> None:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    exclude = os.environ.get("EXCLUDE")
    group = os.environ.get("GROUP")
    stats = {"repository": os.environ["REPOSITORY"]} | count(
        releases(os.environ["REPOSITORY"], os.environ.get("GITHUB_TOKEN", "")),
        re.compile(exclude) if exclude else None,
        re.compile(group) if group else None,
    )
    out.mkdir(parents=True, exist_ok=True)
    (out / "stats.json").write_text(json.dumps(stats, indent=2) + "\n")

    history = out / "history.csv"
    rows = list(csv.DictReader(history.open())) if history.is_file() else []
    today = stats["generated_at"][:10]
    rows = [r for r in rows if r["date"] != today]
    rows.append({"date": today, "total": stats["total"]})
    with history.open("w", newline="") as f:
        writer = csv.DictWriter(f, ["date", "total"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda r: r["date"]))

    print(f"{stats['total']:,} downloads")
    if path := os.environ.get("GITHUB_OUTPUT"):
        with open(path, "a") as f:
            f.write(f"total={stats['total']}\ntotal-short={stats['total_short']}\n")
    if path := os.environ.get("GITHUB_STEP_SUMMARY"):
        lines = [f"## {stats['total']:,} downloads", ""]
        for key, counts in stats["groups"].items():
            lines += [f"| {key} | downloads |", "| --- | ---: |"]
            lines += [f"| {v} | {n:,} |" for v, n in counts.items()] + [""]
        with open(path, "a") as f:
            f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
