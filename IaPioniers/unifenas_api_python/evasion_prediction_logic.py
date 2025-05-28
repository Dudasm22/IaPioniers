import pandas as pd
import json
import os
from datetime import datetime, timedelta

# --- Constantes para regras de evasão (ajustáveis) ---
POINTS_GLOBAL_INACTIVITY = 40
POINTS_COURSE_INACTIVITY = 30
POINTS_LOW_GLOBAL_ACTIONS = 20
POINTS_LOW_COURSE_ACTIONS = 10

THRESHOLD_GLOBAL_INACTIVITY_DAYS = 30
THRESHOLD_COURSE_INACTIVITY_DAYS = 15
THRESHOLD_LOW_GLOBAL_ACTIONS = 10
THRESHOLD_LOW_COURSE_ACTIONS = 3

MIN_SCORE_FOR_EVASION_RISK = 20
MAX_POSSIBLE_SCORE = (POINTS_GLOBAL_INACTIVITY +
                      POINTS_COURSE_INACTIVITY +
                      POINTS_LOW_GLOBAL_ACTIONS +
                      POINTS_LOW_COURSE_ACTIONS)

# --- Mapeamento de Ações do Moodle para nomes legíveis ---
ACTION_MAPPING = {
    'mod_assign_view_assign': 'Visualizou Tarefa',
    'mod_assign_submit_form': 'Submeteu Tarefa',
    'mod_quiz_attempt_started': 'Iniciou Questionário',
    'mod_quiz_attempt_submitted': 'Submeteu Questionário',
    'mod_forum_view_forum': 'Visualizou Fórum',
    'mod_forum_post_created': 'Criou Post no Fórum',
    'mod_url_viewed': 'Visualizou URL',
    'core_course_view_course': 'Visualizou Curso',
    'core_user_login': 'Login no Moodle',
    'core_user_logout': 'Logout no Moodle',
    'mod_resource_view_resource': 'Visualizou Recurso',
    'mod_folder_view_folder': 'Visualizou Pasta',
    'mod_page_view_page': 'Visualizou Página',
    'core_completion_view_course_module': 'Visualizou Módulo',
    'mod_glossary_view_glossary': 'Visualizou Glossário',
    'mod_lesson_view_lesson': 'Visualizou Lição',
    'mod_wiki_view_wiki': 'Visualizou Wiki',
    'mod_scorm_view_scorm': 'Visualizou SCORM',
    'mod_quiz_report_viewed': 'Visualizou Relatório do Questionário',
    'mod_feedback_view_feedback': 'Visualizou Feedback',
    'mod_choice_view_choice': 'Visualizou Enquete',
    'mod_data_view_database': 'Visualizou Banco de Dados',
    'mod_h5pactivity_viewed': 'Visualizou H5P',
    'mod_workshop_view_workshop': 'Visualizou Workshop',
    # Adicione mais mapeamentos conforme necessário
}

def map_action_name(action_code: str) -> str:
    """Mapeia códigos de ação Moodle para nomes mais legíveis."""
    return ACTION_MAPPING.get(action_code, action_code) # Retorna o código se não encontrar mapeamento

# --- Mapeamento Professor-Curso (lido de arquivo JSON ou mock) ---
LOCAL_MAPPING_DIR = os.path.join(os.path.dirname(__file__), 'data')
LOCAL_MAPPING_FILE = os.path.join(LOCAL_MAPPING_DIR, "professor_curso_mapping.json")

# Fallback se o arquivo JSON não for encontrado
FALLBACK_PROFESSOR_COURSE_MAP = {
    "João Silva": [
        "Sistemas de Informação - Programação Web Avançada",
        "Engenharia de Software - Padrões de Projeto",
        "Análise de Dados - Introdução à Inteligência Artificial"
    ],
    "Maria Oliveira": [
        "Ciência da Computação - Algoritmos e Estruturas de Dados II",
        "Sistemas de Informação - Banco de Dados Modernos"
    ]
}

def get_professor_course_mapping_data():
    """
    Carrega o mapeamento professor-curso de um arquivo JSON.
    Usa um mock hardcoded como fallback.
    """
    if os.path.exists(LOCAL_MAPPING_FILE):
        try:
            with open(LOCAL_MAPPING_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"Mapeamento professor-curso carregado de: {LOCAL_MAPPING_FILE}")
            return data
        except (json.JSONDecodeError, FileNotFoundError, Exception) as e:
            print(f"Erro ao carregar mapeamento do arquivo {LOCAL_MAPPING_FILE}: {e}. Usando fallback mock.")
            return FALLBACK_PROFESSOR_COURSE_MAP
    else:
        print(f"Arquivo de mapeamento {LOCAL_MAPPING_FILE} não encontrado. Usando fallback mock.")
        return FALLBACK_PROFESSOR_COURSE_MAP


def run_feature_engineering(df_raw_logs: pd.DataFrame, reference_date: datetime = None) -> pd.DataFrame:
    """
    Realiza a engenharia de características nos logs brutos.
    Calcula features globais e por curso.
    """
    if df_raw_logs.empty:
        return pd.DataFrame()

    if reference_date is None:
        reference_date = df_raw_logs['date'].max() if not df_raw_logs.empty else datetime.now()
    
    # 1. Features a nível de usuário (global)
    df_features_user_global = df_raw_logs.groupby('user_id').agg(
        user_name=('name', 'first'),
        last_access_date_global=('date', 'max'),
        total_actions_global=('action', 'count'),
        unique_courses_accessed_global=('course_fullname', lambda x: x.nunique()),
        # Contagem de tipos de ações específicas a nível global
        forum_interactions_global=('action', lambda x: x.apply(lambda y: 1 if 'forum' in y else 0).sum()),
        quiz_interactions_global=('action', lambda x: x.apply(lambda y: 1 if 'quiz' in y else 0).sum()),
        # Para um "score de presença", podemos usar a contagem de dias ativos no Moodle
        # (número de dias distintos em que o usuário teve alguma ação)
        active_days_global=('date', lambda x: x.dt.date.nunique())
    ).reset_index()
    df_features_user_global['days_since_last_access_global'] = (reference_date - df_features_user_global['last_access_date_global']).dt.days

    # Calcular a média de ações/dia para o score de presença
    if not df_features_user_global.empty:
        # Evitar divisão por zero se active_days_global for 0
        df_features_user_global['avg_actions_per_active_day_global'] = df_features_user_global.apply(
            lambda row: row['total_actions_global'] / row['active_days_global'] if row['active_days_global'] > 0 else 0,
            axis=1
        )
        # Normalizar para um score de 0 a 100 (ou outra escala)
        max_avg_actions = df_features_user_global['avg_actions_per_active_day_global'].max()
        if max_avg_actions > 0:
            df_features_user_global['presence_score_global'] = (df_features_user_global['avg_actions_per_active_day_global'] / max_avg_actions * 100).round(2)
        else:
            df_features_user_global['presence_score_global'] = 0.0


    # 2. Features a nível de usuário E curso
    df_features_user_course = df_raw_logs.groupby(['user_id', 'course_fullname']).agg(
        user_name=('name', 'first'),
        course_last_access_date=('date', 'max'),
        course_total_actions=('action', 'count'),
        viewed_count_course=('action', lambda x: (x == 'viewed').sum()), # Placeholder, precisa do mapped_action para ser preciso
        graded_count_course=('action', lambda x: (x == 'graded').sum()), # Placeholder, precisa do mapped_action para ser preciso
    ).reset_index()
    df_features_user_course['days_since_course_last_access'] = (reference_date - df_features_user_course['course_last_access_date']).dt.days

    # Melhorar a contagem de ações visualizadas/avaliadas no nível do curso
    # Primeiro, mapeie as ações para o DataFrame de logs brutos
    df_raw_logs_mapped = df_raw_logs.copy()
    df_raw_logs_mapped['mapped_action'] = df_raw_logs_mapped['action'].apply(map_action_name)

    # Re-calcular viewed_count_course e graded_count_course com mapped_action
    df_actions_by_course = df_raw_logs_mapped.groupby(['user_id', 'course_fullname']).agg(
        viewed_count_course=('mapped_action', lambda x: (x == 'Visualizou Recurso').sum() + (x == 'Visualizou Página').sum() + (x == 'Visualizou Módulo').sum() + (x == 'Visualizou URL').sum() + (x == 'Visualizou Glossário').sum() + (x == 'Visualizou Lição').sum() + (x == 'Visualizou Wiki').sum() + (x == 'Visualizou SCORM').sum() + (x == 'Visualizou Feedback').sum() + (x == 'Visualizou Enquete').sum() + (x == 'Visualizou Banco de Dados').sum() + (x == 'Visualizou H5P').sum() + (x == 'Visualizou Workshop').sum()),
        graded_count_course=('mapped_action', lambda x: (x == 'Submeteu Tarefa').sum() + (x == 'Submeteu Questionário').sum())
    ).reset_index()
    
    # Atualizar df_features_user_course com as contagens corretas
    df_features_user_course = df_features_user_course.drop(columns=['viewed_count_course', 'graded_count_course'], errors='ignore')
    df_features_user_course = pd.merge(df_features_user_course, df_actions_by_course, on=['user_id', 'course_fullname'], how='left')


    # 3. Mapeamento de ações recentes (para o perfil detalhado do aluno)
    df_recent_actions = df_raw_logs.copy()
    df_recent_actions['mapped_action'] = df_recent_actions['action'].apply(map_action_name)

    # Contagem de ações por tipo nos últimos X dias (ex: 7 dias)
    recent_period_start = reference_date - timedelta(days=7)
    df_recent_actions_filtered = df_recent_actions[df_recent_actions['date'] >= recent_period_start]
    
    recent_actions_summary = df_recent_actions_filtered.groupby(['user_id', 'mapped_action']).size().unstack(fill_value=0)
    recent_actions_summary = recent_actions_summary.add_prefix('recent_action_')
    recent_actions_summary = recent_actions_summary.reset_index()

    # 4. Unir todos os DataFrames
    df_final_features = pd.merge(
        df_features_user_course,
        df_features_user_global,
        on='user_id',
        how='left'
    )
    
    # Unir as ações recentes
    df_final_features = pd.merge(
        df_final_features,
        recent_actions_summary,
        on='user_id',
        how='left'
    )
    
    # Preencher NaNs para as colunas de ações recentes, se algum aluno não teve ações recentes
    for col in recent_actions_summary.columns:
        if col.startswith('recent_action_') and col in df_final_features.columns:
            df_final_features[col] = df_final_features[col].fillna(0)

    return df_final_features


def calculate_evasion_risk_scores(df_final_features: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula a pontuação de risco de evasão e define o status de risco para TODOS os alunos.
    Agora também registra as razões para o risco.
    """
    if df_final_features.empty:
        return pd.DataFrame()

    df_final_features['evasion_score'] = 0
    df_final_features['evasion_reasons'] = [[] for _ in range(len(df_final_features))] # Inicializa como lista vazia

    # Usaremos .apply para adicionar as razões de forma flexível a cada linha (aluno-curso)
    def apply_rules_and_reasons(row):
        score = 0
        reasons = []

        # Regra 1: Inatividade Global
        if row['days_since_last_access_global'] > THRESHOLD_GLOBAL_INACTIVITY_DAYS:
            score += POINTS_GLOBAL_INACTIVITY
            reasons.append(f"Inatividade global (> {THRESHOLD_GLOBAL_INACTIVITY_DAYS} dias)")

        # Regra 2: Inatividade por Curso
        if row['days_since_course_last_access'] > THRESHOLD_COURSE_INACTIVITY_DAYS:
            score += POINTS_COURSE_INACTIVITY
            reasons.append(f"Inatividade no curso '{row['course_fullname']}' (> {THRESHOLD_COURSE_INACTIVITY_DAYS} dias)")

        # Regra 3: Baixas Ações Globais
        if row['total_actions_global'] < THRESHOLD_LOW_GLOBAL_ACTIONS:
            score += POINTS_LOW_GLOBAL_ACTIONS
            reasons.append(f"Baixas interações globais (< {THRESHOLD_LOW_GLOBAL_ACTIONS} ações no total)")

        # Regra 4: Baixas Ações por Curso
        if row['course_total_actions'] < THRESHOLD_LOW_COURSE_ACTIONS:
            score += POINTS_LOW_COURSE_ACTIONS
            reasons.append(f"Baixas interações no curso '{row['course_fullname']}' (< {THRESHOLD_LOW_COURSE_ACTIONS} ações)")

        return pd.Series([score, reasons], index=['evasion_score_calculated', 'evasion_reasons_list'])

    # Aplica a função a cada linha do DataFrame
    results = df_final_features.apply(apply_rules_and_reasons, axis=1)
    df_final_features['evasion_score'] = results['evasion_score_calculated']
    df_final_features['evasion_reasons'] = results['evasion_reasons_list']


    # Marcar risco de evasão
    df_final_features['is_at_risk'] = df_final_features['evasion_score'] >= MIN_SCORE_FOR_EVASION_RISK

    # Garantir que evasion_score e is_at_risk são únicos para cada user_id para o relatório geral
    df_overall_scores = df_final_features.groupby('user_id').agg(
        overall_evasion_score=('evasion_score', 'max'), # Maior score entre os cursos para o score global
        is_at_risk=('is_at_risk', 'any') # Se estiver em risco em qualquer curso, está em risco globalmente
    ).reset_index()

    # Mesclar o score global de volta ao DataFrame original
    df_final_features = pd.merge(
        df_final_features,
        df_overall_scores[['user_id', 'overall_evasion_score', 'is_at_risk']],
        on='user_id',
        how='left',
        suffixes=('', '_overall') # Adiciona sufixo para evitar conflito se já existisse uma 'is_at_risk' ou 'evasion_score'
    )
    
    # Coletar as razões globais: se está em risco global, quais razões gerais o levaram a isso?
    # Isso é um pouco mais complexo, pois um aluno pode estar em risco global por razões em diferentes cursos.
    # A maneira mais simples para o "overall_evasion_reasons" seria coletar todas as razões de todos os cursos
    # onde o aluno está em risco.
    def get_overall_reasons(group):
        all_reasons = []
        if group['is_at_risk_overall'].any(): # Se o aluno está em risco globalmente
            # Coleta as razões de todos os cursos que o levaram a estar em risco
            for reasons_list in group.loc[group['is_at_risk'], 'evasion_reasons']:
                 all_reasons.extend(reasons_list)
            # Adiciona também as razões globais, se a pontuação global foi afetada por elas
            # (que já estão nas reasons_list dos cursos, mas garantimos que as globais não estão faltando)
            if group['days_since_last_access_global'].iloc[0] > THRESHOLD_GLOBAL_INACTIVITY_DAYS:
                 all_reasons.append(f"Inatividade global (> {THRESHOLD_GLOBAL_INACTIVITY_DAYS} dias)")
            if group['total_actions_global'].iloc[0] < THRESHOLD_LOW_GLOBAL_ACTIONS:
                 all_reasons.append(f"Baixas interações globais (< {THRESHOLD_LOW_GLOBAL_ACTIONS} ações no total)")
        
        return list(set(all_reasons)) # Retorna razões únicas

    overall_reasons_df = df_final_features.groupby('user_id').apply(get_overall_reasons).reset_index(name='overall_evasion_reasons')

    # Mesclar as razões globais de volta ao DataFrame
    df_final_features = pd.merge(
        df_final_features,
        overall_reasons_df,
        on='user_id',
        how='left'
    )

    # Garantir que a coluna final de risco global seja `is_at_risk`
    df_final_features['is_at_risk'] = df_final_features['is_at_risk_overall']
    df_final_features['overall_evasion_score'] = df_final_features['overall_evasion_score']
    
    # Remover colunas duplicadas que foram adicionadas no merge
    df_final_features = df_final_features.drop(columns=['is_at_risk_overall', 'evasion_score_calculated', 'evasion_reasons_list'], errors='ignore')

    return df_final_features


def get_overall_evasion_report(df_processed_features: pd.DataFrame) -> dict:
    """
    Gera um relatório geral de risco de evasão por aluno em formato de dicionário.
    Agora recebe o DataFrame COMPLETO de features processadas.
    """
    if df_processed_features.empty:
        return {
            "total_alunos_analisados": 0,
            "alunos_em_risco": 0,
            "evasao_estimada_percentual": 0.0,
            "evasao_por_curso": {},
            "alunos_detalhes": []
        }

    # Filtrar apenas os alunos únicos para o relatório geral (baseado no user_id)
    # E garantir que pegamos os valores globais de risco e score.
    df_unique_students = df_processed_features.drop_duplicates(subset=['user_id'])
    
    total_alunos_analisados = df_unique_students['user_id'].nunique()
    alunos_em_risco = df_unique_students[df_unique_students['is_at_risk']]['user_id'].nunique()
    
    evasao_estimada_percentual = (alunos_em_risco / total_alunos_analisados * 100).round(2) if total_alunos_analisados > 0 else 0.0

    # Relatório de evasão por curso
    evasion_by_course = {}
    if not df_processed_features.empty:
        df_risk_by_course = df_processed_features[df_processed_features['is_at_risk']].groupby('course_fullname').agg(
            alunos_em_risco=('user_id', 'nunique')
        ).reset_index()
        
        df_total_by_course = df_processed_features.groupby('course_fullname').agg(
            total_alunos=('user_id', 'nunique')
        ).reset_index()
        
        df_course_summary = pd.merge(df_total_by_course, df_risk_by_course, on='course_fullname', how='left').fillna(0)
        df_course_summary['alunos_em_risco'] = df_course_summary['alunos_em_risco'].astype(int)
        
        for _, row in df_course_summary.iterrows():
            course_name = row['course_fullname']
            total = row['total_alunos']
            at_risk = row['alunos_em_risco']
            percent = (at_risk / total * 100).round(2) if total > 0 else 0.0
            evasion_by_course[course_name] = {
                "total_alunos": total,
                "alunos_em_risco": at_risk,
                "percentual_risco": percent
            }

    # Detalhes dos alunos
    students_details = []
    for _, row in df_unique_students.iterrows():
        # Calcular o risco percentual do score global
        risk_percent = (row['overall_evasion_score'] / MAX_POSSIBLE_SCORE * 100).round(2) if MAX_POSSIBLE_SCORE > 0 else 0.0
        
        # Coletar as features adicionadas no feature engineering para o perfil do aluno
        student_courses_details = []
        # Filtrar o df_processed_features para este aluno e iterar pelos cursos
        df_student_courses = df_processed_features[df_processed_features['user_id'] == row['user_id']]
        for _, course_row in df_student_courses.iterrows():
            course_risk_percent = (course_row['evasion_score'] / MAX_POSSIBLE_SCORE * 100).round(2) if MAX_POSSIBLE_SCORE > 0 else 0.0
            
            # Resumo de ações recentes por tipo para o curso
            recent_actions_by_type_course_dict = {}
            # O df_processed_features já tem as colunas recent_action_*, mas elas são globais
            # A gente precisa do resumo de ações por tipo *específico do curso*
            # Se você não tem isso, podemos adicionar uma lógica para coletar do df_raw_logs_mapped
            # no run_feature_engineering, ou simplesmente omitir por enquanto ou usar as globais
            # por curso podemos pegar a contagem total de visualizados e graded que já calculamos
            # e as recent_actions_summary_global são o mais próximo que temos por enquanto.

            student_courses_details.append({
                "course_fullname": course_row['course_fullname'],
                "evasion_score": int(course_row['evasion_score']),
                "evasion_risk_pct": course_risk_percent, # Risco percentual para o curso
                "is_at_risk_in_this_course": bool(course_row['is_at_risk']), # Se o aluno está em risco neste curso
                "days_since_course_last_access": int(course_row['days_since_course_last_access']),
                "course_total_actions": int(course_row['course_total_actions']),
                "viewed_count_course": int(course_row['viewed_count_course']),
                "graded_count_course": int(course_row['graded_count_course']),
                "evasion_reasons_course": course_row['evasion_reasons'] # Razões específicas para o risco neste curso
            })


        # Resumo de ações recentes globais (mapear colunas 'recent_action_X' para um dicionário)
        recent_actions_summary_dict = {
            col.replace('recent_action_', ''): int(row[col])
            for col in row.index if col.startswith('recent_action_') and pd.notna(row[col])
        }

        students_details.append({
            "user_id": row['user_id'],
            "user_name": row['user_name'],
            "is_at_risk": bool(row['is_at_risk']),
            "overall_evasion_score": int(row['overall_evasion_score']),
            "overall_evasion_risk_pct": risk_percent,
            "overall_evasion_reasons": row['overall_evasion_reasons'], # NOVO CAMPO
            "days_since_last_access_global": int(row['days_since_last_access_global']),
            "total_actions_global": int(row['total_actions_global']),
            "unique_courses_accessed_global": int(row['unique_courses_accessed_global']),
            "forum_interactions_global": int(row['forum_interactions_global']),
            "quiz_interactions_global": int(row['quiz_interactions_global']),
            "presence_score_global": float(row['presence_score_global']),
            "courses_details": student_courses_details, # Detalhes de cada curso (agora com razões)
            "recent_actions_summary_global": recent_actions_summary_dict
        })

    return {
        "total_alunos_analisados": total_alunos_analisados,
        "alunos_em_risco": alunos_em_risco,
        "evasao_estimada_percentual": evasao_estimada_percentual,
        "evasao_por_curso": evasion_by_course,
        "alunos_detalhes": students_details
    }


def get_evasion_risk_students_for_professor(df_processed_features: pd.DataFrame, professor_name: str) -> list:
    """
    Retorna a lista de alunos em risco de evasão para um professor específico,
    filtrando pelos cursos que ele leciona. Retorna em formato de lista de dicionários.
    Agora inclui as razões de evasão.
    """
    professor_course_map_data = get_professor_course_mapping_data()
    professor_courses = professor_course_map_data.get(professor_name)

    if not professor_courses:
        print(f"Nenhum curso encontrado para o professor '{professor_name}' no mapeamento.")
        return []

    # Filtrar os dados para os cursos do professor E que estejam em risco
    risky_students_for_professor = df_processed_features[
        (df_processed_features['course_fullname'].isin(professor_courses)) &
        (df_processed_features['is_at_risk'])
    ].copy() # Usar .copy() para evitar SettingWithCopyWarning

    if risky_students_for_professor.empty:
        return []

    # Obter os detalhes globais de risco e score por aluno único
    df_unique_students = df_processed_features.drop_duplicates(subset=['user_id'])
    
    # Criar um dicionário para fácil lookup de detalhes globais e ações recentes e razões globais
    student_global_details = {}
    for _, row in df_unique_students.iterrows():
        recent_actions_summary_dict = {
            col.replace('recent_action_', ''): int(row[col])
            for col in row.index if col.startswith('recent_action_') and pd.notna(row[col])
        }
        student_global_details[row['user_id']] = {
            'overall_evasion_score': int(row['overall_evasion_score']),
            'is_at_risk_global': bool(row['is_at_risk']),
            'overall_evasion_reasons': row['overall_evasion_reasons'], # NOVO CAMPO
            'days_since_last_access_global': int(row['days_since_last_access_global']),
            'total_actions_global': int(row['total_actions_global']),
            'forum_interactions_global': int(row['forum_interactions_global']),
            'quiz_interactions_global': int(row['quiz_interactions_global']),
            'presence_score_global': float(row['presence_score_global']),
            'recent_actions_summary_global': recent_actions_summary_dict
        }

    report_list = []
    # Iterar sobre os alunos que estão em risco NOS CURSOS DESSE PROFESSOR
    for _, row in risky_students_for_professor.iterrows():
        user_id = row['user_id']
        global_details = student_global_details.get(user_id, {}) # Pega os detalhes globais do aluno

        # Calcular o risco percentual do score do curso (se aplicável)
        course_risk_percent = (row['evasion_score'] / MAX_POSSIBLE_SCORE * 100).round(2) if MAX_POSSIBLE_SCORE > 0 else 0.0

        report_list.append({
            "user_id": user_id,
            "user_name": row['user_name'],
            "course_fullname": row['course_fullname'],
            "is_at_risk_in_this_course": bool(row['is_at_risk']), # Indica se está em risco especificamente neste curso
            "course_evasion_score": int(row['evasion_score']),
            "course_evasion_risk_pct": course_risk_percent,
            "evasion_reasons_course": row['evasion_reasons'], # NOVO CAMPO
            "days_since_course_last_access": int(row['days_since_course_last_access']),
            "course_total_actions": int(row['course_total_actions']),
            "viewed_count_course": int(row['viewed_count_course']),
            "graded_count_course": int(row['graded_count_course']),
            # Adicionando informações globais do aluno para contexto
            "overall_evasion_score": global_details.get('overall_evasion_score', 0),
            "is_at_risk_global": global_details.get('is_at_risk_global', False),
            "overall_evasion_reasons": global_details.get('overall_evasion_reasons', []), # NOVO CAMPO
            "days_since_last_access_global": global_details.get('days_since_last_access_global', 0),
            "total_actions_global": global_details.get('total_actions_global', 0),
            "forum_interactions_global": global_details.get('forum_interactions_global', 0),
            "quiz_interactions_global": global_details.get('quiz_interactions_global', 0),
            "presence_score_global": global_details.get('presence_score_global', 0.0),
            "recent_actions_summary_global": global_details.get('recent_actions_summary_global', {})
        })

    # Remover duplicatas de alunos que aparecem em múltiplos cursos do mesmo professor,
    # se o objetivo for uma lista de alunos (e não de alunos por curso).
    # Se quiser uma lista de (aluno, curso) em risco, mantenha assim.
    # Se quiser uma lista de alunos em risco e seus cursos relacionados, agrupe.
    # Por enquanto, vou manter como aluno-curso específico para o professor.
    return sorted(report_list, key=lambda x: (x['course_fullname'], x['user_name']))

# Teste local (para ser executado apenas se o arquivo for chamado diretamente)
if __name__ == '__main__':
    print("Executando teste básico para evasion_prediction_logic.py")
    
    # Exemplo de DataFrame de logs brutos (apenas para simulação de teste)
    mock_raw_logs = pd.DataFrame({
        'user_id': ['user1', 'user1', 'user2', 'user1', 'user2', 'user3', 'user3', 'user1', 'user2', 'user3', 'user4', 'user4', 'user4'],
        'name': ['Aluno A', 'Aluno A', 'Aluno B', 'Aluno A', 'Aluno B', 'Aluno C', 'Aluno C', 'Aluno A', 'Aluno B', 'Aluno C', 'Aluno D', 'Aluno D', 'Aluno D'],
        'date': [
            datetime.now() - timedelta(days=5), # user1 - Recente
            datetime.now() - timedelta(days=10), # user1 - Recente
            datetime.now() - timedelta(days=35), # user2 - Inativo global
            datetime.now() - timedelta(days=2), # user1 - Ação bem recente
            datetime.now() - timedelta(days=40), # user2 - Inativo global
            datetime.now() - timedelta(days=10), # user3 - Recente
            datetime.now() - timedelta(days=50),# user3 - Inativo global
            datetime.now() - timedelta(days=6), # user1 - Ação
            datetime.now() - timedelta(days=20), # user2 - Ação no curso
            datetime.now() - timedelta(days=25), # user3 - Ação no curso
            datetime.now() - timedelta(days=10), # user4 - Recente
            datetime.now() - timedelta(days=12), # user4 - Recente
            datetime.now() - timedelta(days=14)  # user4 - Recente
        ],
        'action': ['core_course_view_course', 'mod_assign_submit_form', 'core_user_login', 'mod_forum_post_created', 'mod_resource_view_resource', 'core_course_view_course', 'mod_quiz_attempt_started', 'mod_url_viewed', 'mod_quiz_attempt_submitted', 'mod_feedback_view_feedback', 'core_user_login', 'core_course_view_course', 'mod_forum_view_forum'],
        'course_fullname': ['Curso X', 'Curso X', 'Curso Y', 'Curso X', 'Curso Z', 'Curso Y', 'Curso W', 'Curso X', 'Curso Z', 'Curso Y', 'Curso A', 'Curso A', 'Curso A']
    })

    print("\n--- Testando run_feature_engineering ---")
    df_features = run_feature_engineering(mock_raw_logs)
    print("DataFrame de features gerado:")
    print(df_features[['user_id', 'course_fullname', 'days_since_last_access_global', 'days_since_course_last_access', 'total_actions_global', 'course_total_actions']].head())

    print("\n--- Testando calculate_evasion_risk_scores ---")
    df_risks = calculate_evasion_risk_scores(df_features)
    print("DataFrame de riscos calculado:")
    # Exibe as novas colunas
    print(df_risks[['user_id', 'course_fullname', 'evasion_score', 'evasion_reasons', 'overall_evasion_score', 'overall_evasion_reasons', 'is_at_risk', 'is_at_risk_global']].head(10))

    print("\n--- Testando get_overall_evasion_report ---")
    overall_report = get_overall_evasion_report(df_risks)
    print("Relatório geral de evasão:")
    # Imprime os detalhes de um aluno para ver as novas razões
    if overall_report['alunos_detalhes']:
        print(json.dumps(overall_report['alunos_detalhes'][0], indent=2, default=str)) # default=str para serializar datas/times
    else:
        print("Nenhum aluno detalhado no relatório.")

    print("\n--- Testando get_evasion_risk_students_for_professor ---")
    professor_name_test = "João Silva" # Baseado no FALLBACK_PROFESSOR_COURSE_MAP
    prof_report = get_evasion_risk_students_for_professor(df_risks, professor_name_test)
    print(f"Alunos em risco para o professor {professor_name_test}:")
    print(json.dumps(prof_report, indent=2, default=str))

    professor_name_test2 = "Maria Oliveira"
    prof_report2 = get_evasion_risk_students_for_professor(df_risks, professor_name_test2)
    print(f"Alunos em risco para o professor {professor_name_test2}:")
    print(json.dumps(prof_report2, indent=2, default=str))