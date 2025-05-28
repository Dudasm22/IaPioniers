# update_cache.py
import asyncio
import os
import pandas as pd
from datetime import datetime

# Importe as funções dos seus módulos
from moodle_api_connector import collect_all_moodle_logs, MOODLE_API_BASE_URL, UNIFENAS_EMAIL, UNIFENAS_PASSWORD
from evasion_prediction_logic import run_feature_engineering, calculate_evasion_risk_scores

# --- Configurações de Cache ---
LOCAL_DATA_DIR = os.path.join(os.path.dirname(__file__), 'local_data')
RAW_LOGS_CACHE_FILE = os.path.join(LOCAL_DATA_DIR, 'raw_logs_cache.pkl')
PROCESSED_FEATURES_CACHE_FILE = os.path.join(LOCAL_DATA_DIR, 'processed_features_cache.pkl')

async def main_update_cache():
    """
    Função principal para coletar, processar e salvar os caches de dados.
    Esta função será agendada para rodar diariamente.
    """
    print(f"[{datetime.now()}] Iniciando a atualização diária do cache de dados...")

    os.makedirs(LOCAL_DATA_DIR, exist_ok=True) # Garante que o diretório exista antes de salvar

    # 1. Coleta os logs brutos da API Moodle
    print(f"[{datetime.now()}] Coletando logs brutos da API Moodle...")
    df_raw = await collect_all_moodle_logs(UNIFENAS_EMAIL, UNIFENAS_PASSWORD, MOODLE_API_BASE_URL)
    
    if not df_raw.empty:
        # Salva os logs brutos em cache
        df_raw.to_pickle(RAW_LOGS_CACHE_FILE)
        print(f"[{datetime.now()}] Logs brutos coletados e salvos em '{RAW_LOGS_CACHE_FILE}'. Total de linhas: {len(df_raw)}")
        
        # 2. Realiza a engenharia de features e cálculo de scores
        print(f"[{datetime.now()}] Processando features e calculando scores...")
        df_features = run_feature_engineering(df_raw)
        df_processed = calculate_evasion_risk_scores(df_features)

        if not df_processed.empty:
            # Salva as features processadas e scores em cache
            df_processed.to_pickle(PROCESSED_FEATURES_CACHE_FILE)
            print(f"[{datetime.now()}] Features processadas e scores calculados e salvos em '{PROCESSED_FEATURES_CACHE_FILE}'. Total de linhas: {len(df_processed)}")
        else:
            print(f"[{datetime.now()}] Aviso: Processamento de features resultou em DataFrame vazio. Cache de features não atualizado.")
    else:
        print(f"[{datetime.now()}] Erro: Coleta de logs brutos da API retornou DataFrame vazio. Nenhum cache foi atualizado.")

    print(f"[{datetime.now()}] Atualização diária do cache concluída.")

if __name__ == "__main__":
    # Executa a função principal assíncrona
    asyncio.run(main_update_cache())