using System.Text.Json.Serialization;

namespace IaPioniers.Models
{
    public class CourseEvasionSummary
    {
        [JsonPropertyName("total_alunos")]
        public int TotalAlunos { get; set; }

        [JsonPropertyName("alunos_em_risco")]
        public int AlunosEmRisco { get; set; }

        [JsonPropertyName("percentual_risco")]
        public double PercentualRisco { get; set; }
    }
}
