using System.Collections.Generic;
using System.Text.Json.Serialization; // Adicione esta linha

namespace IaPioniers.Models
{
    // *** ATENÇÃO: Adicione JsonPropertyName aqui também ***
    public class EvasionReportModel
    {
        [JsonPropertyName("total_alunos_analisados")]
        public int TotalAlunosAnalisados { get; set; }

        [JsonPropertyName("alunos_em_risco")]
        public int AlunosEmRisco { get; set; }

        [JsonPropertyName("evasao_estimada_percentual")]
        public double EvasaoEstimadaPercentual { get; set; }

        [JsonPropertyName("evasao_por_curso")]
        public Dictionary<string, CourseEvasionSummary> EvasaoPorCurso { get; set; }

        [JsonPropertyName("alunos_detalhes")]
        public List<StudentDetailModel> AlunosDetalhes { get; set; }
    }
}
