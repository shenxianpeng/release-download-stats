<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/banner-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="docs/banner-light.svg">
  <img src="docs/banner-light.svg" alt="release-download-stats — Record the download counts of your GitHub releases every day" width="100%" />
</picture>

[![Test](https://github.com/shenxianpeng/release-download-stats/actions/workflows/test.yml/badge.svg)](https://github.com/shenxianpeng/release-download-stats/actions/workflows/test.yml)
[![Release](https://img.shields.io/github/v/release/shenxianpeng/release-download-stats)](https://github.com/shenxianpeng/release-download-stats/releases)
[![License](https://img.shields.io/github/license/shenxianpeng/release-download-stats)](LICENSE)

GitHub counts how often each release file is downloaded, but keeps only the running total. This action records the counts of every release once a day, so you can see how they grow.

</div>

Each run commits two files to a branch of your repository (`download-stats` by default):

- `stats.json`: the total now, per release and, optionally, per group of files.
- `history.csv`: one row per day with the total.

It needs nothing but the token of the workflow run: a short Python script that uses only the standard library, no extra tools or services.

## Usage

> [!TIP]
> `@v1` always points to the latest `v1.x.y` release. Pin an exact version (for example `@v1.0.0`) or a commit SHA if you prefer.

```yaml
name: Download stats

on:
  schedule:
    - cron: '20 5 * * *'
  workflow_dispatch:

permissions: {}

concurrency:
  group: download-stats

jobs:
  stats:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: shenxianpeng/release-download-stats@v1
```

## Inputs

| Input | Default | Description |
| --- | --- | --- |
| `repository` | the current one | Repository whose releases are counted. |
| `stats-repository` | `repository` | Repository that the branch is kept in (see [below](#keeping-the-numbers-in-another-repository)). |
| `exclude` | checksums and signatures | Regular expression of file names not to count. |
| `group` | none | Regular expression with named groups. Each group counts the downloads per value it matched (see below). |
| `branch` | `download-stats` | Branch of `stats-repository` that the files are committed to. It is created on the first run. |
| `publish` | `true` | Set to `false` to only count, for example in pull requests. |
| `token` | `github.token` | Token that reads the releases and pushes the branch to `stats-repository`. |

Outputs: `total` (for example `519373`) and `total-short` (`519k`). The job summary shows the total and the groups.

## Groups

The release files of [cpp-linter/clang-tools-static-binaries](https://github.com/cpp-linter/clang-tools-static-binaries/releases) are named like `clang-format-22_linux-amd64`. For them,

```yaml
      - uses: shenxianpeng/release-download-stats@v1
        with:
          group: '-(?P<version>\d+)(?:\.\d+)*_(?P<platform>[a-z0-9]+(?:-[a-z0-9]+)+)'
```

adds the downloads per version and per platform to `stats.json` (shortened to the first two of each):

```json
{
  "repository": "cpp-linter/clang-tools-static-binaries",
  "generated_at": "2026-11-26T06:34:53Z",
  "total": 519373,
  "total_short": "519k",
  "releases": { "master-63858060": 81897, "master-b35c5633": 58066 },
  "groups": {
    "platform": { "linux-amd64": 272533, "windows-amd64": 151307 },
    "version": { "22": 92496, "12": 74373 }
  }
}
```

This repository [counts them every day](.github/workflows/download-stats.yml): the whole file, up to date, is [`stats.json`](https://raw.githubusercontent.com/shenxianpeng/release-download-stats/download-stats/stats.json).

## Keeping the numbers in another repository

By default the branch is kept in the repository whose releases are counted. To count the releases of one repository and keep the numbers in another, for example to collect the numbers of several projects in one place, set `stats-repository`:

```yaml
      - uses: shenxianpeng/release-download-stats@v1
        with:
          repository: OWNER/PROJECT
          stats-repository: ${{ github.repository }}
          branch: download-stats-PROJECT
```

Run it in the workflow of the repository that keeps the numbers: the token of the run can push there and read the releases of any public repository. For a private `repository`, or to push to a repository other than the current one, pass a `token` that may do both.

## Showing the numbers

The files are on a branch, so they can be read from `raw.githubusercontent.com`, which allows requests from any web page. Replace `OWNER/REPO` below with the repository that keeps the branch (`stats-repository`); the branch is `download-stats` unless you changed `branch`.

### Badge

A [dynamic JSON badge](https://shields.io/badges/dynamic-json-badge) from shields.io reads `stats.json` and updates by itself after every run:

| Badge in your README | `query` |
| --- | --- |
| ![downloads](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fshenxianpeng%2Frelease-download-stats%2Fdownload-stats%2Fstats.json&query=%24.total_short&label=downloads) | `$.total_short` |
| ![downloads](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fshenxianpeng%2Frelease-download-stats%2Fdownload-stats%2Fstats.json&query=%24.total&label=downloads) | `$.total` |
| ![linux-amd64](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fshenxianpeng%2Frelease-download-stats%2Fdownload-stats%2Fstats.json&query=%24.groups.platform%5B%22linux-amd64%22%5D&label=linux-amd64) | `$.groups.platform["linux-amd64"]` (one value of a [group](#groups)) |
| ![downloads](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fshenxianpeng%2Frelease-download-stats%2Fdownload-stats%2Fstats.json&query=%24.total_short&label=downloads&style=for-the-badge&logo=github) | `$.total_short`, with `&style=for-the-badge&logo=github` |

<sub>These badges are live: they show the downloads of [cpp-linter/clang-tools-static-binaries](https://github.com/cpp-linter/clang-tools-static-binaries/releases), which [this repository counts](.github/workflows/download-stats.yml). Yours shows your own.</sub>

The first one, ready to copy:

```markdown
[![Downloads](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2FOWNER%2FREPO%2Fdownload-stats%2Fstats.json&query=%24.total_short&label=downloads)](https://github.com/OWNER/REPO/releases)
```

For another row, change `query` (URL-encoded) and `label`. Every [shields.io style](https://shields.io/badges/dynamic-json-badge) works too: `color`, `style`, `logo`.

### Chart

`history.csv` has one row per day, for example [the one of the badges above](https://raw.githubusercontent.com/shenxianpeng/release-download-stats/download-stats/history.csv):

```csv
date,total
2026-11-26,519373
```

A web page can `fetch()` it, or `stats.json`, and draw a chart with any library. The difference between two rows is the downloads of that day.

## Notes

- Counts include downloads by CI jobs, so they show use, not users.
- GitHub does not count the source code archives (`.zip` and `.tar.gz` of the tag).
- `history.csv` starts on the day of the first run: GitHub keeps no earlier counts.
- If a ruleset protects every branch, allow GitHub Actions to push to the stats branch.

## License

[MIT](LICENSE)
