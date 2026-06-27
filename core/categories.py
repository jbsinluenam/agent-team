EXPENSE_KEYWORDS = {
    "Food": ["กาแฟ", "ข้าว", "อาหาร", "ชา", "ขนม", "กิน", "ร้านอาหาร", "ก๋วยเตี๋ยว", "food", "coffee"],
    "Transportation": ["grab", "taxi", "bts", "mrt", "น้ำมัน", "เติมน้ำมัน", "ทางด่วน", "ค่ารถ", "fuel"],
    "Health": ["หมอ", "ยา", "โรงพยาบาล", "คลินิก", "doctor", "pharmacy"],
    "Entertainment": ["หนัง", "เกม", "netflix", "spotify", "game", "movie"],
    "Housing": ["ค่าเช่า", "ไฟฟ้า", "น้ำประปา", "internet", "rent"],
}

INCOME_KEYWORDS = ["เงินเดือน", "ได้เงิน", "รับเงิน", "โบนัส", "salary", "bonus", "income"]

PAYMENT_MAP = {
    "ktc": "KTC ROP",
    "rop": "KTC ROP",
    "ttb": "TTB Absolute",
    "absolute": "TTB Absolute",
    "cardx": "CardX",
    "cash": "Cash",
    "เงินสด": "Cash",
    "paotang": "Paotang",
    "เป๋าตัง": "Paotang",
}

PAYMENT_TO_ACCOUNT = {
    "": "SCB Savings",
    "KTC ROP": "KTC ROP",
    "TTB Absolute": "TTB Absolute",
    "Paotang": "Paotang",
}
