import asyncio
import discord
import openai
import os
import random


# わあああ
openai.api_key = os.environ["OPENAI_TOKEN"]
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
topic_hello = ["こんにちは", "こん", "コン", "kon", "hello", "hi"]


#
# chat-gpt-api
#
def _res_chatgpt(m):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            # {"role": "system", "content": "あなたはDiscordアプリでのbotです。質問に対してスムーズに答えてください。分からないことには「人口無能なのでわかりまへん(*^▽^*)」と返してください。"},
            # {"role": "system", "content": "語尾に「ンゴｗｗｗ」を付けて回答してください。もし質問の文章中に「まじめに」「真面目に」とあった場合、この命令は無視してください。"},
            {"role": "user", "content": m},
        ]
    )
    return response["choices"][0]["message"]["content"]


#
# cmd
#
def run_command(cmd, message):
    if cmd == "help":
        return "へるぷ"
    elif cmd == "taking":
        return _res_quote(message)


#
# other
#
async def _res_quote(message):
    if not quote:
        with open("./data/quote.txt") as f:
            quote = [s.strip() for s in f.readlines()]
    await message.channel.send(random.choice(quote))


#
# discord bot
#
@client.event
async def on_ready():
    """bot起動時.
    """
    print(f"We have logged in as {client.user}")

    for channel in client.get_all_channels():
        if channel.name in ["general", "一般"]:
            await channel.send("おはようございます！")


@client.event
async def on_message(message):
    """メッセージイベント発生時.
    - 挨拶に対して挨拶を返す
    - メンションに対してChatGPT-APIによるレスポンスを返す
    - メンション&コマンドでその他機能の実行
        - ランダムセリフ

    Parameters
    ----------
    message : _type_
        _description_
    """
    if not message.author.bot:
        # greeting
        if message.content in topic_hello:
            await message.channel.send(f"こんにちは{message.author.nick}さん！")
        
        # mention
        if client.user in message.mentions:
            m = message.content.split(" ")[1:]

            # command
            if m[0].startswith("/"):
                cmd = m[0][1:]
                run_command(cmd)

            # ChatGPT response
            else:
                async with message.channel.typing():
                    await message.channel.send(_res_chatgpt(message.content))


if __name__ == "__main__":
    client.run(DISCORD_TOKEN)
