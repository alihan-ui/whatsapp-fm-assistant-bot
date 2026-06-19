
import os
import json
import requests
from datetime import datetime, date
from flask import Flask, request, jsonify
 
app = Flask(__name__)
 
# ─── НАСТРОЙКИ ──────────────────────────────────────────────────────────────
 
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")          # маркер доступа из Meta
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")        # Phone Number ID из Meta
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "fm_math_verify_2026")  # подтверждение маркера для Webhook
ADMIN_PHONE = os.getenv("ADMIN_PHONE")                # твой номер для /admin, формат: 77789999999
 
GRAPH_URL = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"
STATS_FILE = "stats.json"
 
 
# ─── СТАТИСТИКА ─────────────────────────────────────────────────────────────
 
def load_stats() -> dict:
    if not os.path.exists(STATS_FILE):
        return {"users": {}, "buttons": {}}
    with open(STATS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
 
def save_stats(stats: dict):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
 
def track(phone: str, name: str, button: str = None):
    stats = load_stats()
    today = str(date.today())
    now = datetime.now().isoformat(timespec="seconds")
 
    if phone not in stats["users"]:
        stats["users"][phone] = {
            "name": name,
            "first_seen": today,
            "last_seen": now,
            "count": 0,
            "buttons": {}
        }
 
    u = stats["users"][phone]
    u["name"] = name
    u["last_seen"] = now
    u["count"] = u.get("count", 0) + 1
 
    if button:
        u["buttons"][button] = u["buttons"].get(button, 0) + 1
        stats["buttons"][button] = stats["buttons"].get(button, 0) + 1
 
    save_stats(stats)
 
 
# ─── ОТПРАВКА СООБЩЕНИЙ ─────────────────────────────────────────────────────
 
def send_text(to: str, text: str):
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    _post(payload)
 
def send_buttons(to: str, body_text: str, buttons: list):
    """buttons: список словарей {'id': 'btn_id', 'title': 'Текст'} максимум 3 шт."""
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body_text},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": b["id"], "title": b["title"]}}
                    for b in buttons
                ]
            }
        }
    }
    _post(payload)
 
def send_list(to: str, body_text: str, button_label: str, sections: list):
    """sections: [{'title': 'Раздел', 'rows': [{'id':'x','title':'..'}]}]"""
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": body_text},
            "action": {
                "button": button_label,
                "sections": sections
            }
        }
    }
    _post(payload)
 
def _post(payload: dict):
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    r = requests.post(GRAPH_URL, headers=headers, json=payload)
    if r.status_code >= 400:
        print("WhatsApp API error:", r.status_code, r.text)
 
 
# ─── МЕНЮ ───────────────────────────────────────────────────────────────────
 
MAIN_MENU_SECTIONS = [
    {
        "title": "Бөлімдер",
        "rows": [
            {"id": "menu_formulas", "title": "📖 Формула жинақтары"},
            {"id": "menu_nuska", "title": "📝 Нұсқа талдаулар"},
            {"id": "menu_prof", "title": "🎯 Мамандықтар тізімі"},
            {"id": "menu_checklists", "title": "✅ Чек-листтер"},
            {"id": "menu_streams", "title": "🎥 12 сағаттық эфирлер"},
            {"id": "menu_books", "title": "📚 Есеп жинақтары"},
            {"id": "menu_guides", "title": "📘 Гайдтар"},
            {"id": "menu_specs", "title": "📄 Спецификациялар"},
        ]
    }
]
 
def send_main_menu(to: str):
    send_list(
        to,
        "Қажетті бөлімді таңдаңыз😊:",
        "Мәзір",
        MAIN_MENU_SECTIONS
    )
 
def send_welcome(to: str):
    send_text(
        to,
        "Сәлем 😊\n\n"
        "Бұл сіздің математикадан ҰБТ-ға дайындығыңызды жеңілдетуге арналған заманауи көмекшіңіз.\n\n"
        "Өзіңізге керекті батырманы басып, қажетті ақпаратты ала аласыз🫶🏻"
    )
    send_main_menu(to)
 
 
# ─── ОБРАБОТКА КНОПОК ───────────────────────────────────────────────────────
 
def handle_button(to: str, button_id: str, phone: str, name: str):
    track(phone, name, button_id)
 
    if button_id == "menu_formulas":
        send_list(to, "Формула жинағын таңдаңыз😊:", "Таңдау", [
            {"title": "Формулалар", "rows": [
                {"id": "f_fm", "title": "FM толық формула жинағы"},
                {"id": "f_geo", "title": "Геометрия формулалары"},
            ]}
        ])
    elif button_id == "menu_prof":
        send_list(to, "Бағытты таңдаңыз😊:", "Таңдау", [
            {"title": "Мамандықтар", "rows": [
                {"id": "p_phys", "title": "Математика + Физика"},
                {"id": "p_info", "title": "Математика + Информатика"},
                {"id": "p_geo", "title": "Математика + География"},
            ]}
        ])
    elif button_id == "menu_checklists":
        send_list(to, "Чек-лист таңдаңыз😊:", "Таңдау", [
            {"title": "Чек-листтер", "rows": [
                {"id": "c_stereo", "title": "Стереометрия"},
                {"id": "c_integral", "title": "Интеграл"},
                {"id": "c_module", "title": "Модуль және теңсіздіктер"},
                {"id": "c_percent", "title": "Пайыз табу"},
                {"id": "c_degree", "title": "Дәреже және оның қасиеттері"},
                {"id": "c_ekoe", "title": "ЕКОЕ және ЕҮОБ"},
            ]}
        ])
    elif button_id == "menu_books":
        send_list(to, "Есеп жинағын таңдаңыз😊:", "Таңдау", [
            {"title": "Есеп жинақтары", "rows": [
                {"id": "b_rust", "title": "Рустюмова"},
                {"id": "b_red1", "title": "Қызыл кітап 1"},
                {"id": "b_scan_kz", "title": "Scanavi Қазақша"},
                {"id": "b_scan_v", "title": "Skanavi gruppa V"},
                {"id": "b_scan_a", "title": "Skanavi Gruppa A"},
            ]}
        ])
    elif button_id == "menu_streams":
        send_text(to,
            "🎥 12 сағаттық эфирлер\n\n"
            "1️⃣ https://www.youtube.com/live/5ZJyxKkKKM0\n"
            "2️⃣ https://www.youtube.com/live/8g4nBZuqSyg\n"
            "3️⃣ https://www.youtube.com/live/LQI2qCXN2R4\n"
            "4️⃣ https://www.youtube.com/live/4JrjVvrqA6Y\n"
            "5️⃣ https://www.youtube.com/live/v4ViVRkwfPM\n"
            "6️⃣ https://www.youtube.com/live/Py9KJ88uvQs\n"
            "7️⃣ https://www.youtube.com/live/AEaxkQJ9C_E\n"
            "8️⃣ https://www.youtube.com/live/7iWfTWMcnZY\n"
            "9️⃣ https://www.youtube.com/live/W2vAd0WphBo\n"
            "🔟 https://www.youtube.com/live/D4R6tUm40LU"
        )
    elif button_id == "menu_nuska":
        send_text(to,
            "📝 Нұсқа талдаулар\n\n"
            "1️⃣ https://www.youtube.com/live/X8E_LKEvCQQ\n"
            "2️⃣ https://www.youtube.com/live/Hr_Lcc8SDrA\n"
            "3️⃣ https://www.youtube.com/live/qszjXWW-kzg\n"
            "4️⃣ https://www.youtube.com/live/RBI30Sl7znE\n"
            "5️⃣ https://www.youtube.com/live/dT0Zusf1q58\n"
            "6️⃣ https://www.youtube.com/live/GToZYK7EGqQ\n"
            "7️⃣ https://youtu.be/J4u4xVYWTKk\n"
            "8️⃣ https://www.youtube.com/live/WX3s4lVT_Do\n"
            "9️⃣ https://www.youtube.com/live/fCnZPZ1Rw7w\n"
            "🔟 https://www.youtube.com/live/W5PhjoWd77c\n"
            "1️⃣1️⃣ https://www.youtube.com/live/dpzWNqCqL8k"
        )
    elif button_id in ("menu_guides", "menu_specs", "f_fm", "f_geo", "p_phys", "p_info", "p_geo",
                        "c_stereo", "c_integral", "c_module", "c_percent", "c_degree", "c_ekoe",
                        "b_rust", "b_red1", "b_scan_kz", "b_scan_v", "b_scan_a"):
        # Здесь нужно отправить PDF-документ через media_id (загруженный заранее в Meta)
        # send_document(to, MEDIA_IDS[button_id])
        send_text(to, "Үздік нәтиже сізді күтеді 🏆\n\nДайындықты жалғастырамыз ба? 😇")
    else:
        send_main_menu(to)
 
 
# ─── WEBHOOK ────────────────────────────────────────────────────────────────
 
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
 
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403
 
 
@app.route("/webhook", methods=["POST"])
def receive_webhook():
    data = request.get_json()
 
    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]["value"]
 
        if "messages" not in changes:
            return jsonify({"status": "ok"}), 200
 
        message = changes["messages"][0]
        contact = changes["contacts"][0]
        phone = message["from"]
        name = contact["profile"]["name"]
 
        # Команда /id
        if message.get("type") == "text" and message["text"]["body"].strip() == "/id":
            track(phone, name, "/id")
            send_text(phone, f"🪪 Сіздің телефон нөміріңіз: {phone}")
            return jsonify({"status": "ok"}), 200
 
        # Команда /admin
        if message.get("type") == "text" and message["text"]["body"].strip() == "/admin":
            if ADMIN_PHONE and phone == ADMIN_PHONE:
                stats = load_stats()
                today = str(date.today())
                users = stats.get("users", {})
                buttons = stats.get("buttons", {})
 
                total_users = len(users)
                new_today = sum(1 for u in users.values() if u.get("first_seen") == today)
                total_actions = sum(u.get("count", 0) for u in users.values())
                top_buttons = sorted(buttons.items(), key=lambda x: x[1], reverse=True)[:5]
                top_text = "\n".join(f"{i+1}. {b} — {c}" for i, (b, c) in enumerate(top_buttons)) or "—"
 
                send_text(phone,
                    f"📊 Админ панель\n\n"
                    f"👥 Барлық пайдаланушылар: {total_users}\n"
                    f"🆕 Бүгін жаңалар: {new_today}\n"
                    f"🖱 Жалпы әрекеттер: {total_actions}\n\n"
                    f"🔥 Топ-5 батырмалар:\n{top_text}"
                )
            # если не админ — молчим
            return jsonify({"status": "ok"}), 200
 
        # Нажатие интерактивной кнопки/списка
        if message.get("type") == "interactive":
            interactive = message["interactive"]
            if interactive["type"] == "list_reply":
                button_id = interactive["list_reply"]["id"]
            elif interactive["type"] == "button_reply":
                button_id = interactive["button_reply"]["id"]
            else:
                button_id = None
 
            if button_id:
                handle_button(phone, button_id, phone, name)
            return jsonify({"status": "ok"}), 200
 
        # Обычное текстовое сообщение -> показать меню
        track(phone, name)
        send_welcome(phone)
 
    except (KeyError, IndexError) as e:
        print("Webhook parse skip:", e)
 
    return jsonify({"status": "ok"}), 200
 
 
@app.route("/", methods=["GET"])
def health():
    return "FM Math WhatsApp Bot is running", 200
 
 
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    a
