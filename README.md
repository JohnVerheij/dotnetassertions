# DotNetAssertions

Landing page for the DotNetAssertions family: focused, AOT-safe assertion
extensions for [TUnit](https://github.com/thomhurst/TUnit). Each package adds a
fluent `Assert.That(...)` vocabulary for one domain.

Live at <https://dotnetassertions.dev>.

| Package | Domain |
| --- | --- |
| [LogAssertions.TUnit](https://logassertions.dev) | Captured `ILogger` records: filters, counts, order, level limits |
| [TimeAssertions.TUnit](https://timeassertions.dev) | Fake-clock state, timer leaks and fires, time budgets |
| [SnapshotAssertions.TUnit](https://snapshotassertions.dev) | Text snapshots with scrubbers and line diffs |
| [MathAssertions.TUnit](https://mathassertions.dev) | Tolerance checks for vectors, quaternions, poses; statistics; 3D geometry |
| [JsonAssertions.TUnit](https://jsonassertions.dev) | JSON path, value, subset and equivalence; ProblemDetails |
| [SseAssertions.TUnit](https://sseassertions.dev) | Server-Sent Events: named events, data, ids, retry |
| [GrpcAssertions.TUnit](https://grpcassertions.dev) | `RpcException` status, detail, trailers; fake calls and streams |
| [TracingAssertions.TUnit](https://tracingassertions.dev) | `Activity` spans: lookup, tags, parent/child, durations, tree |
| [MetricsAssertions.TUnit](https://metricsassertions.dev) | `System.Diagnostics.Metrics` captures: totals, counts, tags, samples |

The packages target every .NET version in Microsoft support: .NET 10 and
.NET 11 today. The TUnit version each package needs is in its own README.

## This repo

A single static page (`index.html`) served by GitHub Pages at the apex custom
domain, with no build step. `CNAME` pins `dotnetassertions.dev`; theme
preference is stored in first-party `localStorage` only. `_config.yml` keeps
`README.md` and `LICENSE` out of the published site.

## Checks

The workflow `.github/workflows/site.yml` runs on every push to `main`, on
pull requests, and weekly.

- **Snippets compile.** `.github/snippets/extract.py` reads every code snippet
  from `index.html` (the hero lines and one per card) and writes them into a
  small project, `.github/snippets/Snippets`, as one method per snippet. The
  project references TUnit and all nine packages without a pinned version, so
  it builds against the newest published packages on `net10.0` and `net11.0`.
  The build fails when a snippet no longer compiles or uses an obsolete API.
  The snippets are compiled, not run. The variables a snippet uses
  (`collector`, `time`, `json`, ...) are declared in `extract.py`; the snippet
  text comes only from `index.html`.
- **Links resolve.** [lychee](https://github.com/lycheeverse/lychee) checks the
  links in `index.html` and `README.md`.

To run the snippet check locally:

```sh
python .github/snippets/extract.py
dotnet restore .github/snippets/Snippets/Snippets.csproj --force-evaluate
dotnet build .github/snippets/Snippets/Snippets.csproj --no-restore
```

The forced restore takes the newest packages: their versions float (`*`) and
there is no lock file, so a plain build can reuse an earlier restore.

When a snippet needs a new variable, add its declaration to `PACKAGES` in
`extract.py`.

## License

MIT. Copyright (c) 2026 John Verheij.
