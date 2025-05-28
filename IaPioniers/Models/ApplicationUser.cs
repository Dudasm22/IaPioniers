using IaPioniers.Models.Models_DB;
using Microsoft.AspNetCore.Identity;
using System.Collections.Generic;

namespace IaPioniers.Models
{
    public class ApplicationUser : IdentityUser
    {
        public string NomeCompleto { get; set; }

        // Um ApplicationUser pode ser um Professor
        public Professor Professor { get; set; } // Propriedade de navegação

        // Um ApplicationUser pode ser um Coordenador
        public Coordenador Coordenador { get; set; } // Propriedade de navegação
    }
}
