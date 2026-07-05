# DotNetAssertions

Landing page for the DotNetAssertions family: focused, AOT-safe assertion
extensions for [TUnit](https://github.com/thomhurst/TUnit). Each package adds a
fluent `Assert.That(...)` vocabulary for one domain.

Live at <https://dotnetassertions.dev>.

| Package | Domain |
| --- | --- |
| [LogAssertions.TUnit](https://logassertions.dev) | Captured `ILogger` logs |
| [SnapshotAssertions.TUnit](https://snapshotassertions.dev) | Text snapshot / approval |
| [TimeAssertions.TUnit](https://timeassertions.dev) | `TimeProvider`, timers, budgets |
| [MathAssertions.TUnit](https://mathassertions.dev) | Numeric, geometry, statistics |
| [JsonAssertions.TUnit](https://jsonassertions.dev) | JSON path / value / shape |
| [SseAssertions.TUnit](https://sseassertions.dev) | Server-Sent Events |
| [GrpcAssertions.TUnit](https://grpcassertions.dev) | gRPC status / response |
| [TracingAssertions.TUnit](https://tracingassertions.dev) | OpenTelemetry `Activity` / spans |
| [MetricsAssertions.TUnit](https://metricsassertions.dev) | Metrics / instruments |

## This repo

A single static page (`index.html`) served by GitHub Pages at the apex custom
domain, with no build step. `CNAME` pins `dotnetassertions.dev`; theme
preference is stored in first-party `localStorage` only.

## License

MIT. Copyright (c) 2026 John Verheij.
