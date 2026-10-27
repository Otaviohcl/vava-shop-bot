import os # biblioteca do py para interajir com SO
import discord # biblioteca principal do discord.py que faz a ponte com os servidores do dc
from discord.ext import commands # Módulo de comandos para facilitar a criação de comandos de chat (como !ping)
from dotenv import load_dotenv #funçao da biblioteca que le o arquivo .env e injeta as variaveis no sistema

# procura um arquivo .env na pasta
load_dotenv()

# isso chama a chave que salvei no .env
TOKEN = os.getenv('DISCORD_TOKEN')

# isso são permissoes que o bot pede ao discord. Aki eu escolhi para escolher as padroes
intents = discord.Intents.default()

# permicao explicitamente ativa aki (mesmo no site do dc eu ja tendo marcado essa permiçao)
intents.message_content = True

# definiçao das permiçoes e prefixo usado para usuario chamar o bot
bot = commands.Bot(command_prefix="%", intents=intents)

#  o @ faz que quando o evento acontecer ele vai realizar x funçao
@bot.event
async def on_ready():
    print(f"✅ Bot conectado com sucesso como: {bot.user.name} (ID: {bot.user.id})")
    print(f"-------------------------------------------------")


# o @bot.command registra que a funçao (ping) abaixo é um comando 
@bot.command()
async def hello(ctx):
    await ctx.send("Salve meu Chupetinha, O bot está 100% online e pronto para te servir")

#inica o bot ultilizando a key que ta no .env
bot.run(TOKEN)
