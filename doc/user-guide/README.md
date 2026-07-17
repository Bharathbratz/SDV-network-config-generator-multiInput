# Linux Network Config User Guide — Build Instructions

This directory contains the AsciiDoc user guide for the Linux network configuration generator.

## Build inside the Dev Container (recommended)

All tools are pre-installed in the container — no local installation needed.

```bash
# HTML
asciidoctor doc/user-guide/linux-network-config-user-guide.adoc

# PDF
asciidoctor-pdf doc/user-guide/linux-network-config-user-guide.adoc
```

Output is written alongside the source file:
- `doc/user-guide/linux-network-config-user-guide.html`
- `doc/user-guide/linux-network-config-user-guide.pdf`

