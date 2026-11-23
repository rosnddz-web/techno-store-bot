# TECHNO STORE Telegram bot

## Included
- Demo catalog: smartphones, computers and accessories
- Inline product pages and cart
- Order request flow (name + contact)
- SQLite order storage
- Optional admin notifications and `/orders_admin`

## Run locally
1. Install Python 3.10+
2. `pip install -r requirements.txt`
3. Set `BOT_TOKEN` and optionally `ADMIN_ID`
4. `python bot.py`

## Railway
Connect this GitHub repository to a Railway service. Add variables:
- `BOT_TOKEN` = fresh token from @BotFather
- `ADMIN_ID` = your Telegram numeric user ID (optional)

The service runs as a worker using the Procfile. The listed products and prices are demo data; edit `PRODUCTS` in `bot.py` before real sales. The bot creates order requests only; it does not take payments or verify stock/delivery.
