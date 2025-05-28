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
      

        protected override void OnModelCreating(ModelBuilder builder)
        {
            base.OnModelCreating(builder);

         
            builder.Entity<ApplicationUser>().ToTable("Users");
            builder.Entity<IdentityRole>().ToTable("Roles");
            builder.Entity<IdentityUserRole<string>>().ToTable("UserRoles");
            builder.Entity<IdentityUserClaim<string>>().ToTable("UserClaims");
            builder.Entity<IdentityUserLogin<string>>().ToTable("UserLogins");
            builder.Entity<IdentityRoleClaim<string>>().ToTable("RoleClaims");
            builder.Entity<IdentityUserToken<string>>().ToTable("UserTokens");


            builder.Entity<Professor>()
                .HasMany(p => p.Turmas)      
                .WithMany(t => t.Professores) 
                .UsingEntity(j => j.ToTable("TurmaProfessor"));
               
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