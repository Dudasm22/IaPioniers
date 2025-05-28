// Data/ApplicationDbContext.cs
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Identity.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore;
using IaPioniers.Models; 
using IaPioniers.Models.Models_DB; 

namespace IaPioniers.Data
{
    public class ApplicationDbContext : IdentityDbContext<ApplicationUser, IdentityRole, string>
    {
        public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options)
            : base(options)
        {
        }

        public DbSet<Curso> Cursos { get; set; }
        public DbSet<Turma> Turmas { get; set; }
        public DbSet<Professor> Professores { get; set; }
        public DbSet<Coordenador> Coordenadores { get; set; }
        // REMOVA: public DbSet<TurmaProfessor> TurmaProfessores { get; set; } // Não é mais necessário como DbSet explícito

        protected override void OnModelCreating(ModelBuilder builder)
        {
            base.OnModelCreating(builder);

            // Renomear tabelas do Identity (opcional)
            builder.Entity<ApplicationUser>().ToTable("Users");
            builder.Entity<IdentityRole>().ToTable("Roles");
            builder.Entity<IdentityUserRole<string>>().ToTable("UserRoles");
            builder.Entity<IdentityUserClaim<string>>().ToTable("UserClaims");
            builder.Entity<IdentityUserLogin<string>>().ToTable("UserLogins");
            builder.Entity<IdentityRoleClaim<string>>().ToTable("RoleClaims");
            builder.Entity<IdentityUserToken<string>>().ToTable("UserTokens");

            // Configuração Many-to-Many entre Turma e Professor (se EF Core >= 5.0)
            // O EF Core irá automaticamente criar a tabela de junção "TurmaProfessor"
            // com as chaves estrangeiras TurmaId e ProfessorId.
            builder.Entity<Professor>()
                .HasMany(p => p.Turmas)       // Um Professor tem muitas Turmas
                .WithMany(t => t.Professores) // Uma Turma tem muitos Professores
                // .UsingEntity(j => j.ToTable("TurmaProfessor")); // Opcional: especificar o nome da tabela de junção e configurar chaves adicionais, se necessário.
                // Se você não usar UsingEntity, o EF Core criará um nome padrão (ex: ProfessorTurma).
                // Se quiser manter o nome "TurmaProfessor", descomente esta linha.

            // Configuração One-to-One para ApplicationUser e Professor
            builder.Entity<ApplicationUser>()
                .HasOne(au => au.Professor)
                .WithOne(p => p.ApplicationUser)
                .HasForeignKey<Professor>(p => p.ApplicationUserId)
                .IsRequired(false);

            // Configuração One-to-One para ApplicationUser e Coordenador
            builder.Entity<ApplicationUser>()
                .HasOne(au => au.Coordenador)
                .WithOne(c => c.ApplicationUser)
                .HasForeignKey<Coordenador>(c => c.ApplicationUserId)
                .IsRequired(false);
        }
    }
}