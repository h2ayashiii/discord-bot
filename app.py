import discord
# import openai
import os

from time import sleep
from googleapiclient import discovery

from const import TOPIC_HELLO, PROJECT, ZONE, INSTANCE


#
# set
#
# openai.api_key = os.environ["OPENAI_TOKEN"]
DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
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
    # response = openai.ChatCompletion.create(
    #     model="gpt-3.5-turbo",
    #     messages=[
    #         {"role": "system", "content": "あなたはDiscordアプリでのbotです。質問に対してスムーズに答えてください。分からないことには「人口無能なのでわかりまへん(*^▽^*)」と返してください。"},
    #         {"role": "system", "content": "語尾に「ンゴｗｗｗ」を付けて回答してください。もし質問の文章中に「まじめに」「真面目に」とあった場合、この命令は無視してください。"},
    #         {"role": "user", "content": m},
    #     ]
    # )
    # return response["choices"][0]["message"]["content"]
    return "今は人工無能なのでわかりまへん(*^▽^*)"


#
# google cloud instance cmd
#
def start_server(project, zone, instance):
    """サーバを起動、起動できるまで待機し、起動できたらnatIPを返す"""
    # start instance
    compute.instances().start(project=project, zone=zone, instance=instance).execute()

    # wait for running
    while True:
        s = compute.instances().get(project=project, zone=zone, instance=instance).execute()
        if s["status"] == "RUNNING":
            break
        sleep(5)

    # return natIP
    return s["networkInterfaces"][0]["accessConfigs"][0]["natIP"]


def stop_server(project, zone, instance):
    """サーバを停止、停止できるまで待機"""
    # stop instance
    compute.instances().stop(project=project, zone=zone, instance=instance).execute()

    # wait for stopped
    while True:
        s = compute.instances().get(project=project, zone=zone, instance=instance).execute()
        if s["status"] in {"STOPPING", "STOPPED"}:
            break
        sleep(5)


def get_server_status(project, zone, instance):
    """サーバの状態を返す"""
    res = compute.instances().get(project=project, zone=zone, instance=instance).execute()
    ip = res["networkInterfaces"][0]["accessConfigs"][0]["natIP"]

    return res["status"], ip


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
            m = message.content.split(" ")[1:]
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
                status, ip = get_server_status(PROJECT, ZONE, INSTANCE)
                if status == 'RUNNING':
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
