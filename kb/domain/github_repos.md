# GitHub Repos Dataset — Domain Knowledge

This document is injected into the agent's Domain Knowledge context layer before any GitHub Repos query is answered. All facts here are specific to this dataset — do not assume they apply to other DAB datasets.

---

## Dataset Structure

Two active databases. Repository metadata lives in SQLite, repository artifacts (files, commits, contents) live in DuckDB.

| Database | Format | What it contains |
|----------|--------|-----------------|
| `metadata_database` | SQLite | Languages, licenses, watch counts per repo |
| `artifacts_database` | DuckDB | File contents, commits, file-level metadata |

---

## Schema Reference

### SQLite — `metadata_database`

#### `languages` table
| Field | Type | Notes |
|-------|------|-------|
| `repo_name` | str | `owner/repo` format |
| `language_description` | str | Natural language — may list multiple languages |

#### `licenses` table
| Field | Type | Notes |
|-------|------|-------|
| `repo_name` | str | `owner/repo` format |
| `license` | str | e.g. `apache-2.0`, `mit` |

#### `repos` table
| Field | Type | Notes |
|-------|------|-------|
| `repo_name` | str | `owner/repo` format |
| `watch_count` | int | Number of watchers |

### DuckDB — `artifacts_database`

#### `contents` table
| Field | Type | Notes |
|-------|------|-------|
| `id` | str | File blob identifier |
| `content` | str | File content — may be truncated for large or binary files |
| `sample_repo_name` | str | `owner/repo` format |
| `sample_ref` | str | Branch or commit SHA |
| `sample_path` | str | File path within repo |
| `sample_symlink_target` | str | Symlink target if applicable |
| `repo_data_description` | str | Natural language metadata — derived from size, binary, copies, mode |

#### `commits` table
| Field | Type | Notes |
|-------|------|-------|
| `commit` | str | Commit SHA |
| `tree` | str | Tree SHA |
| `parent` | str | JSON-like parent commit SHAs |
| `author` | str | JSON-like object — name, email, timestamp |
| `committer` | str | JSON-like object — name, email, timestamp |
| `subject` | str | Short commit message subject line |
| `message` | str | Full commit message |
| `trailer` | str | JSON-like additional metadata |
| `difference` | str | JSON-like file changes in this commit |
| `difference_truncated` | bool | Whether difference data is truncated |
| `repo_name` | str | `owner/repo` format |
| `encoding` | str | Encoding format if applicable |

#### `files` table
| Field | Type | Notes |
|-------|------|-------|
| `repo_name` | str | `owner/repo` format |
| `ref` | str | Branch or commit SHA |
| `path` | str | File path within repo |
| `mode` | int | File mode (normal, executable, symlink) |
| `id` | str | File blob identifier — links to `contents.id` |
| `symlink_target` | str | Symlink target if applicable |

---

## Join Keys

- Across all tables: `repo_name` (SQLite) = `sample_repo_name` (DuckDB contents) = `repo_name` (DuckDB commits/files)
- `files.id` = `contents.id` to get file content from file metadata

---

## Domain Rules

### Primary Language Detection
`languages.language_description` lists multiple languages per repo in natural language. To find the primary language, compare the relative byte count across languages mentioned — the one with the highest byte count is the primary language.

### File Content May Be Truncated
`contents.content` may contain placeholders for large or binary files. Do not assume full file content is always available.

### Commit Author vs Committer
`author` and `committer` are JSON-like strings. Parse to extract name, email, or timestamp. Author = who wrote the code, committer = who applied the commit (may differ in rebased or merged commits).

### repo_data_description
`contents.repo_data_description` is a natural language field derived from file attributes (size, binary, copies, mode). Use substring or regex matching to filter on file attributes — not direct field access.
