# moodle_api_connector.py
import asyncio
import aiohttp
import json
import pandas as pd
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# --- Configurações da API Moodle ---
MOODLE_API_BASE_URL = "https://api.unifenas.br/v1"
UNIFENAS_EMAIL = "hackathon@unifenas.br"
UNIFENAS_PASSWORD = "hackathon#2025"

# --- Configuração de Delay e Concorrência ---
REQUEST_DELAY_SECONDS = 0.5 # Ajustando para 0.5s para maior chance de sucesso inicial
MAX_CONCURRENT_REQUESTS = 5 # Mantenha em 5 por enquanto.

# --- Configurações de Retry ---
RETRY_SETTINGS = {
    'stop': stop_after_attempt(5),
    'wait': wait_exponential(multiplier=1, min=2, max=60),
    'retry': retry_if_exception_type(aiohttp.ClientError),
    'reraise': True
}

# --- Funções Assíncronas para a API Moodle ---

@retry(**RETRY_SETTINGS)
async def get_access_token_async(email, password, api_base_url):
    """Obtém um token de acesso da API do Moodle de forma assíncrona."""
    url = f"{api_base_url}/get-token"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    data = {"email": email, "password": password}
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            response.raise_for_status()
            token_data = await response.json()
            return token_data.get("access_token")

@retry(**RETRY_SETTINGS)
async def get_moodle_users_async(token, api_base_url):
    """Lista os usuários do Moodle que acessaram recentemente de forma assíncrona."""
    url = f"{api_base_url}/moodle/usuarios"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            response.raise_for_status()
            return await response.json()

async def get_user_logs_async(session, user_id, token, api_base_url, semaphore):
    """
    Coleta os logs de acesso de um usuário específico de forma assíncrona com controle de concorrência.
    A sessão aiohttp é passada externamente.
    """
    async with semaphore:
        await asyncio.sleep(REQUEST_DELAY_SECONDS)

        url = f"{api_base_url}/moodle/logs-usuario"
        
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
        }
        
        payload = {"user_id": user_id}

        try:
            @retry(**RETRY_SETTINGS)
            async def _fetch_single_log_with_retry():
                async with session.get(url, headers=headers, params=payload) as response:
                    response.raise_for_status()
                    return await response.json()
            
            return await _fetch_single_log_with_retry()

        except aiohttp.ClientError as e:
            print(f"[{datetime.now()}] Erro assíncrono final (após retries) ao obter logs para o usuário {user_id}: {e}")
            return []

# --- Função Principal de Coleta (agora assíncrona) ---

async def collect_all_moodle_logs_async(email, password, api_base_url):
    print(f"[{datetime.now()}] Iniciando collect_all_moodle_logs_async...")
    
    async with aiohttp.ClientSession() as session: # Criar sessão aqui, para ser usada por todas as sub-chamadas
        # Obter token
        token = await get_access_token_async(email, password, api_base_url) # Não precisa passar a sessão aqui
        if not token:
            print(f"[{datetime.now()}] Erro: Não foi possível obter o token de acesso. Abortando coleta de logs.")
            return pd.DataFrame()

        print(f"[{datetime.now()}] Token obtido. Coletando lista de usuários...")
        
        # Obter lista de usuários
        users_data = await get_moodle_users_async(token, api_base_url) # Não precisa passar a sessão aqui
        if not users_data:
            print(f"[{datetime.now()}] Erro: Não foi possível obter a lista de usuários. Abortando coleta de logs.")
            return pd.DataFrame()

        print(f"[{datetime.now()}] {len(users_data)} usuários encontrados. Coletando logs individuais...")
        
        all_logs = []
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

        tasks = []
        for user in users_data:
            user_id = user.get('user_id')
            user_name = user.get('name')
            
            if user_id:
                tasks.append(get_user_logs_async(session, user_id, token, api_base_url, semaphore)) # Passar a sessão aqui
            else:
                print(f"[{datetime.now()}] Aviso: user_id não encontrado para o usuário: {user.get('name', 'N/A')}")

        if tasks:
            print(f"[{datetime.now()}] Executando {len(tasks)} tarefas de coleta de logs concorrentemente...")
            results = await asyncio.gather(*tasks, return_exceptions=True)
            print(f"[{datetime.now()}] Todas as tarefas de coleta de logs concluídas.")
        else:
            results = []
            print(f"[{datetime.now()}] Nenhuma tarefa de coleta de logs para executar.")

        for i, res in enumerate(results):
            user = users_data[i]
            user_id = user.get('user_id')
            user_name = user.get('name')

            if isinstance(res, Exception):
                print(f"[{datetime.now()}] Erro no processamento do log para o usuário {user_id}: {res}")
            elif res:
                for log in res:
                    log['user_id'] = user_id
                    log['name'] = user_name
                    log['user_lastaccess'] = user.get('user_lastaccess')
                    all_logs.append(log)
    
    df_raw_logs = pd.DataFrame(all_logs)
    print(f"[{datetime.now()}] DataFrame de logs brutos criado. Total de linhas: {len(df_raw_logs)}")

    if not df_raw_logs.empty:
        df_raw_logs['date'] = pd.to_datetime(df_raw_logs['date'], errors='coerce')
        df_raw_logs['user_lastaccess'] = pd.to_datetime(df_raw_logs['user_lastaccess'], errors='coerce')
        df_raw_logs = df_raw_logs.dropna(subset=['date'])
        
        if 'course_fullname' not in df_raw_logs.columns:
            print(f"[{datetime.now()}] Aviso: Coluna 'course_fullname' não encontrada nos logs. Adicionando 'Curso Desconhecido'.")
            df_raw_logs['course_fullname'] = 'Curso Desconhecido'

        print(f"[{datetime.now()}] DataFrame processado. Total de linhas após dropna e ajuste de colunas: {len(df_raw_logs)}")
    else:
        print(f"[{datetime.now()}] DataFrame de logs brutos está vazio, pulando o processamento.")

    return df_raw_logs

# --- Funções de Envolvimento para compatibilidade (AGORA É ASSÍNCRONA) ---
# Esta função AGORA DEVE SER 'async def' para ser awaitada pelo Flask
async def collect_all_moodle_logs(email, password, api_base_url):
    return await collect_all_moodle_logs_async(email, password, api_base_url)


if __name__ == '__main__':
    print("Testando moodle_api_connector.py com assincronia em modo standalone...")
    # Para testar este arquivo isoladamente, você precisa usar asyncio.run()
    # Apenas este bloco 'if __name__ == "__main__":' deve conter asyncio.run()
    async def main_test_connector():
        df_test_logs = await collect_all_moodle_logs_async(UNIFENAS_EMAIL, UNIFENAS_PASSWORD, MOODLE_API_BASE_URL)
        print("Logs coletados (amostra):")
        print(df_test_logs.head())
        print(f"Total de logs: {len(df_test_logs)}")
    
    asyncio.run(main_test_connector())
    print("Teste principal de coleta assíncrona concluído.")