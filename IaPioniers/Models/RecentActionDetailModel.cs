using System;
using System.Text.Json.Serialization; // Adicione esta linha

namespace IaPioniers.Models
{
    public class RecentActionDetailModel
    {
        [JsonPropertyName("date")]
        public DateTime Date { get; set; }

        [JsonPropertyName("mapped_action")]
        public string MappedAction { get; set; }

        [JsonPropertyName("course_fullname")]
        public string CourseFullname { get; set; }

        [JsonPropertyName("timestamp_moodle")]
        public long? TimestampMoodle { get; set; }

        [JsonPropertyName("course_id")]
        public int? CourseId { get; set; }
    }
}