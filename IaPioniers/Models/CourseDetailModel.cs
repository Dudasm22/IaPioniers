using System.Collections.Generic;
using System.Text.Json.Serialization; // Adicione esta linha

namespace IaPioniers.Models
{
    public class CourseDetailModel
    {
        [JsonPropertyName("course_fullname")]
        public string CourseFullname { get; set; }

        [JsonPropertyName("evasion_score")]
        public int EvasionScore { get; set; }

        [JsonPropertyName("evasion_risk_pct")]
        public double EvasionRiskPct { get; set; }

        [JsonPropertyName("is_at_risk_in_this_course")]
        public bool IsAtRiskInThisCourse { get; set; }

        [JsonPropertyName("evasion_reasons_course")]
        public List<string> EvasionReasonsCourse { get; set; }

        [JsonPropertyName("days_since_course_last_access")]
        public int DaysSinceCourseLastAccess { get; set; }

        [JsonPropertyName("course_total_actions")]
        public int CourseTotalActions { get; set; }

        [JsonPropertyName("viewed_count_course")]
        public int ViewedCountCourse { get; set; }

        [JsonPropertyName("graded_count_course")]
        public int GradedCountCourse { get; set; }
    }
}
