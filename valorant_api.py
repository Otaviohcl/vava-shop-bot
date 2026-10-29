import os
import base64
import json
import requests

def buscar_loja_valorant(access_token, entitlements_token, puuid, region="na"):
    # 1. Descobre a versão ATUAL do cliente do Valorant
    try:
        resp_versao = requests.get("https://valorant-api.com/v1/version", timeout=10)
        client_version = resp_versao.json()["data"]["riotClientVersion"]
    except Exception as e:
        print(f"❌ Não consegui descobrir a versão do cliente: {e}")
        return None

    # 2. Monta o texto que descreve a plataforma e converte para Base64
    plataforma = {
        "platformType": "PC",
        "platformOS": "Windows",
        "platformOSVersion": "10.0.19042.1.256.64bit",
        "platformChipset": "Unknown"
    }
    client_platform = base64.b64encode(json.dumps(plataforma).encode()).decode()

    # 3. Os headers agora estão completos
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Riot-Entitlements-JWT": entitlements_token,
        "X-Riot-ClientVersion": client_version,
        "X-Riot-ClientPlatform": client_platform
    }

    url = f"https://pd.{region}.a.pvp.net/store/v3/storefront/{puuid}"

    try:
        response = requests.post(url, headers=headers, json={}, timeout=10)
    except requests.exceptions.RequestException as e:
        print(f"❌ Falha de conexão: {e}")
        return None

    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Erro ao buscar loja: {response.status_code} - {response.text}")
        return None


def obter_credenciais_locais_riot():
    """
    Lê o arquivo 'lockfile' gerado pelo Riot Client no Windows 
    para descobrir a porta e a senha de autenticação local.
    """
    # Caminho padrão do lockfile no Windows
    lockfile_path = os.path.expandvars(r'%LOCALAPPDATA%\Riot Games\Riot Client\Config\lockfile')
    
    if not os.path.exists(lockfile_path):
        print("❌ Riot Client não encontrado ou fechado. Abra o jogo/Riot Client primeiro!")
        return None
        
    try:
        with open(lockfile_path, 'r') as f:
            conteudo = f.read().split(':')
            # O arquivo lockfile tem o formato: nome:pid:porta:senha:protocolo
            port = conteudo[2]
            token = conteudo[3]
            
            # Codifica o token local em Base64 para usar no cabeçalho HTTP
            auth_encoded = base64.b64encode(f"riot:{token}".encode()).decode()
            
            return {
                "port": port,
                "auth": auth_encoded
            }
    except Exception as e:
        print(f"❌ Erro ao ler o lockfile: {e}")
        return None

def obter_tokens_locais():
    """
    Usa a porta e a senha do lockfile para pedir ao Riot Client local
    os tokens de acesso, entitlements e o PUUID da conta logada.
    """
    credenciais = obter_credenciais_locais_riot()
    if not credenciais:
        return None
        
    port = credenciais["port"]
    auth = credenciais["auth"]
    
    # Cabeçalho exigido pelo Riot Client local
    headers = {
        "Authorization": f"Basic {auth}"
    }
    
    # Desativa o aviso de certificado SSL autoassinado local do Riot Client (verify=False)
    # O Riot Client roda um servidor HTTPS local com certificado próprio.
    url_tokens = f"https://127.0.0.1:{port}/entitlements/v1/token"
    
    try:
        response = requests.get(url_tokens, headers=headers, verify=False)
        if response.status_code == 200:
            dados = response.json()
            access_token = dados.get("accessToken")
            entitlements_token = dados.get("token")
            puuid = dados.get("subject") # O 'subject' é o PUUID da conta
            
            return {
                "access_token": access_token,
                "entitlements_token": entitlements_token,
                "puuid": puuid
            }
    except Exception as e:
        print(f"❌ Erro ao obter tokens locais: {e}")

def buscar_nome_skin(skin_uuid):
    url = f"https://valorant-api.com/v1/weapons/skinlevels/{skin_uuid}"
    
    try:
        resp = requests.get(url, timeout=10)
    except requests.exceptions.RequestException as e:
        print(f"❌ Falha ao buscar nome da skin: {e}")
        return None
    
    if resp.status_code == 200:
        return resp.json()["data"]["displayName"]
    
    return None

def buscar_skins_por_nome(termo):
    url = "https://valorant-api.com/v1/weapons/skins"

    try:
        resp = requests.get(url, timeout=15)
    except requests.exceptions.RequestException as e:
        print(f"❌ Falha ao buscar catálogo de skins: {e}")
        return None

    if resp.status_code != 200:
        return None

    termo = termo.lower()
    encontradas = []

    for skin in resp.json()["data"]:
        nome = skin["displayName"]
        if termo in nome.lower():
            uuid_nivel1 = skin["levels"][0]["uuid"]
            icone = skin.get("displayIcon") or skin["levels"][0].get("displayIcon")
            encontradas.append((uuid_nivel1, nome, icone))        
            
    return encontradas
        
    return None