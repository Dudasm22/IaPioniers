# app.py
import os
import pandas as pd
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
# asyncio não é mais estritamente necessário para este propósito, mas não causa problema.
# import asyncio 

# Apenas importe as funções de lógica de negócios que operam nos DataFrames já processados
from evasion_prediction_logic import get_overall_evasion_report, get_evasion_risk_students_for_professor
from student_profile_generator import get_student_profile_details

app = Flask(__name__)
CORS(app)

# --- Configurações de Cache ---
LOCAL_DATA_DIR = os.path.join(os.path.dirname(__file__), 'local_data')
RAW_LOGS_CACHE_FILE = os.path.join(LOCAL_DATA_DIR, 'raw_logs_cache.pkl')
PROCESSED_FEATURES_CACHE_FILE = os.path.join(LOCAL_DATA_DIR, 'processed_features_cache.pkl')

# Variáveis globais para armazenar os DataFrames em memória
# Isso evita que o Flask recarregue os dados do disco a cada requisição
cached_raw_logs_df = None
cached_processed_features_df = None
# Não precisamos mais de last_cache_update_time para esta estratégia,
# pois a "frescura" é garantida pelo script diário que sobrescreve os arquivos.
# As requisições ao Flask sempre carregarão o mais recente do disco.


# A função _is_cache_valid() não é mais necessária para a "frescura" diária,
# mas podemos adaptá-la para verificar se os arquivos existem e não estão vazios.
def _are_cache_files_present_and_valid():
    """Verifica se os arquivos de cache no disco existem e não estão vazios."""
    if not os.path.exists(RAW_LOGS_CACHE_FILE) or os.path.getsize(RAW_LOGS_CACHE_FILE) == 0:
        print(f"[{datetime.now()}] Cache de logs brutos ausente ou vazio.")
        return False
    if not os.path.exists(PROCESSED_FEATURES_CACHE_FILE) or os.path.getsize(PROCESSED_FEATURES_CACHE_FILE) == 0:
        print(f"[{datetime.now()}] Cache de features processadas ausente ou vazio.")
        return False
    print(f"[{datetime.now()}] Arquivos de cache presentes e válidos no disco.")
    return True


# Esta função agora apenas carrega os dados do disco OU do cache em memória.
# Não faz chamadas à API nem processamento de features.
async def _load_data_from_cache_or_disk(force_reload_from_disk: bool = False):
    global cached_raw_logs_df, cached_processed_features_df

    # Se não for forçado a recarregar e os dados já estiverem em memória, use a memória.
    if not force_reload_from_disk and cached_raw_logs_df is not None and cached_processed_features_df is not None:
        print(f"[{datetime.now()}] Dados em memória disponíveis. Usando cache em memória.")
        return cached_raw_logs_df, cached_processed_features_df

    # Tenta carregar do disco
    print(f"[{datetime.now()}] Recarregando dados do disco (forçado ou não em memória)...")
    if _are_cache_files_present_and_valid():
        try:
            df_raw = pd.read_pickle(RAW_LOGS_CACHE_FILE)
            df_processed = pd.read_pickle(PROCESSED_FEATURES_CACHE_FILE)
            print(f"[{datetime.now()}] Dados brutos ({len(df_raw)} linhas) e processados ({len(df_processed)} linhas) carregados do cache de disco.")
            
            # Atualiza o cache em memória
            cached_raw_logs_df = df_raw
            cached_processed_features_df = df_processed
            return cached_raw_logs_df, cached_processed_features_df

        except Exception as e:
            print(f"[{datetime.now()}] Erro ao carregar caches do disco: {e}. Certifique-se de que 'update_cache.py' foi executado.")
            return pd.DataFrame(), pd.DataFrame() # Retorna DataFrames vazios em caso de erro

    else:
        print(f"[{datetime.now()}] Arquivos de cache ausentes ou inválidos. Por favor, execute 'update_cache.py' para gerar os dados.")
        return pd.DataFrame(), pd.DataFrame() # Retorna DataFrames vazios se os arquivos não existirem/estiverem vazios


def _get_raw_logs_for_profile_generator():
    """Função auxiliar para o gerador de perfil de estudante carregar os logs brutos."""
    global cached_raw_logs_df
    # Prefere o cache em memória
    if cached_raw_logs_df is not None and not cached_raw_logs_df.empty:
        return cached_raw_logs_df
    
    # Se não estiver em memória, tenta carregar diretamente do disco
    if os.path.exists(RAW_LOGS_CACHE_FILE) and os.path.getsize(RAW_LOGS_CACHE_FILE) > 0:
        try:
            df_raw = pd.read_pickle(RAW_LOGS_CACHE_FILE)
            cached_raw_logs_df = df_raw # Atualiza o cache em memória para futuras chamadas
            return df_raw
        except Exception as e:
            print(f"[{datetime.now()}] Erro ao carregar logs brutos para gerador de perfil: {e}")
            return pd.DataFrame()
    return pd.DataFrame()


# --- Endpoints da API ---
# Os endpoints continuarão sendo async def, e usarão a nova função _load_data_from_cache_or_disk

@app.route('/api/evasion-report', methods=['GET'])
async def get_evasion_report():
    print(f"[{datetime.now()}] Requisição recebida para /api/evasion-report")
    # force_refresh agora significa recarregar do disco para a memória
    force_reload = request.args.get('force_refresh', 'false').lower() == 'true'
    
    _, df_processed = await _load_data_from_cache_or_disk(force_reload)

    if df_processed.empty:
        return jsonify({"message": "Nenhum dado processado disponível. Por favor, gere os dados com 'update_cache.py'."}), 500

    report = get_overall_evasion_report(df_processed)
    return jsonify(report)

@app.route('/api/professor-evasion-risk', methods=['GET'])
async def get_professor_evasion_risk():
    professor_name = request.args.get('professor_name')
    print(f"[{datetime.now()}] Requisição recebida para /api/professor-evasion-risk para professor: {professor_name}")

    if not professor_name:
        return jsonify({"error": "Parâmetro 'professor_name' é obrigatório."}), 400

    # Não há necessidade de force_reload aqui, a menos que você queira.
    _, df_processed = await _load_data_from_cache_or_disk()

    if df_processed.empty:
        return jsonify({"message": "Nenhum dado processado disponível. Por favor, gere os dados com 'update_cache.py'."}), 500

    risk_students = get_evasion_risk_students_for_professor(df_processed, professor_name)
    return jsonify(risk_students)


@app.route('/api/student-profile/<user_id>', methods=['GET'])
async def get_student_profile(user_id):
    print(f"[{datetime.now()}] Requisição recebida para /api/student-profile/{user_id}")
    
    # Não há necessidade de force_reload aqui, a menos que você queira.
    _, df_processed = await _load_data_from_cache_or_disk()

    if df_processed.empty:
        return jsonify({"message": "Nenhum dado processado disponível para gerar o perfil. Por favor, gere os dados com 'update_cache.py'."}), 500
    
    # _get_raw_logs_for_profile_generator() agora prefere o cache em memória ou carrega do disco
    profile = get_student_profile_details(user_id, df_processed, _get_raw_logs_for_profile_generator)

    if profile:
        return jsonify(profile)
    else:
        return jsonify({"message": f"Aluno com ID {user_id} não encontrado ou dados insuficientes."}), 404

@app.route('/api/raw-logs', methods=['GET'])
async def get_raw_moodle_logs():
    print(f"[{datetime.now()}] Requisição recebida para /api/raw-logs")
    # force_refresh agora significa recarregar do disco para a memória
    force_reload = request.args.get('force_refresh', 'false').lower() == 'true'

    df_raw, _ = await _load_data_from_cache_or_disk(force_reload)

    if df_raw.empty:
        return jsonify({"message": "Nenhum dado bruto disponível. Por favor, gere os dados com 'update_cache.py'."}), 500
    
    df_raw_json = df_raw.copy()
    # A correção de datetime para string permanece aqui
    for col in df_raw_json.select_dtypes(include=['datetime64[ns]']).columns:
        df_raw_json[col] = df_raw_json[col].apply(lambda x: x.isoformat() if pd.notna(x) else None)

    return jsonify(df_raw_json.to_dict(orient='records'))


if __name__ == '__main__':
    print(f"[{datetime.now()}] Iniciando a API Flask...")
    os.makedirs(LOCAL_DATA_DIR, exist_ok=True) # Garante que o diretório exista ao iniciar
    
    # Opcional: Carregar o cache na inicialização do Flask para que a primeira requisição seja rápida.
    # No entanto, se os arquivos ainda não existirem (primeira execução), isso retornará DataFrames vazios.
    # Se você quiser que o Flask 'espere' pelos dados, remova esta linha e deixe as rotas carregarem sob demanda.
    # Pessoalmente, eu prefiro que o Flask inicie rápido e os dados sejam carregados na primeira requisição
    # ou que o script de atualização seja executado primeiro para garantir que os arquivos existam.
    # cached_raw_logs_df, cached_processed_features_df = asyncio.run(_load_data_from_cache_or_disk())

    app.run(host='0.0.0.0', port=5000, debug=True)