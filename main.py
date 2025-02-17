import discord
import asyncio
import re
import mysql.connector
import json

with open("config.json", "r") as config_file:
	config = json.load(config_file)

TOKEN = config["DISCORD_BOT_TOKEN"]
HEARHBEAT_CHANNEL_ID = config["HEARHBEAT_CHANNEL_ID"]
DB_CONFIG = config["DATABASE"]

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.webhooks = True
bot = discord.Client(intents=intents)

#Grazie chatGPT per questa regex
MESSAGE_PATTERN = re.compile(
    r"(?s)^(?P<name>.+?)\n"
    r"Online: (?P<online>[\w, ]+)\.\n"
    r"Offline: (?P<offline>[\w, ]+)\.\n" 
    r"Time: (?P<uptime>\d+)m Packs: (?P<packs>\d+)"
)

def get_db_connection():
	return mysql.connector.connect(
		host=DB_CONFIG["HOST"],
		user=DB_CONFIG["USER"],
		password=DB_CONFIG["PASSWORD"],
		database=DB_CONFIG["NAME"],
		port=DB_CONFIG["PORT"]
	)

async def save_message(timestamp, message_id, name, online, offline, uptime, packs, raw_text):
	conn = get_db_connection()
	cursor = conn.cursor()
	cursor.execute(
		"INSERT INTO HeartBeat (timestamp, message_id, name, online, offline, uptime, packs, raw_text) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
		(timestamp, message_id, name, online, offline, uptime, packs, raw_text)
	)
	conn.commit()
	cursor.close()
	conn.close()


@bot.event
async def on_ready():
	print(f"{bot.user} è online e monitorando il canale {HEARHBEAT_CHANNEL_ID}!")


@bot.event
async def on_message(message):
	print(f"Contenuto del messaggio ricevuto: {message.content}")
	if message.channel.id != HEARHBEAT_CHANNEL_ID: # or not message.webhook_id:
		return

	match = MESSAGE_PATTERN.match(message.content)
	if match:
		name = match.group("name")
		online = match.group("online")
		offline = match.group("offline")
		uptime = int(match.group("uptime"))
		packs = int(match.group("packs"))
		timestamp = message.created_at.isoformat()
		message_id = str(message.id)
		raw_text = message.content
		
		await save_message(timestamp, message_id, name, online, offline, uptime, packs, raw_text)

bot.run(TOKEN)