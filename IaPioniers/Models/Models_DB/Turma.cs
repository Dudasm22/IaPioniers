using IaPioniers.Models.Models_DB;
using System.Collections.Generic; 

namespace IaPioniers.Models
{
    public class Turma
    {
        public int IdTurma { get; set; } 

        public string Codigo { get; set; } 
        public int AnoLetivo { get; set; } 


        public int CursoId { get; set; }
        public Curso Curso { get; set; }

       
        public ICollection<Professor> TurmaProfessores { get; set; } = new List<Professor>();
    }
}