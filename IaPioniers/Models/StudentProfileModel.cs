using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace IaPioniers.Models
{
    public class StudentProfileModel
    {
        [JsonPropertyName("all_recent_actions_detailed")]
        public List<RecentActionDetailModel> AllRecentActionsDetailed { get; set; }
    }
}