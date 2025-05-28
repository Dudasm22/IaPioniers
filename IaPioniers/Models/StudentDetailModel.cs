using System.Collections.Generic;
using System.Text.Json.Serialization; // Adicione esta linha

namespace IaPioniers.Models
{
    public class StudentDetailModel
    {
        [JsonPropertyName("user_id")]
        public string UserId { get; set; }

        [JsonPropertyName("user_name")]
        public string UserName { get; set; }

        [JsonPropertyName("is_at_risk")]
        public bool IsAtRisk { get; set; }

        [JsonPropertyName("overall_evasion_score")]
        public int OverallEvasionScore { get; set; }

        [JsonPropertyName("overall_evasion_risk_pct")]
        public double OverallEvasionRiskPct { get; set; }

        [JsonPropertyName("overall_evasion_reasons")]
        public List<string> OverallEvasionReasons { get; set; }

        [JsonPropertyName("days_since_last_access_global")]
        public int DaysSinceLastAccessGlobal { get; set; }

        [JsonPropertyName("total_actions_global")]
        public int TotalActionsGlobal { get; set; }

        [JsonPropertyName("unique_courses_accessed_global")]
        public int UniqueCoursesAccessedGlobal { get; set; }

        [JsonPropertyName("forum_interactions_global")]
        public int ForumInteractionsGlobal { get; set; }

        [JsonPropertyName("quiz_interactions_global")]
        public int QuizInteractionsGlobal { get; set; }

        [JsonPropertyName("presence_score_global")]
        public double PresenceScoreGlobal { get; set; }

        [JsonPropertyName("courses_details")]
        public List<CourseDetailModel> CoursesDetails { get; set; }

        [JsonPropertyName("recent_actions_summary_global")]
        public Dictionary<string, int> RecentActionsSummaryGlobal { get; set; }

        [JsonPropertyName("all_recent_actions_detailed")]
        public List<RecentActionDetailModel> AllRecentActionsDetailed { get; set; }
    }
}
