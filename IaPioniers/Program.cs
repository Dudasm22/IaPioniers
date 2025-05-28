using Microsoft.AspNetCore.Identity;
using Microsoft.EntityFrameworkCore;
using IaPioniers.Data; // Este será o namespace do seu futuro DbContext
using IaPioniers.Models; // Seu namespace para ApplicationUser, Professor, Coordenador
using IaPioniers.Services; // Seu namespace para IaPioniersApiService

var builder = WebApplication.CreateBuilder(args);

// 1. Configuração do Banco de Dados para Entity Framework Core e Identity
var connectionString = builder.Configuration.GetConnectionString("DefaultConnection") ??
                       throw new InvalidOperationException("Connection string 'DefaultConnection' not found.");

builder.Services.AddDbContext<ApplicationDbContext>(options =>
    options.UseSqlServer(connectionString)); // Se for SQL Server

// Adicione isso para páginas de erro de desenvolvimento relacionadas a banco de dados (útil)
builder.Services.AddDatabaseDeveloperPageExceptionFilter();

// 2. Configuração do Identity
builder.Services.AddDefaultIdentity<ApplicationUser>(options =>
{
    // Opções de senha, bloqueio, etc.
    options.SignIn.RequireConfirmedAccount = false; // Ajuste conforme sua necessidade
    options.Password.RequireDigit = false;
    options.Password.RequiredLength = 6;
    options.Password.RequireNonAlphanumeric = false;
    options.Password.RequireUppercase = false;
    options.Password.RequireLowercase = false;
})
.AddRoles<IdentityRole>() // Habilita o uso de Roles (Professor, Coordenador)
.AddEntityFrameworkStores<ApplicationDbContext>(); // Conecta o Identity ao seu DbContext

// 3. Configuração do HttpClientFactory para sua API Python
builder.Services.AddHttpClient<IaPioniersApiService>(client =>
{
    client.BaseAddress = new Uri(builder.Configuration["PythonApiSettings:BaseUrl"]);
    // Adicione cabeçalhos padrão aqui se sua API precisar (ex: Accept, Auth, etc.)
    client.DefaultRequestHeaders.Add("Accept", "application/json");
});

// Add services to the container.
builder.Services.AddControllersWithViews();
builder.Services.AddRazorPages(); // Necessário se você for usar as páginas padrão do Identity UI
builder.Services.AddSingleton<ProfessorCourseMappingService>();

var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.UseMigrationsEndPoint(); // Para o filtro de exceção do EF Core
}
else
{
    app.UseExceptionHandler("/Home/Error");
    // The default HSTS value is 30 days. You may want to change this for production scenarios, see https://aka.ms/aspnetcore-hsts.
    app.UseHsts();
}

app.UseHttpsRedirection();
app.UseStaticFiles();

app.UseRouting();

// Middleware de Autenticação e Autorização (ORDEM IMPORTA!)
app.UseAuthentication(); // Deve vir antes de UseAuthorization
app.UseAuthorization();

app.MapControllerRoute(
    name: "default",
    pattern: "{controller=Home}/{action=Index}/{id?}");
app.MapRazorPages(); // Mapeia as rotas para as páginas Razor do Identity UI

app.Run();