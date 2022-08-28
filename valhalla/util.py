def camel_case(s: str) -> str:
    parts = s.split("_")
    parts[1:] = [_.capitalize() for _ in parts[1:]]
    return "".join(parts)
