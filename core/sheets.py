import json
import os
from datetime import date

import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


class SheetsClient:
    def __init__(self):
        creds_json = os.environ.get("GOOGLE_SHEETS_CREDENTIALS_JSON", "")
        spreadsheet_id = os.environ["GOOGLE_SHEETS_SPREADSHEET_ID"]

        if creds_json:
            creds_dict = json.loads(creds_json)
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        else:
            creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)

        gc = gspread.authorize(creds)
        self._spreadsheet = gc.open_by_key(spreadsheet_id)
        self._transactions = self._spreadsheet.worksheet("Transactions")
        self._budget = self._spreadsheet.worksheet("Budget")
        self._accounts = self._spreadsheet.worksheet("Accounts")

    def append_transaction(self, tx_date: date, tx_type: str, category: str,
                           description: str, amount: float, note: str = "",
                           payment: str = "") -> None:
        row = [tx_date.isoformat(), tx_type, category, description, amount, note, payment]
        self._transactions.append_row(row)

    def get_transactions(self, month: str = "") -> list[dict]:
        records = self._transactions.get_all_records()
        if month:
            records = [r for r in records if str(r.get("Date", "")).startswith(month)]
        return records

    def get_budgets(self) -> list[dict]:
        return self._budget.get_all_records()

    def get_accounts(self) -> list[dict]:
        return self._accounts.get_all_records()

    def update_account_balance(self, account: str, delta: float) -> float | None:
        records = self._accounts.get_all_records()
        for i, row in enumerate(records, start=2):
            if row["Account"] == account:
                new_balance = float(row["Balance"]) + delta
                self._accounts.update_cell(i, 3, round(new_balance, 2))
                return round(new_balance, 2)
        return None

    def get_spent_by_category(self, month: str) -> dict[str, float]:
        records = self.get_transactions(month)
        spent: dict[str, float] = {}
        for r in records:
            if r.get("Type") == "expense":
                cat = r["Category"]
                spent[cat] = spent.get(cat, 0) + r["Amount"]
        return spent
