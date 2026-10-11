def compact_number(value):
    sign = "-" if value < 0 else ""
    value = abs(value)
    if value < 10_000:
        return f"{sign}{value}"
    if value < 1_000_000:
        return f"{sign}{value // 1000} Tsd."
    millions = value // 100_000 / 10
    return f"{sign}{millions:g}M"
