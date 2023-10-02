import argparse
import discord

from time import sleep
from googleapiclient import discovery

from const import HELP, TOPIC_HELLO, PROJECT, ZONE, INSTANCE


parser = argparse.ArgumentParser()
parser.add_argument('discord_token', help="DiscordBotのトークン")
parser.add_argument('--openai_token', help="OpenAIのトークン")
args = parser.parse_args()


#
# set
#
DISCORD_TOKEN = args.discord_token
USE_CHATGPT = False
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
class MicraButton(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.responses = get_server_status(PROJECT, ZONE, INSTANCE)
        self.status = self.responses["status"]

    @discord.ui.button(label="Status", style=discord.ButtonStyle.primary)
    async def status(self, interaction, button):
        if self.status in ['PROVISIONING', 'STAGING']:
            await interaction.response.send_message("サーバーを起動している最中です。")
        elif self.status == 'RUNNING':
            ip = self.responses["networkInterfaces"][0]["accessConfigs"][0]["natIP"]
            await interaction.response.send_message(f"サーバーは起動中です！アドレスは{ip}です。")
        elif self.status == 'STOPPING':
            await interaction.response.send_message("サーバーを停止している最中です。")
        elif self.status == 'TERMINATED':
            await interaction.response.send_message("サーバーは停止中です。")
        else:
            await interaction.response.send_message(f"サーバーの状態を確認できません！時間おいてもう一度お試しください。(ステータス：{self.status})")

    @discord.ui.button(label="Start", style=discord.ButtonStyle.green)
    async def start(self, interaction, button):
        if self.status in ['PROVISIONING', 'STAGING']:
            await interaction.response.send_message(f"サーバーは既に起動しています、起動するまで少々お待ちください。")
        elif self.status == 'RUNNING':
            ip = self.responses["networkInterfaces"][0]["accessConfigs"][0]["natIP"]
            await interaction.response.send_message(f"サーバーは既に起動しています！アドレスは{ip}です。")
        elif self.status == 'STOPPING':
            await interaction.response.send_message(f"サーバーを停止しています、停止完了後にもう一度お試しください。")
        elif self.status == 'TERMINATED':
            await interaction.response.send_message("サーバーを起動します、少々お待ちください...")
            ip = start_server(PROJECT, ZONE, INSTANCE)
            await interaction.response.send_message(f"サーバーが起動しました！アドレスは{ip}です。")
        else:
            await interaction.response.send_message(f"サーバーの状態を確認できません！時間おいてもう一度お試しください。(ステータス：{self.status})")

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.red)
    async def stop(self, interaction, button):
        if self.status in ['PROVISIONING', 'STAGING']:
            await interaction.response.send_message(f"サーバーは起動中です、起動完了後にもう一度お試しください。")
        elif self.status == 'RUNNING':
            await interaction.response.send_message("サーバー停止中、少々お待ちください...")
            stop_server(PROJECT, ZONE, INSTANCE)
            await interaction.response.send_message("サーバーが停止しました！")
        elif self.status == 'STOPPING':
            await interaction.response.send_message(f"サーバーを停止しています、少々お待ちください。")
        elif self.status == 'TERMINATED':
            await interaction.response.send_message("サーバーは既に停止しています！")
        else:
            await interaction.response.send_message(f"サーバーの状態を確認できません！時間おいてもう一度お試しください。(ステータス：{self.status})")


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
    if not message.author.bot:
        # greeting
        if message.content in TOPIC_HELLO:
            await message.channel.send(f"こんにちは{message.author}さん！")
        
        # chatgpt
        elif client.user in message.mentions:
            m = message.content.split(" ")[1:]
            async with message.channel.typing():
                await message.channel.send(res_chatgpt(m))

        # command: minecraft
        elif message.content.startswith('/micra'):
            message_list = message.content.split(' ')
            if len(message_list) == 1:
                """マイクラサーバー操作をボタンで表示"""
                await message.channel.send("マイクラサーバー操作メニューだよ", view=MicraButton())
            elif len(message_list) == 2:
                """マイクラサーバー操作をコマンドで受け付ける"""
                sub_command = message_list[1]
                res = get_server_status(PROJECT, ZONE, INSTANCE)
                status = res["status"]
                if sub_command == 'start':
                    if status in ['PROVISIONING', 'STAGING']:
                        await message.channel.send(f"サーバーは既に起動しています、起動するまで少々お待ちください。")
                    elif status == 'RUNNING':
                        ip = res["networkInterfaces"][0]["accessConfigs"][0]["natIP"]
                        await message.channel.send(f"サーバーは既に起動しています！アドレスは{ip}です。")
                    elif status == 'STOPPING':
                        await message.channel.send(f"サーバーを停止しています、停止完了後にもう一度お試しください。")
                    elif status == 'TERMINATED':
                        await message.channel.send("サーバーを起動します、少々お待ちください...")
                        ip = start_server(PROJECT, ZONE, INSTANCE)
                        await message.channel.send(f"サーバーが起動しました！アドレスは{ip}です。")
                    else:
                        await message.channel.send(f"サーバーの状態を確認できません！時間おいてもう一度お試しください。(ステータス：{status})")
                elif sub_command == 'stop':
                    if status in ['PROVISIONING', 'STAGING']:
                        await message.channel.send(f"サーバーは起動中です、起動完了後にもう一度お試しください。")
                    elif status == 'RUNNING':
                        await message.channel.send("サーバー停止中、少々お待ちください...")
                        stop_server(PROJECT, ZONE, INSTANCE)
                        await message.channel.send("サーバーが停止しました！")
                    elif status == 'STOPPING':
                        await message.channel.send(f"サーバーを停止しています、少々お待ちください。")
                    elif status == 'TERMINATED':
                        await message.channel.send("サーバーは既に停止しています！")
                    else:
                        await message.channel.send(f"サーバーの状態を確認できません！時間おいてもう一度お試しください。(ステータス：{status})")
                elif sub_command == 'status':
                    if status in ['PROVISIONING', 'STAGING']:
                        await message.channel.send("サーバーを起動している最中です。")
                    elif status == 'RUNNING':
                        ip = status["networkInterfaces"][0]["accessConfigs"][0]["natIP"]
                        await message.channel.send(f"サーバーは起動中です！アドレスは{ip}です。")
                    elif status == 'STOPPING':
                        await message.channel.send("サーバーを停止している最中です。")
                    elif status == 'TERMINATED':
                        await message.channel.send("サーバーは停止中です。")
                    else:
                        await message.channel.send(f"サーバーの状態を確認できません！時間おいてもう一度お試しください。(ステータス：{status})")
            else:
                await message.channel.send("コマンド引数が多いよ、使い方は`/help`見てね。")

        # help
        elif message.content.startswith('/help'):
            await message.channel.send(HELP)

        # other
        else:
            pass


if __name__ == "__main__":
    client.run(DISCORD_TOKEN)
