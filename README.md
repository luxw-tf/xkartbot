# Xkart Bot

A Telegram bot designed to sell Twitter Premium and other digital services, fully integrated with a crypto payment flow and an admin dashboard right inside Telegram.

## Features
- **Crypto Payments**: Easy instructions for users to pay via EVM wallets (USDT/USDC on BSC, Polygon, Arbitrum, Optimism).
- **Automated Order Processing**: Users submit their Transaction Hash, which is verified by an admin.
- **Admin Commands**: Manage your business directly from Telegram.
  - `/pending`: View all pending orders and easily complete them.
  - `/broadcast <message>`: Send an announcement to every user who has ever started the bot.
  - `/setevent <message>`: Update the text of the "Event" button in the menu.
- **Dynamic Menus**: Fully interactive inline keyboards for smooth user experience.

## Setup Instructions

### 1. Requirements
- Python 3.8+
- `pip`
- A Telegram Bot Token from [@BotFather](https://t.me/BotFather)

### 2. Installation (Linux/Debian)
Clone the repository and install the dependencies:
```bash
git clone https://github.com/luxw-tf/xkartbot.git
cd xkartbot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configuration
Make sure your `config.py` is configured with your Bot Token and your Telegram Username for Admin access.

### 4. Running the Bot
To run the bot in the background, you can use `tmux`:
```bash
tmux new -s bot
python3 main.py
```
*(Press `Ctrl + B`, then `D` to safely detach and leave the bot running in the background).*

### 5. Admin Setup
Once the bot is online, go to Telegram, start the bot, and send `/setadmin` to register yourself as the administrator.
