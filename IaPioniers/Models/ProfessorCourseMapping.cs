using System.Collections.Generic;

namespace IaPioniers.Models

{
    public class ProfessorCourseMapping
    {
        public Dictionary<string, List<string>> Mapping { get; set; } = new Dictionary<string, List<string>>();
    }
}
