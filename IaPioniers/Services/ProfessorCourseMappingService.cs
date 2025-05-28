// Services/ProfessorCourseMappingService.cs
using Microsoft.Extensions.Hosting; // Para IWebHostEnvironment ou IHostEnvironment
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Configuration; // Para ler do appsettings.json
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using System.Threading.Tasks;
using IaPioniers.Models; // Para ProfessorCourseMapping

namespace IaPioniers.Services
{
    public class ProfessorCourseMappingService
    {
        private readonly ILogger<ProfessorCourseMappingService> _logger;
        private readonly IHostEnvironment _env; // Usar IHostEnvironment ou IWebHostEnvironment
        private readonly string _mappingFilePath;
        private Dictionary<string, List<string>> _professorCourseMappingCache; // Cache em memória

        public ProfessorCourseMappingService(ILogger<ProfessorCourseMappingService> logger, IHostEnvironment env, IConfiguration configuration)
        {
            _logger = logger;
            _env = env;
            _mappingFilePath = configuration["ProfessorMappingSettings:FilePath"];

            // Carregar o mapeamento na inicialização do serviço (ou sob demanda, dependendo da necessidade)
            _professorCourseMappingCache = LoadMappingFile().GetAwaiter().GetResult();
        }

        private async Task<Dictionary<string, List<string>>> LoadMappingFile()
        {
            var mappingFullPath = Path.Combine(_env.ContentRootPath, _mappingFilePath);

            if (!File.Exists(mappingFullPath))
            {
                _logger.LogError($"Arquivo de mapeamento de professor/curso não encontrado em: {mappingFullPath}");
                return new Dictionary<string, List<string>>();
            }

            try
            {
                await using var stream = File.OpenRead(mappingFullPath);
                // Deserialize o JSON diretamente para Dictionary<string, List<string>>
                var mapping = await JsonSerializer.DeserializeAsync<Dictionary<string, List<string>>>(stream,
                    new JsonSerializerOptions { PropertyNameCaseInsensitive = true }); // Permite flexibilidade de nomes

                if (mapping == null)
                {
                    _logger.LogWarning($"Arquivo de mapeamento de professor/curso vazio ou mal formatado: {mappingFullPath}");
                    return new Dictionary<string, List<string>>();
                }

                _logger.LogInformation($"Mapeamento de professor/curso carregado com sucesso de: {mappingFullPath}");
                return mapping;
            }
            catch (JsonException ex)
            {
                _logger.LogError(ex, $"Erro de deserialização JSON ao carregar mapeamento de professor/curso de: {mappingFullPath}");
                return new Dictionary<string, List<string>>();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Erro ao carregar mapeamento de professor/curso de: {mappingFullPath}");
                return new Dictionary<string, List<string>>();
            }
        }

        public Dictionary<string, List<string>> GetProfessorCourseMapping()
        {
            return _professorCourseMappingCache;
        }

        public List<string> GetCoursesForProfessor(string professorName)
        {
            if (_professorCourseMappingCache.TryGetValue(professorName, out var courses))
            {
                return courses;
            }
            return new List<string>(); // Retorna lista vazia se o professor não for encontrado
        }
    }
}