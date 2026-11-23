import os
import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    ContextTypes, filters
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
DB = "store.db"

PRODUCTS = {
    "phone1": ("Смартфон Nova X", "Смартфоны", 29990, "Современный смартфон. Демонстрационный товар."),
    "phone2": ("Смартфон Pixel Pro", "Смартфоны", 45990, "Камера и яркий экран. Демонстрационный товар."),
    "laptop1": ("Ноутбук WorkBook 15", "Компьютеры", 62990, "Ноутбук для учёбы и работы. Демонстрационный товар."),
    "head1": ("Наушники SoundMax", "Аксессуары", 4990, "Беспроводные наушники. Демонстрационный товар."),
    "watch1": ("Смарт-часы Active", "Аксессуары", 6990, "Умные часы. Демонстрационный товар."),
}

def db():
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS orders
        (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, username TEXT,
         customer TEXT, phone TEXT, items TEXT, total INTEGER, status TEXT DEFAULT 'Новый')""")
    con.commit()
    return con

def money(value):
    return f"{value:,}".replace(",", " ") + " ₽"

def cart(context):
    return context.user_data.setdefault("cart", {})

def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 Смартфоны", callback_data="cat:Смартфоны")],
        [InlineKeyboardButton("💻 Компьютеры", callback_data="cat:Компьютеры")],
        [InlineKeyboardButton("🎧 Аксессуары", callback_data="cat:Аксессуары")],
        [InlineKeyboardButton("🛒 Корзина", callback_data="cart"),
         InlineKeyboardButton("📦 Мои заказы", callback_data="orders")],
        [InlineKeyboardButton("ℹ️ Поддержка", callback_data="support")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛍 Добро пожаловать в TECHNO STORE!\n\n"
        "Выберите категорию каталога. Сейчас здесь демонстрационные товары и цены.",
        reply_markup=main_keyboard()
    )

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data

    if data.startswith("cat:"):
        category = data.split(":", 1)[1]
        rows = []
        for pid, p in PRODUCTS.items():
            if p[1] == category:
                rows.append([InlineKeyboardButton(f"{p[0]} — {money(p[2])}", callback_data=f"item:{pid}")])
        rows.append([InlineKeyboardButton("⬅️ В меню", callback_data="menu")])
        await q.edit_message_text(f"Категория: {category}", reply_markup=InlineKeyboardMarkup(rows))

    elif data.startswith("item:"):
        pid = data.split(":", 1)[1]
        p = PRODUCTS.get(pid)
        if not p:
            return
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Добавить в корзину", callback_data=f"add:{pid}")],
            [InlineKeyboardButton("⬅️ Назад", callback_data=f"cat:{p[1]}")]
        ])
        await q.edit_message_text(f"**{p[0]}**\nЦена: {money(p[2])}\n\n{p[3]}",
                                  parse_mode="Markdown", reply_markup=keyboard)

    elif data.startswith("add:"):
        pid = data.split(":", 1)[1]
        if pid in PRODUCTS:
            c = cart(context)
            c[pid] = c.get(pid, 0) + 1
            await q.edit_message_text(f"✅ Добавлено: {PRODUCTS[pid][0]}\nВ корзине: {sum(c.values())} шт.",
                                      reply_markup=InlineKeyboardMarkup([
                                          [InlineKeyboardButton("🛒 Открыть корзину", callback_data="cart")],
                                          [InlineKeyboardButton("🏠 В меню", callback_data="menu")]
                                      ]))

    elif data == "cart":
        c = cart(context)
        if not c:
            await q.edit_message_text("Корзина пока пустая.", reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 В меню", callback_data="menu")]
            ]))
            return
        lines, total = [], 0
        for pid, qty in c.items():
            p = PRODUCTS[pid]
            subtotal = p[2] * qty
            total += subtotal
            lines.append(f"{p[0]} × {qty} — {money(subtotal)}")
        await q.edit_message_text("🛒 Ваша корзина:\n\n" + "\n".join(lines) +
                                  f"\n\nИтого: {money(total)}",
                                  reply_markup=InlineKeyboardMarkup([
                                      [InlineKeyboardButton("✅ Оформить заказ", callback_data="checkout")],
                                      [InlineKeyboardButton("🗑 Очистить корзину", callback_data="clear")],
                                      [InlineKeyboardButton("🏠 В меню", callback_data="menu")]
                                  ]))

    elif data == "clear":
        context.user_data["cart"] = {}
        await q.edit_message_text("Корзина очищена.", reply_markup=main_keyboard())

    elif data == "checkout":
        if not cart(context):
            await q.edit_message_text("Корзина пуста.")
            return
        context.user_data["checkout_step"] = "customer"
        await q.edit_message_text("Напишите ваше имя для оформления заказа:")

    elif data == "orders":
        con = db()
        rows = con.execute("SELECT id, total, status FROM orders WHERE user_id=? ORDER BY id DESC LIMIT 10",
                           (q.from_user.id,)).fetchall()
        con.close()
        if not rows:
            msg = "У вас пока нет заказов."
        else:
            msg = "📦 Ваши заказы:\n" + "\n".join(
                f"№{r[0]} — {money(r[1])} — {r[2]}" for r in rows)
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 В меню", callback_data="menu")]
        ]))

    elif data == "support":
        await q.edit_message_text("По вопросам заказа напишите администратору магазина.",
                                  reply_markup=InlineKeyboardMarkup([
                                      [InlineKeyboardButton("🏠 В меню", callback_data="menu")]
                                  ]))
    elif data == "menu":
        await q.edit_message_text("Главное меню TECHNO STORE", reply_markup=main_keyboard())

async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get("checkout_step")
    if not step:
        await update.message.reply_text("Откройте меню командой /start.")
        return
    value = update.message.text.strip()
    if step == "customer":
        context.user_data["customer"] = value[:100]
        context.user_data["checkout_step"] = "phone"
        await update.message.reply_text("Укажите номер телефона для связи (или напишите «нет»):")
    elif step == "phone":
        c = cart(context)
        if not c:
            context.user_data.pop("checkout_step", None)
            await update.message.reply_text("Корзина пуста. Откройте /start.")
            return
        lines, total = [], 0
        for pid, qty in c.items():
            p = PRODUCTS[pid]
            total += p[2] * qty
            lines.append(f"{p[0]} × {qty}")
        items = "; ".join(lines)
        con = db()
        cur = con.execute(
            "INSERT INTO orders(user_id, username, customer, phone, items, total) VALUES(?,?,?,?,?,?)",
            (update.effective_user.id, update.effective_user.username or "",
             context.user_data.get("customer", ""), value[:50], items, total))
        order_id = cur.lastrowid
        con.commit()
        con.close()
        context.user_data["cart"] = {}
        context.user_data.pop("checkout_step", None)
        await update.message.reply_text(
            f"✅ Заказ №{order_id} принят!\n{items}\nИтого: {money(total)}\n"
            "Это заявка, а не оплата. Администратор свяжется для подтверждения."
        )
        if ADMIN_ID:
            await context.bot.send_message(
                ADMIN_ID,
                f"🆕 Заказ №{order_id}\nПокупатель: {context.user_data.get('customer','')}\n"
                f"Контакт: {value}\nTelegram: @{update.effective_user.username or 'не указан'}\n"
                f"{items}\nИтого: {money(total)}"
            )

async def admin_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ADMIN_ID or update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Команда доступна только администратору.")
        return
    con = db()
    rows = con.execute("SELECT id, customer, phone, items, total, status FROM orders ORDER BY id DESC LIMIT 20").fetchall()
    con.close()
    if not rows:
        await update.message.reply_text("Заказов пока нет.")
        return
    for r in rows:
        await update.message.reply_text(
            f"Заказ №{r[0]} — {r[5]}\nКлиент: {r[1]}\nКонтакт: {r[2]}\n"
            f"{r[3]}\nИтого: {money(r[4])}"
        )

def main():
    if not TOKEN:
        raise RuntimeError("Set BOT_TOKEN environment variable")
    db().close()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("orders_admin", admin_orders))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message))
    app.run_polling()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
