import os
import requests
from dotenv import load_dotenv
from flask import Flask, request, abort

from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.exceptions import InvalidSignatureError

import router.bailey as bailey
import agents.april as april
import agents.lexie as lexie
import agents.george as george
import agents.arizona as arizona

load_dotenv()

app = Flask(__name__)

_line_config = Configuration(access_token=os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", ""))
_line_handler = WebhookHandler(os.environ.get("LINE_CHANNEL_SECRET", ""))
_telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_SECRET = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "")


def handle_message(raw_text: str) -> str:
    agent_name, text = bailey.dispatch(raw_text)

    if agent_name == "april":
        return april.handle(text)
    if agent_name == "lexie":
        return lexie.handle(text)
    if agent_name == "george":
        return george.handle(text)
    if agent_name == "arizona":
        return arizona.handle(text)
    if agent_name == "unknown":
        return "Bailey: ไม่แน่ใจว่าต้องส่งให้ใคร ลองพิมพ์ชื่อ agent นำหน้า เช่น 'Lexie: ...' หรือ 'April: ...'"
    return f"⏳ {agent_name.capitalize()} ยังไม่พร้อมใช้งาน — Phase 2"


# --- LINE webhook ---

@app.route("/callback/line", methods=["POST"])
def line_callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        _line_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"


@_line_handler.add(MessageEvent, message=TextMessageContent)
def on_line_message(event):
    text = event.message.text.strip()
    try:
        reply = handle_message(text)
    except Exception as e:
        reply = f"เกิดข้อผิดพลาด: {type(e).__name__}: {str(e)[:120]}"
    with ApiClient(_line_config) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply)],
            )
        )


# --- Telegram webhook ---

@app.route("/callback/telegram", methods=["POST"])
def telegram_callback():
    if TELEGRAM_SECRET:
        token = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if token != TELEGRAM_SECRET:
            abort(403)
    data = request.get_json(silent=True) or {}
    msg = data.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    text = msg.get("text", "").strip()
    if not text or not chat_id:
        return "OK"
    try:
        reply = handle_message(text)
    except Exception:
        reply = "เกิดข้อผิดพลาด ลองใหม่นะ"
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{_telegram_token}/sendMessage",
            json={"chat_id": chat_id, "text": reply},
            timeout=10,
        )
        resp.raise_for_status()
    except Exception:
        pass
    return "OK"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
