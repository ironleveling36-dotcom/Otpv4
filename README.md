# OTPCart Telegram Bot — v4 (Wallet + Admin + Swiggy Checker + Multi-SMS)

A Telegram OTP-number bot powered by OTPDoctor, with a full **Wallet System**,
**Admin Control Panel**, **Top Services**, **Swiggy Checker**, **Multi-SMS**,
an improved **cancellation system**, and a robust **Auto-Retry** engine.

## 🆕 What's new in v4

### 📞 Number display & copy format
- Numbers display with the country code (e.g. `+91 9876543210`).
- The number is shown in a tap-to-copy code span containing **only the local
  10-digit number** (no country code) — tapping copies `9876543210`.

### 🍔 Swiggy Checker
- Dedicated **🍔 Swiggy Checker** button on the dashboard.
- Admin configures the provider **Service ID** used by the checker
  (Admin → Services Management → *Configure Swiggy Service ID*).
- Flow: auto-purchase number → `POST https://checker.otpcart.xyz/api/check-swiggy`
  with `{"mobile": "XXXXXXXXXX"}`:
  - `unregistered` → number is delivered, OTP flow continues normally.
  - `registered` → number is **never delivered**; it is auto-released after
    5 minutes and the wallet is refunded.

### 📩 Multi-SMS & Check SMS
- Supports multiple OTP/SMS messages per activation.
- **📩 Check SMS** button to manually refresh and view incoming messages.
- All messages are listed with timestamps.

### ⏱️ Improved cancellation
- Users can cancel **only after 3 minutes** (a live countdown shows when it unlocks).
- On cancel, the number stays visible until the provider confirms — with live
  status: Active → Waiting OTP → OTP Received → Cancelling → Cancelled / Expired.

### 🔁 Auto-Retry (expanded)
- Retries on `No Number Available`, `Try Again`, `No Stock`, `Temporary Error`,
  `Provider Error`, and similar — every **2s, up to 20 attempts**.
- Stops immediately when a valid number is received.
- On total failure → cancel + automatic wallet refund + user notification.

### 🧾 Logging & stability
- Detailed logs for purchases, OTP receipts, cancellations, refunds, wallet
  transactions, admin actions, and Swiggy checks (Admin → *View System Logs*).
- Refund guards prevent double-refunds / balance drift.

## ✨ Features

### 💳 Wallet System
- Users recharge their wallet via **QR code + UPI** (managed by admin).
- User enters an amount → sees QR/UPI → taps **✅ I Paid**.
- Admin gets an instant notification with **Approve / Reject** buttons.
- On approval, the balance is credited automatically and the user is notified.
- Services are purchased directly from wallet balance — the bot verifies funds
  and deducts the cost before activation.

### 💸 Automatic Refunds
- If a number is **cancelled** before any OTP arrives → amount refunded.
- If **no OTP arrives within 3 minutes** → number auto-cancelled + refunded.
- If a number **expires** with no messages → refunded.
- If all auto-retry attempts fail → refunded.

### 🔁 Auto-Retry System
- On provider errors (`No Number Available`, `Try Again`, etc.), the bot
  automatically retries the **same service every 2 seconds, up to 20 attempts**.
- Stops as soon as a number is received.
- If all 20 attempts fail → service cancelled + wallet refunded.

### ⭐ Top Services
- Admin can mark any service as a **Top Service**.
- Top services appear as **pinned/highlighted 🔥 buttons** at the top of the main menu.

### 🔧 Admin Panel (`/admin`)
- **Services:** add / edit / delete, enable / disable, change prices, mark as Top.
- **User Wallets:** search users, view balances, credit / debit, view tx logs.
- **Transactions:** view full system transaction history.
- **Notifications:** broadcast a message to all users.
- **Payment Details:** update UPI ID and QR-code image at any time.

## 🚀 Setup

### Environment variables
| Variable      | Required | Description                                              |
|---------------|----------|----------------------------------------------------------|
| `BOT_TOKEN`   | ✅       | Telegram bot token from @BotFather.                      |
| `ADMIN_IDS`   | ✅       | Comma-separated Telegram user IDs of admins, e.g. `12345,67890`. |
| `OTP_API_KEY` | optional | OTPDoctor API key (defaults to the bundled key).         |

> Get your numeric Telegram ID from [@userinfobot](https://t.me/userinfobot).

### Install & run
```bash
pip install -r requirements.txt
export BOT_TOKEN="your_token_here"
export ADMIN_IDS="123456789"        # your Telegram ID
python bot.py
```

## 🗂️ Files
| File           | Purpose                                                        |
|----------------|---------------------------------------------------------------|
| `bot.py`       | Main bot: handlers, wallet flow, admin panel, OTP + auto-retry |
| `database.py`  | SQLite persistence (users, wallets, services, tx, settings)   |
| `keyboards.py` | All inline keyboards (user + admin + wallet)                  |
| `otp_api.py`   | OTPDoctor API wrapper                                          |
| `storage.py`   | In-memory active-order tracking                               |
| `config.py`    | Config + timing (3-min OTP timeout)                          |

## 📝 Notes
- Wallet balances, services, transactions and payment settings persist in a local
  `bot.db` SQLite file (created automatically on first run).
- The first time a country's service catalog is opened, services are auto-synced
  from the provider into the local DB so the admin can manage/price them.
