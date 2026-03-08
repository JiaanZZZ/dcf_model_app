def fair_value(eps: float, g: float, n: int, pe_exit: float, r: float) -> float:
    """Compute DCF fair value. g and r are percentages (e.g. 15.0 for 15%)."""
    return eps * (1 + g / 100) ** n * pe_exit / (1 + r / 100) ** n


def implied_growth(price: float, eps: float, n: int, pe_exit: float, r: float) -> float | None:
    """Reverse-engineer the growth rate implied by the current market price."""
    ratio = (price * (1 + r / 100) ** n) / (eps * pe_exit)
    if ratio <= 0:
        return None
    return (ratio ** (1 / n) - 1) * 100


def eps_path(eps: float, g: float, n: int, pe_exit: float, r: float) -> list[dict]:
    """Return year-by-year EPS compounding table as a list of dicts."""
    rows = []
    eps_t = eps
    for yr in range(1, n + 1):
        eps_t *= (1 + g / 100)
        exit_p = eps_t * pe_exit if yr == n else None
        pv_val = exit_p / (1 + r / 100) ** yr if exit_p else None
        rows.append({
            "year": yr,
            "eps": eps_t,
            "exit_price": exit_p,
            "pv": pv_val,
        })
    return rows
