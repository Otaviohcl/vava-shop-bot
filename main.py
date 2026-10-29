import os # biblioteca do py para interajir com SO
import discord # biblioteca principal do discord.py que faz a ponte com os servidores do dc
import asyncio
from discord.ext import commands # Módulo de comandos para facilitar a criação de comandos de chat (como !ping)
from dotenv import load_dotenv #funçao da biblioteca que le o arquivo .env e injeta as variaveis no sistema
from database import SessionLocal, User, Favorite, init_db
from valorant_api import obter_tokens_locais, buscar_loja_valorant, buscar_nome_skin, buscar_skins_por_nome

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

@bot.before_invoke
async def garantir_usuario(ctx):
    discord_id_str = str(ctx.author.id)
    session = SessionLocal()
    try:
        existe = session.query(User).filter_by(discord_id=discord_id_str).first()
        if not existe:
            session.add(User(discord_id=discord_id_str))
            session.commit()
    except Exception as e:
        session.rollback()
        print(f"Erro ao registrar usuário: {e}")
    finally:
        session.close()

#  o @ faz que quando o evento acontecer ele vai realizar x funçao
@bot.event
async def on_ready():
    init_db() # <-- faz o sql e tabela iniciam junto com o bot
    print(f"✅ Bot conectado com sucesso como: {bot.user.name} (ID: {bot.user.id})")
    print(f"-------------------------------------------------")


# o @bot.command registra que a funçao (ping) abaixo é um comando 
@bot.command()
async def hello(ctx):
    await ctx.send("Salve meu Chupetinha, O bot está 100% online e pronto para te servir")


@bot.command(name="loja")
async def loja(ctx):
    """Consulta a loja diaria do vava do usuario logado"""
    await ctx.send("Buscando sua loja no RiotClient... Aguarde!")

    tokens = obter_tokens_locais()
    if not tokens:
        await ctx.send("Não consegui encontrar o Riot Client aberto. Certifique-se de que o Client está rodando em segundo plano no PC!")
        return
    
    access_token = tokens["access_token"]
    entitlements_token = tokens["entitlements_token"]
    puuid = tokens["puuid"]

    #2. requisição para a API da Riot com os tokenszinhos
    dados_loja = buscar_loja_valorant(access_token, entitlements_token, puuid)

    if not dados_loja:
        await ctx.send(" Erro ao consultar a API da RIOT. Verifique o terminal para detalhes ")
        return

    try:
        # A API guarda as 4 ofertas diárias dentro de 'SkinsPanelLayout' -> 'SingleItemOffers'
        ofertas = dados_loja.get("SkinsPanelLayout", {}).get("SingleItemOffers", [])
        
        if not ofertas:
            await ctx.send("⚠️ Não encontrei ofertas ativas na sua loja.")
            return
            
        mensagem = "**Suas 4 skins da Loja Diária:**\n"

        for skin_uuid in ofertas:
            nome = await asyncio.to_thread(buscar_nome_skin, skin_uuid)
            mensagem += f"- {nome or skin_uuid}\n"

        await ctx.send(mensagem)
    
    except Exception as e:
        await ctx.send(f"❌ Ocorreu um erro ao processar os dados da loja: {e}")

@bot.command(name="favoritar")
async def favoritar(ctx, *, termo):
    discord_id_str = str(ctx.author.id)

    resultados = await asyncio.to_thread(buscar_skins_por_nome, termo)

    if resultados is None:
        await ctx.send("❌ Não consegui consultar o catálogo de skins agora.")
        return

    if len(resultados) == 0:
        await ctx.send(f"⚠️ Não achei nenhuma skin com '{termo}'.")
        return

    if len(resultados) > 1:
        lista = "\n".join(f"- {nome}" for _, nome, _ in resultados[:10])
        await ctx.send(f"Achei {len(resultados)} skins parecidas. Digite o nome mais completo:\n{lista}")
        return

    skin_uuid, skin_nome, skin_icone = resultados[0]

    session = SessionLocal()
    try:
        ja_existe = session.query(Favorite).filter_by(
            discord_id=discord_id_str, skin_uuid=skin_uuid
        ).first()

        if ja_existe:
            await ctx.send(f"⚠️ **{skin_nome}** já está nas suas favoritas.")
        else:
            session.add(Favorite(discord_id=discord_id_str, skin_uuid=skin_uuid, skin_nome=skin_nome))
            session.commit()

            embed = discord.Embed(
                title=f"⭐ {skin_nome}",
                description="Adicionada às suas favoritas!",
                color=discord.Color.gold()
            )
            if skin_icone:
                embed.set_image(url=skin_icone)
            await ctx.send(embed=embed)

    except Exception as e:
        session.rollback()
        await ctx.send("❌ Erro ao salvar a favorita.")
        print(f"Erro no banco: {e}")

    finally:
        session.close()


@bot.command(name="favoritas")
async def favoritas(ctx):
    discord_id_str = str(ctx.author.id)

    session = SessionLocal()
    try:
        favoritas_db = session.query(Favorite).filter_by(
            discord_id=discord_id_str
        ).order_by(Favorite.skin_nome).all()
        nomes = [fav.skin_nome for fav in favoritas_db]
    finally:
        session.close()

    if not nomes:
        await ctx.send("Você ainda não tem favoritas. Use `%favoritar <nome da skin>`.")
        return

    lista = "\n".join(f"- {nome}" for nome in nomes)
    await ctx.send(f"⭐ **Suas favoritas ({len(nomes)}):**\n{lista}")


@bot.command(name="remover")
async def remover(ctx, *, termo):
    discord_id_str = str(ctx.author.id)

    session = SessionLocal()
    try:
        achadas = session.query(Favorite).filter(
            Favorite.discord_id == discord_id_str,
            Favorite.skin_nome.ilike(f"%{termo}%")
        ).all()

        if len(achadas) == 0:
            await ctx.send(f"⚠️ Nenhuma das suas favoritas combina com '{termo}'.")
        elif len(achadas) > 1:
            lista = "\n".join(f"- {fav.skin_nome}" for fav in achadas)
            await ctx.send(f"Achei {len(achadas)} favoritas parecidas. Digite o nome mais completo:\n{lista}")
        else:
            nome = achadas[0].skin_nome
            session.delete(achadas[0])
            session.commit()
            await ctx.send(f"🗑️ **{nome}** foi removida das suas favoritas.")

    except Exception as e:
        session.rollback()
        await ctx.send("❌ Erro ao remover a favorita.")
        print(f"Erro no banco: {e}")

    finally:
        session.close()

#inica o bot ultilizando a key que ta no .env
bot.run(TOKEN)
