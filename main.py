import asyncio

from crypto_bot import CryptoBot

if __name__ == "__main__":
    bot = CryptoBot()
    asyncio.run(bot.run_cycle())