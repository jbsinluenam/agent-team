from core.categories import EXPENSE_KEYWORDS, INCOME_KEYWORDS, PAYMENT_MAP


def parse(text: str) -> dict | None:
    tokens = text.strip().split()

    amount = None
    amount_idx = None
    for i, token in enumerate(tokens):
        try:
            amount = float(token.replace(",", ""))
            amount_idx = i
            break
        except ValueError:
            continue

    if amount is None:
        return None

    payment = ""
    if amount_idx is not None and amount_idx + 1 < len(tokens):
        candidate = tokens[amount_idx + 1].lower()
        if candidate in PAYMENT_MAP:
            payment = PAYMENT_MAP[candidate]

    description = " ".join(tokens[:amount_idx]) if amount_idx is not None else text

    text_lower = text.lower()
    for kw in INCOME_KEYWORDS:
        if kw in text_lower:
            return {
                "type": "income",
                "description": description,
                "amount": amount,
                "category": "Income",
                "payment": payment,
            }

    category = None
    for cat, keywords in EXPENSE_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                category = cat
                break
        if category:
            break

    return {
        "type": "expense",
        "description": description,
        "amount": amount,
        "category": category,
        "payment": payment,
    }
