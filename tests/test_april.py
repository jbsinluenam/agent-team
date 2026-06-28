from unittest.mock import MagicMock
from agents.april import handle


def make_client(transactions=None, accounts=None, budgets=None, spent=None, new_balance=None):
    client = MagicMock()
    client.get_transactions.return_value = transactions or []
    client.get_accounts.return_value = accounts or []
    client.get_budgets.return_value = budgets or []
    client.get_spent_by_category.return_value = spent or {}
    client.update_account_balance.return_value = new_balance
    return client


def test_expense_records_to_sheets():
    client = make_client()
    result = handle("กาแฟ 65", client)
    assert "บันทึกแล้ว" in result
    assert "65" in result
    assert "Food" in result
    client.append_transaction.assert_called_once()
    kwargs = client.append_transaction.call_args[1]
    assert kwargs["tx_type"] == "expense"
    assert kwargs["amount"] == 65.0
    assert kwargs["category"] == "Food"


def test_expense_with_payment_method():
    client = make_client(new_balance=397.0)
    result = handle("กาแฟ 65 ktc", client)
    assert "KTC ROP" in result
    client.update_account_balance.assert_called_once_with("KTC ROP", 65.0)


def test_expense_deducts_scb_by_default():
    client = make_client(new_balance=49935.0)
    handle("กาแฟ 65", client)
    client.update_account_balance.assert_called_once_with("SCB Savings", -65.0)


def test_income_records_to_sheets():
    client = make_client(new_balance=154000.0)
    result = handle("เงินเดือน 50000", client)
    assert "บันทึกแล้ว" in result
    assert "50,000" in result
    kwargs = client.append_transaction.call_args[1]
    assert kwargs["tx_type"] == "income"
    assert kwargs["amount"] == 50000.0


def test_summary_keyword():
    client = make_client(
        transactions=[
            {"Type": "income", "Amount": 1000, "Category": "Income"},
            {"Type": "expense", "Amount": 200, "Category": "Food"},
        ],
        accounts=[
            {"Account": "SCB Savings", "Type": "savings", "Balance": "50000", "Group": "Daily"},
        ],
    )
    result = handle("summary", client)
    assert "Summary" in result
    assert "1,000" in result
    assert "200" in result
    assert "SCB Savings" in result


def test_summary_thai_keyword():
    client = make_client()
    result = handle("สรุป", client)
    assert "Summary" in result


def test_balance_keyword():
    client = make_client(
        accounts=[
            {"Account": "SCB Savings", "Type": "savings", "Balance": "50000", "Group": "Daily"},
            {"Account": "KTC ROP", "Type": "credit", "Balance": "397", "Group": "Daily"},
        ]
    )
    result = handle("balance", client)
    assert "SCB Savings" in result
    assert "50,000" in result
    assert "KTC ROP" in result


def test_expense_deducts_paotung():
    client = make_client(new_balance=381.0)
    result = handle("ข้าว 91 เป๋าตัง", client)
    assert "Paotung" in result
    assert "381" in result
    client.update_account_balance.assert_called_once_with("Paotung", -91.0)


def test_expense_warns_when_account_not_found():
    client = make_client(new_balance=None)
    result = handle("กาแฟ 65 เป๋าตัง", client)
    assert "ไม่พบบัญชี" in result


def test_unrecognized_returns_help():
    client = make_client()
    result = handle("สวัสดี", client)
    assert "ไม่เจอ" in result
    client.append_transaction.assert_not_called()
