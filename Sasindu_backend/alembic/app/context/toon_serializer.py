def to_toon(rows: list[dict]) -> str:
    """Minimal TOON (Token-Oriented Object Notation) encoder: one header line of
    pipe-delimited keys, then one pipe-delimited data line per row. Avoids repeating
    JSON key names on every row, which is the source of its token-count advantage
    (measured formally in Phase 10)."""
    if not rows:
        return ""
    keys = list(rows[0].keys())
    lines = ["|".join(keys)]
    for row in rows:
        lines.append("|".join(str(row[k]) for k in keys))
    return "\n".join(lines)
