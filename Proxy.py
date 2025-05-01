import telebot
import socket
import socks
import threading
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('proxy_checker.log'),
        logging.StreamHandler()  # Print to console
    ]
)
logger = logging.getLogger(__name__)

# Telegram bot token (replace with your token)
BOT_TOKEN = "7827531586:AAG_fR5xyjeSzKWyX5iVwoi7SHSfr8ZbmJE"  # Replace with actual token from @BotFather
bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

# Proxy list
proxies = [
    ("116.106.104.148", 1080),
    ("159.223.202.0", 8080),
    ("34.124.190.108", 8080),
    ("74.122.101.11", 25340),
    ("199.102.104.70", 4145),
]

# Test proxy for UDP support
def test_proxy(proxy_ip, proxy_port, timeout=3):
    logger.debug(f"Testing proxy {proxy_ip}:{proxy_port}")
    try:
        sock = socks.socksocket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.set_proxy(socks.SOCKS5, proxy_ip, proxy_port)
        sock.settimeout(timeout)
        dns_query = b"\x00\x01\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x03www\x06google\x03com\x00\x00\x01\x00\x01"
        sock.sendto(dns_query, ("8.8.8.8", 53))
        sock.recvfrom(1024)
        logger.info(f"Proxy {proxy_ip}:{proxy_port} supports UDP")
        return True, None
    except (socks.ProxyError, socket.timeout, socket.error) as e:
        logger.warning(f"Proxy {proxy_ip}:{proxy_port} does NOT support UDP: {str(e)}")
        return False, str(e)
    finally:
        sock.close()

# Handle /start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.from_user.id)
    logger.info(f"Received /start from user {user_id}")
    bot.reply_to(message, "Welcome to UDP Proxy Checker Bot!\n"
                          "Use:\n"
                          "/checkproxy <IP> <PORT> - Test a single proxy\n"
                          "/checkall - Test all configured proxies")

# Handle /checkproxy command
@bot.message_handler(commands=['checkproxy'])
def check_single_proxy(message):
    user_id = str(message.from_user.id)
    logger.info(f"Received /checkproxy from user {user_id}")
    
    command = message.text.split()
    if len(command) != 3:
        bot.reply_to(message, "⚠️ Usage: /checkproxy <IP> <PORT>")
        return
    
    proxy_ip, proxy_port = command[1], command[2]
    try:
        proxy_port = int(proxy_port)
    except ValueError:
        bot.reply_to(message, "❌ Port must be an integer!")
        return

    bot.reply_to(message, f"🔄 Testing {proxy_ip}:{proxy_port}...")
    is_active, error = test_proxy(proxy_ip, proxy_port)
    status = "✅ Supports UDP" if is_active else f"❌ Does not support UDP ({error})"
    bot.reply_to(message, f"📋 Proxy {proxy_ip}:{proxy_port} - {status}")
    logger.info(f"Checked proxy {proxy_ip}:{proxy_port} for user {user_id}: {status}")

# Handle /checkall command
@bot.message_handler(commands=['checkall'])
def check_all_proxies(message):
    user_id = str(message.from_user.id)
    logger.info(f"Received /checkall from user {user_id}")
    
    bot.reply_to(message, "🔄 Testing all proxies...")
    response = "📋 Proxy Status:\n"
    
    with ThreadPoolExecutor(max_workers=len(proxies)) as executor:
        future_to_proxy = {
            executor.submit(test_proxy, ip, port): (ip, port)
            for ip, port in proxies
        }
        for future in as_completed(future_to_proxy):
            ip, port = future_to_proxy[future]
            try:
                is_active, error = future.result()
                status = "✅ Supports UDP" if is_active else f"❌ Does not support UDP ({error})"
                response += f"{ip}:{port} - {status}\n"
            except Exception as e:
                response += f"{ip}:{port} - ❌ Error ({str(e)})\n"
                logger.error(f"Proxy {ip}:{port} test failed: {e}")

    bot.reply_to(message, response)
    logger.info(f"Sent proxy status to user {user_id}")

# Start the bot
try:
    logger.info("Bot is polling...")
    bot.infinity_polling()
except Exception as e:
    logger.error(f"Bot polling failed: {e}")
    exit(1)