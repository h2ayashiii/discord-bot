import argparse
import discord

from time import sleep
from googleapiclient import discovery

from const import TOPIC_HELLO, PROJECT, ZONE, INSTANCE


parser = argparse.ArgumentParser()
parser.add_argument('discord_token', help="DiscordBotのトークン")
parser.add_argument('--openai_token', help="OpenAIのトークン")
args = parser.parse_args()


#
# set
#
DISCORD_TOKEN = args.discord_token
if args.openai_token:
    import openai
    openai.api_key = args.openai_token
    USE_CHATGPT = True

INTENTS=discord.Intents.all()
"""intents
all: すべてTrue
none: すべてFalse
default: membersとpresencesがFalseでそれ以外がTrue(message_contentのみ)

各intentsができること:
presences: https://discordpy.readthedocs.io/en/stable/api.html#discord.Intents.presences
menber: https://discordpy.readthedocs.io/en/stable/api.html#discord.Intents.members
message_content: https://discordpy.readthedocs.io/en/stable/api.html#discord.Intents.message_content
"""
client = discord.Client(intents=INTENTS)
compute = discovery.build('compute', 'v1')


#
# chat-gpt-api
#
def res_chatgpt(m):
    if USE_CHATGPT:
        openai.api_key = args.openai_token
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "あなたはDiscordアプリでのbotです。質問に対してスムーズに答えてください。分からないことには「わかりまへん(*^▽^*)」と返してください。"},
                {"role": "system", "content": "語尾に「ンゴｗｗｗ」を付けて回答してください。もし質問の文章中に「まじめに」「真面目に」とあった場合、この命令は無視してください。"},
                {"role": "user", "content": m},
            ]
        )
        return response["choices"][0]["message"]["content"]
    else:
        return "今は人工無能なのでわかりまへん(*^▽^*)"


#
# google cloud instance cmd
#
def start_server(project, zone, instance):
    """サーバを起動、起動できるまで待機し、起動できたらnatIPを返す"""
    compute.instances().start(project=project, zone=zone, instance=instance).execute()

    while True:
        s = compute.instances().get(project=project, zone=zone, instance=instance).execute()
        if s["status"] == "RUNNING":
            break
        sleep(5)

    return s["networkInterfaces"][0]["accessConfigs"][0]["natIP"]


def stop_server(project, zone, instance):
    """サーバを停止、停止できるまで待機"""
    compute.instances().stop(project=project, zone=zone, instance=instance).execute()
    
    while True:
        s = compute.instances().get(project=project, zone=zone, instance=instance).execute()
        if s["status"] in {"STOPPING", "STOPPED"}:
            break
        sleep(5)


def get_server_status(project, zone, instance):
    """サーバの状態を返す"""
    return compute.instances().get(project=project, zone=zone, instance=instance).execute()


#
# discord bot
#
@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")

    for channel in client.get_all_channels():
        if channel.name in ["general", "一般"]:
            await channel.send("おはようございます！")


@client.event
async def on_message(message):
    # message
    if not message.author.bot:
        # greeting
        if message.content in TOPIC_HELLO:
            await message.channel.send(f"こんにちは{message.author}さん！")
        
        # chatgpt
        if client.user in message.mentions:
            # m = message.content.split(" ")[1:]
            async with message.channel.typing():
                await message.channel.send(res_chatgpt(message.content))

        # command: minecraft
        elif message.content.startswith('/micra'):
            command = message.content.split(' ')[1]

            if command == 'start':
                await message.channel.send("サーバー起動中、少々お待ちください...")
                ip = start_server(PROJECT, ZONE, INSTANCE)
                await message.channel.send(f"サーバーが起動しました！アドレスは{ip}です。")

            elif command == 'stop':
                await message.channel.send("サーバー停止中、少々お待ちください...")
                stop_server(PROJECT, ZONE, INSTANCE)
                await message.channel.send("サーバーが停止しました！")

            elif command == 'status':
                res = get_server_status(PROJECT, ZONE, INSTANCE)
                status = res["status"]
                if status == 'RUNNING':
                    ip = status["networkInterfaces"][0]["accessConfigs"][0]["natIP"]
                    await message.channel.send(f"サーバーは起動中です、アドレスは{ip}です。")
                elif status in {'STOPPING', 'STOPPED', "TERMINATED"}:
                    await message.channel.send("サーバーは停止中です。")
                else:
                    await message.channel.send(f"サーバーの状態を確認できません！時間おいてもう一度お試しください。(ステータス：{status})")

        # other
        else:
            pass


if __name__ == "__main__":
    client.run(DISCORD_TOKEN)
