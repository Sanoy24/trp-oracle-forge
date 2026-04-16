# deps.dev v1 Dataset — Domain Knowledge

This document is injected into the agent's Domain Knowledge context layer before any deps.dev query is answered. All facts here are specific to this dataset — do not assume they apply to other DAB datasets.

---

## Dataset Structure

Two active databases. Package metadata lives in SQLite, project information and package-to-project mappings live in DuckDB.

| Database | Format | What it contains |
|----------|--------|-----------------|
| `package_database` | SQLite | Software package metadata — licenses, versions, dependencies, advisories |
| `project_database` | DuckDB | GitHub project info and package-to-project mappings |

---

## Schema Reference

### SQLite — `package_database`

#### `packageinfo` table
| Field | Type | Notes |
|-------|------|-------|
| `System` | str | Package ecosystem e.g. `NPM`, `Maven` |
| `Name` | str | Package name |
| `Version` | str | Version string |
| `Licenses` | str | JSON-like array of licenses |
| `Links` | str | JSON-like list of links (origin, docs, source) |
| `Advisories` | str | JSON-like list of security advisories |
| `VersionInfo` | str | JSON-like object — `IsRelease`, `Ordinal` |
| `Hashes` | str | JSON-like list of file hashes |
| `DependenciesProcessed` | bool | Whether dependencies were processed |
| `DependencyError` | bool | Whether a dependency error occurred |
| `UpstreamPublishedAt` | float | Unix timestamp in milliseconds |
| `Registries` | str | JSON-like list of registries |
| `SLSAProvenance` | float | SLSA provenance level if available |
| `UpstreamIdentifiers` | str | JSON-like list of upstream identifiers |
| `Purl` | float | Package URL in purl format if available |

### DuckDB — `project_database`

#### `project_packageversion` table
| Field | Type | Notes |
|-------|------|-------|
| `System` | str | Package ecosystem |
| `Name` | str | Package name |
| `Version` | str | Package version string |
| `ProjectType` | str | e.g. `GITHUB` |
| `ProjectName` | str | Repository path in `owner/repo` format |
| `RelationProvenance` | str | Provenance of the relationship |
| `RelationType` | str | Type of relationship e.g. source repository |

#### `project_info` table
| Field | Type | Notes |
|-------|------|-------|
| `Project_Information` | str | Natural language — includes project name, GitHub stars, fork count, other details |
| `Licenses` | str | JSON-like array of licenses |
| `Description` | str | Project description |
| `Homepage` | str | Homepage URL |
| `OSSFuzz` | float | OSSFuzz status indicator |

---

## Join Pattern — Three-Table Chain

Queries require joining across all three tables in order:

```
packageinfo (SQLite)
    → match on System + Name + Version →
project_packageversion (DuckDB)
    → match on ProjectName →
project_info (DuckDB)
```

1. Get `System`, `Name`, `Version` from `packageinfo`
2. Find matching row in `project_packageversion` using all three fields
3. Take `ProjectName` from that row
4. Look up `project_info` using `ProjectName`

Do not skip steps — there is no direct link between `packageinfo` and `project_info`.

---

## Domain Rules

### GitHub Stars and Fork Count
Stars and fork count are embedded inside `project_info.Project_Information` as natural language text — they are not separate columns. Use regex to extract numeric values.

### Timestamps
`UpstreamPublishedAt` is a Unix timestamp in **milliseconds** — divide by 1000 to get seconds before converting to a date.

### JSON-like String Fields
`Licenses`, `Advisories`, `Links`, `Hashes`, `Registries` in `packageinfo` are stored as JSON-like array strings. Use `json_extract` or parse with Python before filtering.

### Security Advisories
`Advisories` field contains security advisory records. A package with an empty or null `Advisories` field has no known vulnerabilities.
