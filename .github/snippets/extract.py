#!/usr/bin/env python3
"""Extract the code snippets from index.html into a C# file that is compiled.

The snippet text comes only from index.html: the hero lines (div.row inside
div.hero-lines) and one pre.snippet per package card. This script adds only
the variable declarations a snippet needs (the PACKAGES dict below, keyed by
package). Each snippet becomes the body of its own async method. The
generated file is compiled, never run.

Usage: python extract.py [index.html] [output.cs]
"""
import html.parser
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_HTML = HERE.parent.parent / "index.html"
DEFAULT_OUT = HERE / "Snippets" / "Snippets.g.cs"

# A hero line belongs to the package of its entry point. The receiver variable
# of Assert.That(...) tells which one.
HERO_RECEIVERS = {
    "collector": "Log",
    "time": "Time",
    "json": "Json",
}

# Per package: the namespaces the snippet needs, the declarations of the
# variables it uses, and optional helper types. Keys are the package names
# without the "Assertions.TUnit" suffix.
PACKAGES = {
    "Log": {
        "usings": ["Microsoft.Extensions.Logging", "Microsoft.Extensions.Logging.Testing", "LogAssertions"],
        "decls": ["var collector = new FakeLogCollector();"],
    },
    "Time": {
        "usings": ["Microsoft.Extensions.Time.Testing", "TimeAssertions"],
        "decls": [
            "var fakeTime = new FakeTimeProvider();",
            "var time = new ObservableTimeProvider(fakeTime);",
        ],
    },
    "Snapshot": {
        "usings": ["SnapshotAssertions"],
        "decls": ['string actual = "text";'],
    },
    "Math": {
        "usings": ["System.Numerics", "MathAssertions"],
        "decls": [
            "var rotation = Quaternion.Identity;",
            "var expected = Quaternion.Identity;",
        ],
    },
    "Json": {
        "usings": ["System.Text.Json", "JsonAssertions"],
        "decls": ['string json = "{}";'],
    },
    "Sse": {
        "usings": ["SseAssertions"],
        "decls": ['string body = "event: tick\\ndata: 1\\n\\n";'],
    },
    "Grpc": {
        "usings": ["Grpc.Core", "GrpcAssertions"],
        "decls": [
            "var client = new OrdersClient();",
            "var request = new OrderRequest();",
        ],
        "types": [
            "internal sealed class OrderRequest { }",
            "internal sealed class OrderReply { }",
            "// Shaped like a generated gRPC client: the call returns AsyncUnaryCall<T>.",
            "internal sealed class OrdersClient",
            "{",
            "    public AsyncUnaryCall<OrderReply> GetOrderAsync(OrderRequest request, CancellationToken cancellationToken)",
            "        => GrpcCallBuilder.Success(new OrderReply());",
            "}",
        ],
    },
    "Tracing": {
        "usings": ["System.Diagnostics", "TracingAssertions"],
        "decls": ['using var capture = SpanCapture.ForSource("Shop.Orders");'],
    },
    "Metrics": {
        "usings": ["System.Diagnostics.Metrics", "MetricsAssertions"],
        "decls": [
            'using var meter = new Meter("Shop.Orders");',
            'var counter = meter.CreateCounter<long>("orders.placed");',
            "using var capture = InstrumentCapture.Of(counter);",
        ],
    },
}

# Declared in every method, whatever the package.
COMMON_DECLS = ["CancellationToken ct = CancellationToken.None;"]


class SnippetParser(html.parser.HTMLParser):
    """Collects the hero lines and the card snippets from the page."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hero = []
        self.cards = []
        self._hero_depth = 0
        self._div_stack = []
        self._row = None
        self._h3 = None
        self._pkg = None
        self._pre = None

    @staticmethod
    def _classes(attrs):
        return (dict(attrs).get("class") or "").split()

    def handle_starttag(self, tag, attrs):
        classes = self._classes(attrs)
        if tag == "div":
            is_hero = "hero-lines" in classes
            is_row = "row" in classes and self._hero_depth > 0
            self._div_stack.append("hero" if is_hero else "row" if is_row else "div")
            if is_hero:
                self._hero_depth += 1
            if is_row:
                self._row = []
        elif tag == "h3" and "pkg" in classes:
            self._h3 = []
        elif tag == "pre" and "snippet" in classes:
            self._pre = []

    def handle_endtag(self, tag):
        if tag == "div" and self._div_stack:
            kind = self._div_stack.pop()
            if kind == "hero":
                self._hero_depth -= 1
            elif kind == "row":
                self.hero.append("".join(self._row))
                self._row = None
        elif tag == "h3" and self._h3 is not None:
            self._pkg = "".join(self._h3)
            self._h3 = None
        elif tag == "pre" and self._pre is not None:
            self.cards.append((self._pkg, "".join(self._pre)))
            self._pre = None

    def handle_data(self, data):
        for target in (self._row, self._h3, self._pre):
            if target is not None:
                target.append(data)


def package_key(heading):
    """Turns a card heading such as 'LogAssertions.TUnit' into 'Log'."""
    name = (heading or "").strip()
    suffix = "Assertions.TUnit"
    if not name.endswith(suffix) or name[: -len(suffix)] not in PACKAGES:
        raise SystemExit(f"error: card heading '{heading}' is not a known package")
    return name[: -len(suffix)]


def hero_package(line):
    """Finds the package of a hero line from the receiver of Assert.That(...)."""
    marker = "Assert.That("
    start = line.find(marker)
    if start < 0:
        raise SystemExit(f"error: hero line has no Assert.That(...): {line}")
    receiver = line[start + len(marker):].split(")", 1)[0].strip()
    if receiver not in HERO_RECEIVERS:
        raise SystemExit(f"error: no package mapped for hero receiver '{receiver}': {line}")
    return HERO_RECEIVERS[receiver]


def method_source(name, package, snippet):
    """Builds one async method: the declarations, then the snippet text."""
    lines = [f"        public static async Task {name}()", "        {"]
    for decl in COMMON_DECLS + PACKAGES[package]["decls"]:
        lines.append(f"            {decl}")
    lines.append("")
    snippet_lines = snippet.strip().splitlines()
    for index, line in enumerate(snippet_lines):
        text = line.strip() if index == 0 else line.rstrip()
        lines.append(f"            {text}")
    lines.append("        }")
    return "\n".join(lines)


def build(hero, cards):
    """Builds the whole C# file, one namespace per package."""
    by_package = {key: [] for key in PACKAGES}
    for index, line in enumerate(hero, start=1):
        by_package[hero_package(line)].append((f"Hero{index}", line))
    for heading, text in cards:
        by_package[package_key(heading)].append(("Card", text))
    out = [
        "// <auto-generated> by extract.py from index.html. Do not edit. </auto-generated>",
        "#nullable enable",
        "",
    ]
    for package, snippets in by_package.items():
        if not snippets:
            raise SystemExit(f"error: no snippet found for package {package}")
        spec = PACKAGES[package]
        out.append(f"namespace {package}Snippets")
        out.append("{")
        for using in ["System", "System.Threading", "System.Threading.Tasks"] + spec["usings"]:
            out.append(f"    using {using};")
        out.append("")
        out.extend(f"    {line}" for line in spec.get("types", []))
        out.append("    internal static class Snippets")
        out.append("    {")
        out.append("\n\n".join(method_source(n, package, s) for n, s in snippets))
        out.append("    }")
        out.append("}")
        out.append("")
    return "\n".join(out)


def main(argv):
    """Reads the page, checks the snippet counts and writes the C# file."""
    html_path = pathlib.Path(argv[1]) if len(argv) > 1 else DEFAULT_HTML
    out_path = pathlib.Path(argv[2]) if len(argv) > 2 else DEFAULT_OUT
    parser = SnippetParser()
    parser.feed(html_path.read_text(encoding="utf-8"))
    parser.close()
    if len(parser.cards) != len(PACKAGES):
        raise SystemExit(f"error: expected {len(PACKAGES)} card snippets, found {len(parser.cards)}")
    if not parser.hero:
        raise SystemExit("error: no hero lines found")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build(parser.hero, parser.cards), encoding="utf-8", newline="\n")
    print(f"extracted {len(parser.hero)} hero lines and {len(parser.cards)} card snippets -> {out_path}")


if __name__ == "__main__":
    main(sys.argv)
