"""Context normaliser for Jinja2 rendering.

Wraps a raw JSON dict under the ``data`` key so all templates can access
the full document as ``data['ietf-interfaces:interfaces']`` etc.
"""


def alter_context(context: dict) -> dict:
    """Return *context* wrapped under ``data`` if not already present."""
    if "data" not in context:
        return {"data": context}
    return context
