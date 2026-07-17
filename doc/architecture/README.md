# Architecture Document — Build Instructions

This directory contains the AsciiDoc architecture document for the automated network configuration tooling.

## Build inside the Dev Container (recommended)

All tools are pre-installed in the container — no local installation needed.

```bash
# HTML
asciidoctor doc/architecture/linux-networkconfig-automation.adoc

# PDF
asciidoctor-pdf doc/architecture/linux-networkconfig-automation.adoc
```

Output is written alongside the source file:
- `doc/architecture/linux-networkconfig-automation.html`
- `doc/architecture/linux-networkconfig-automation.pdf`
