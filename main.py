import re, os, sys
import discord, httpx, yaml

file_path = "./config.yml"

if not os.path.isfile(file_path):
    data = {
        "token": "",
        "check_channel_id": 0,
        "send_channel_id": 0,
        "disregard_role_id": 0
    }
    with open(file_path, 'w') as file:
        yaml.dump(data, file)
    sys.exit()

with open(file_path, 'r') as file:
    data = yaml.safe_load(file)
token = data["token"]
check_channel_id = data["check_channel_id"]
send_channel_id = data["send_channel_id"]
disregard_role_id = data["disregard_role_id"]

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

mc_url = ["https://api.mojang.com/users/profiles/minecraft", "https://api.geysermc.org/v2/xbox/xuid"]

async def mcid_check(url: str)->bool:
    async with httpx.AsyncClient(http2=True) as client:
        response = await client.get(url)
    if response.status_code == 200:
        return True
    else:
        return False

@client.event
async def on_message(message):
    if message.author == client.user or message.channel.id != check_channel_id:
        return
    if not isinstance(message.author, discord.Member):
        return
    author_roles = [role.id for role in message.author.roles]
    patterns_to_remove = [r"\s*\(?be\)?", r"\s*\(?java\)?"]
    if disregard_role_id in author_roles:
        return
    message_content = message.content
    pattern_updated = r"(?:【)?mcid(?:】)?\s*(.+)"
    mcid_match_updated = re.search(pattern_updated, message_content, re.IGNORECASE)
    mcid = mcid_match_updated.group(1) if mcid_match_updated else "MCID not found"
    for pattern in patterns_to_remove:
        mcid = re.sub(pattern, "", mcid, flags=re.IGNORECASE)
    if mcid == "MCID not found":
        return
    if await mcid_check(f"{mc_url[0]}/{mcid}"):
        message = f"{message.author.name}の{mcid}はJava版のアカウントです。"
    elif await mcid_check(f"{mc_url[1]}/{mcid}"):
        message = f"{message.author.name}の{mcid}は統合版のアカウントです。"
    else:
        message = f"{message.author.name}の{mcid}の確認ができませんでした。"
    channel = client.get_channel(send_channel_id)
    if channel:
        await channel.send(message)

client.run(token)
