# student_profile_generator.py
import pandas as pd
from datetime import datetime, timedelta
import json

# Importar o mapeamento de ações e a função de mapeamento do evasion_prediction_logic
from evasion_prediction_logic import ACTION_MAPPING, map_action_name

# Importar a função de relatório geral para obter a estrutura base de um aluno
from evasion_prediction_logic import get_overall_evasion_report # Reutilizamos isso para a estrutura base do perfil

def get_student_profile_details(
    user_id: int,
    df_all_students_features: pd.DataFrame,
    get_raw_logs_func # Função para obter logs brutos (passada do app.py)
) -> dict | None:
    """
    Gera um dicionário detalhado do perfil de um aluno específico.
    Inclui informações de risco, interações e presença.

    Args:
        user_id (int): O ID do aluno.
        df_all_students_features (pd.DataFrame): DataFrame completo com todas as features e scores (para todos os alunos).
        get_raw_logs_func: Uma função (callable) que, quando chamada, retorna o df_raw_logs.
                           Isso permite carregar os logs brutos sob demanda sem duplicação de lógica.

    Returns:
        dict | None: Um dicionário com o perfil do aluno ou None se o aluno não for encontrado.
    """
    print(f"[{datetime.now()}] (Perfil do Aluno) Gerando perfil para o aluno {user_id}...")

    if df_all_students_features.empty:
        print(f"[{datetime.now()}] (Perfil do Aluno) DataFrame de features vazio. Não é possível gerar perfil.")
        return None

    # Obter o resumo geral do aluno a partir da lógica de relatório consolidado
    # Esta função já formata bem os dados globais de um aluno.
    overall_report = get_overall_evasion_report(df_all_students_features)
    student_summary = next((item for item in overall_report['alunos_detalhes'] if item["user_id"] == user_id), None)

    if student_summary is None:
        print(f"[{datetime.now()}] (Perfil do Aluno) Aluno {user_id} não encontrado nos dados processados.")
        return None

    # Agora, para as ações brutas recentes, precisamos do df_raw_logs
    df_raw_logs = get_raw_logs_func() # Chama a função para obter os logs brutos

    if df_raw_logs is None or df_raw_logs.empty:
        print(f"[{datetime.now()}] (Perfil do Aluno) Aviso: Logs brutos não disponíveis para detalhes de ações recentes.")
        student_summary['all_recent_actions_detailed'] = []
    else:
        student_recent_logs = df_raw_logs[df_raw_logs['user_id'] == user_id].sort_values(by='date', ascending=False)
        # Mapear ações para nomes mais legíveis no log bruto antes de retornar
        student_recent_logs['mapped_action'] = student_recent_logs['action'].apply(map_action_name)
        
        # Limitar a 50 ações mais recentes para não sobrecarregar o JSON
        # Adicionar 'timestamp_moodle' se existir na API e 'course_id' para mais detalhes
        cols_to_include = ['date', 'mapped_action', 'course_fullname']
        if 'timestamp_moodle' in student_recent_logs.columns:
            cols_to_include.append('timestamp_moodle')
        if 'course_id' in student_recent_logs.columns:
            cols_to_include.append('course_id')

        student_summary['all_recent_actions_detailed'] = student_recent_logs[cols_to_include].head(50).to_dict(orient='records')
        
        # Garante que a data seja serializável para JSON
        for action in student_summary['all_recent_actions_detailed']:
            if 'date' in action and isinstance(action['date'], pd.Timestamp):
                action['date'] = action['date'].isoformat()


    print(f"[{datetime.now()}] (Perfil do Aluno) Perfil gerado com sucesso para o aluno {user_id}.")
    return student_summary

if __name__ == '__main__':
    print("Testando student_profile_generator.py (requer dados simulados).")
    # Exemplo de teste (requer df_all_students_features e df_raw_logs simulados)
    
    # Criar um mock df_all_students_features (com todas as colunas que get_overall_evasion_report espera)
    mock_df_features = pd.DataFrame([{
        'user_id': 'USER_001',
        'user_name': 'Aluno Teste',
        'overall_evasion_score': 70,
        'is_at_risk': True,
        'days_since_last_access_global': 40,
        'total_actions_global': 5,
        'unique_courses_accessed_global': 1,
        'forum_interactions_global': 1,
        'quiz_interactions_global': 0,
        'presence_score_global': 25.5,
        'course_fullname': 'Curso A', # Precisa de pelo menos uma linha por curso
        'evasion_score': 70, # Score específico do curso
        'days_since_course_last_access': 40,
        'course_total_actions': 5,
        'viewed_count_course': 3,
        'graded_count_course': 2,
        'recent_action_Login no Moodle': 1, # Exemplo de coluna de ação recente
        'recent_action_Visualizou Curso': 2,
        'recent_action_Visualizou Tarefa': 0,
        # ... outras colunas recent_action_... (preencha com 0 se não existirem)
    },{
        'user_id': 'USER_001',
        'user_name': 'Aluno Teste',
        'overall_evasion_score': 70,
        'is_at_risk': True,
        'days_since_last_access_global': 40,
        'total_actions_global': 5,
        'unique_courses_accessed_global': 1,
        'forum_interactions_global': 1,
        'quiz_interactions_global': 0,
        'presence_score_global': 25.5,
        'course_fullname': 'Curso B', # Outro curso para o mesmo aluno
        'evasion_score': 30,
        'days_since_course_last_access': 20,
        'course_total_actions': 3,
        'viewed_count_course': 2,
        'graded_count_course': 1,
        'recent_action_Login no Moodle': 1,
        'recent_action_Visualizou Curso': 2,
        'recent_action_Visualizou Tarefa': 0,
    }
    ])
    
    # Adicionar outras colunas 'recent_action_' para ter um conjunto completo se o DF real tiver
    all_possible_actions = list(ACTION_MAPPING.values())
    for action_name in all_possible_actions:
        col_name = f'recent_action_{action_name}'
        if col_name not in mock_df_features.columns:
            mock_df_features[col_name] = 0

    # Criar um mock df_raw_logs
    mock_raw_logs = pd.DataFrame([
        {'user_id': 'USER_001', 'name': 'Aluno Teste', 'date': datetime.now() - timedelta(days=1), 'action': 'core_user_login', 'course_fullname': 'N/A'},
        {'user_id': 'USER_001', 'name': 'Aluno Teste', 'date': datetime.now() - timedelta(days=3), 'action': 'mod_forum_post_created', 'course_fullname': 'Curso A'},
        {'user_id': 'USER_001', 'name': 'Aluno Teste', 'date': datetime.now() - timedelta(days=5), 'action': 'core_course_view_course', 'course_fullname': 'Curso A'},
        {'user_id': 'USER_001', 'name': 'Aluno Teste', 'date': datetime.now() - timedelta(days=8), 'action': 'mod_assign_view_assign', 'course_fullname': 'Curso B'},
        # ... adicione mais logs conforme necessário
    ])

    # Simular a função get_raw_logs_func
    def mock_get_raw_logs():
        return mock_raw_logs

    user_id_test = 'USER_001'
    profile = get_student_profile_details(user_id_test, mock_df_features, mock_get_raw_logs)
    if profile:
        print(f"\nPerfil gerado para {user_id_test}:")
        print(json.dumps(profile, indent=2, default=str))
    else:
        print(f"\nNão foi possível gerar perfil para {user_id_test}.")