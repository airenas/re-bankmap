def fix_exp_name(name: str, max_len: int = 50) -> str:
    return ''.join(x for x in name if x.isalpha() or x in ' _-0123456789')[:max_len]
