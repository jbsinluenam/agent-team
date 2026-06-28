import os
from datetime import date
from core.parser import parse
from core.sheets import SheetsClient
from core.categories import PAYMENT_TO_ACCOUNT

_client = None


def _get_client() -> SheetsClient:
    global _client
    if _client is None:
        _client = SheetsClient()
    return _client


def _reset_client() -> None:
    global _client
    _client = None


def handle(text: str, client: SheetsClient | None = None) -> str:
    if client is None:
        client = _get_client()

    lower = text.lower().strip()

    if lower in ("summary", "สรุป"):
        return _summary(client)
    if lower in ("balance", "บัญชี"):
        return _balance(client)

    result = parse(text)
    if result is None:
        return "ไม่เจอจำนวนเงิน ลองใหม่นะ เช่น กาแฟ 65"

    if result["type"] == "income":
        return _record_income(result, client)
    return _record_expense(result, client)


def _summary(client: SheetsClient) -> str:
    month = date.today().strftime("%Y-%m")
    txns = client.get_transactions(month=month)
    accounts = client.get_accounts()

    income = sum(t["Amount"] for t in txns if t.get("Type") == "income")
    expense = sum(t["Amount"] for t in txns if t.get("Type") == "expense")
    net = income - expense

    cats: dict[str, float] = {}
    for t in txns:
        if t.get("Type") == "expense":
            c = t["Category"]
            cats[c] = cats.get(c, 0) + t["Amount"]

    lines = [f"📊 Summary — {month}\n"]
    lines.append(f"💰 Income:   {income:>10,.0f}")
    lines.append(f"💸 Expenses: {expense:>10,.0f}")
    lines.append(f"📈 Net:      {net:>10,.0f}\n")

    if cats:
        lines.append("Expenses by category:")
        for cat, amt in sorted(cats.items(), key=lambda x: -x[1]):
            lines.append(f"  {cat}: {amt:,.0f}")

    daily = [a for a in accounts if a.get("Group") == "Daily"]
    if daily:
        lines.append("\n💳 Daily Accounts:")
        for a in daily:
            bal = float(a.get("Balance") or 0)
            icon = "🏦" if a.get("Type") == "savings" else "💳"
            suffix = " (outstanding)" if a.get("Type") == "credit" else ""
            lines.append(f"  {icon} {a['Account']}{suffix}: {bal:,.0f}")

    return "\n".join(lines)


def _balance(client: SheetsClient) -> str:
    accounts = client.get_accounts()
    lines = ["💰 Account Balances\n"]
    savings = [a for a in accounts if a.get("Type") == "savings"]
    credit = [a for a in accounts if a.get("Type") == "credit"]
    for a in savings:
        bal = float(a.get("Balance") or 0)
        lines.append(f"🏦 {a['Account']}: {bal:,.0f}")
    if credit:
        lines.append("\n💳 Outstanding:")
        for a in credit:
            bal = float(a.get("Balance") or 0)
            lines.append(f"  {a['Account']}: {bal:,.0f}")
    return "\n".join(lines)


CREDIT_ACCOUNTS = {"KTC ROP", "TTB Absolute", "CardX"}


def _record_expense(result: dict, client: SheetsClient) -> str:
    category = result["category"] or "อื่นๆ"
    client.append_transaction(
        tx_date=date.today(),
        tx_type="expense",
        category=category,
        description=result["description"],
        amount=result["amount"],
        note="",
        payment=result["payment"],
    )

    account = PAYMENT_TO_ACCOUNT.get(result["payment"], "SCB Savings")
    delta = result["amount"] if account in CREDIT_ACCOUNTS else -result["amount"]
    direction = "หักจาก" if delta < 0 else "บวกเข้า"
    icon = "📤" if delta < 0 else "📥"
    account_line = f"\n{icon} {direction} {account} {abs(delta):,.0f} บาท"
    try:
        new_balance = client.update_account_balance(account, delta)
        if new_balance is not None:
            account_line += f" (คงเหลือ {new_balance:,.0f} บาท)"
        else:
            account_line += f"\n⚠️ ไม่พบบัญชี {account} — ยอดไม่ถูกอัพเดท"
    except Exception as e:
        account_line += f"\n⚠️ อัพเดทยอดไม่สำเร็จ — {e}"

    budget_line = ""
    try:
        month = date.today().strftime("%Y-%m")
        spent = client.get_spent_by_category(month)
        budgets = {b["Category"]: b["Monthly Limit"] for b in client.get_budgets()}
        if category in budgets:
            used = spent.get(category, 0)
            limit = budgets[category]
            pct = (used / limit * 100) if limit else 0
            budget_line = f"\n📊 Budget {category}: {used:,.0f}/{limit:,.0f} ({pct:.0f}%)"
            if pct >= 100:
                budget_line += "\n🚨 เกิน budget แล้ว!"
            elif pct >= 80:
                budget_line += "\n⚠️ ใช้ไปเกิน 80% แล้ว"
    except Exception as e:
        print(f"[april] warning: {e}")

    payment_str = f" 💳 {result['payment']}" if result["payment"] else ""
    return (
        f"✅ บันทึกแล้ว: {result['description']} {result['amount']:,.0f} บาท "
        f"({category}){payment_str}{account_line}{budget_line}"
    )


def _record_income(result: dict, client: SheetsClient) -> str:
    client.append_transaction(
        tx_date=date.today(),
        tx_type="income",
        category="Income",
        description=result["description"],
        amount=result["amount"],
        note="",
        payment="",
    )
    balance_line = ""
    try:
        new_balance = client.update_account_balance("SCB Savings", result["amount"])
        if new_balance is not None:
            balance_line = f" (คงเหลือ {new_balance:,.0f} บาท)"
    except Exception as e:
        print(f"[april] warning: {e}")
    return (
        f"✅ บันทึกแล้ว: {result['description']} {result['amount']:,.0f} บาท (Income)\n"
        f"📥 บวกเข้า SCB Savings {result['amount']:,.0f} บาท{balance_line}"
    )
