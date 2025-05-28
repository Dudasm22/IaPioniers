using System.Net.Http;
using System.Threading.Tasks;
using System.Collections.Generic;
using System.Text.Json; // Use System.Text.Json
using System; // Para Uri.EscapeDataString
using IaPioniers.Models; // Para os seus modelos de resposta da API

namespace IaPioniers.Services
{
    public class IaPioniersApiService
    {
        private readonly HttpClient _httpClient;
        private readonly JsonSerializerOptions _jsonSerializerOptions; // Opcional: para configurações de serialização

        public IaPioniersApiService(HttpClient httpClient)
        {
            _httpClient = httpClient;
            // Configurar opções de serialização (opcional, mas recomendado para snake_case)
            _jsonSerializerOptions = new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true, // Permite mapeamento de camelCase para PascalCase
                ReadCommentHandling = JsonCommentHandling.Skip,
                AllowTrailingCommas = true,
                // Se sua API Python usa snake_case e você não quer usar [JsonPropertyName] em cada propriedade,
                // você pode adicionar um conversor de nome de propriedade aqui:
                // PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower, // Isso exige um conversor customizado se você misturar
                // O mais seguro é usar [JsonPropertyName] ou garantir que os nomes das propriedades em C# sejam exatamente iguais aos do JSON.
                // Com [JsonPropertyName] você não precisa de PropertyNamingPolicy.
            };
        }

        // Endpoint: /api/evasion-report
        public async Task<EvasionReportModel> GetEvasionReportAsync()
        {
            try
            {
                var response = await _httpClient.GetAsync("api/evasion-report");
                response.EnsureSuccessStatusCode();

                var jsonString = await response.Content.ReadAsStringAsync();
                return JsonSerializer.Deserialize<EvasionReportModel>(jsonString, _jsonSerializerOptions);
            }
            catch (HttpRequestException ex)
            {
                Console.WriteLine($"Erro ao obter relatório de evasão: {ex.Message}");
                return null;
            }
        }

        // Endpoint: /api/professor-evasion-risk?professor_name=...
        public async Task<List<StudentDetailModel>> GetProfessorEvasionRiskAsync(string professorName)
        {
            try
            {
                var response = await _httpClient.GetAsync($"api/professor-evasion-risk?professor_name={Uri.EscapeDataString(professorName)}");
                response.EnsureSuccessStatusCode();

                var jsonString = await response.Content.ReadAsStringAsync();
                return JsonSerializer.Deserialize<List<StudentDetailModel>>(jsonString, _jsonSerializerOptions);
            }
            catch (HttpRequestException ex)
            {
                Console.WriteLine($"Erro ao obter risco de evasão para professor {professorName}: {ex.Message}");
                return null;
            }
        }

        // Endpoint: /api/student-profile/<user_id>
        public async Task<StudentDetailModel> GetStudentProfileAsync(string userId)
        {
            try
            {
                var response = await _httpClient.GetAsync($"api/student-profile/{userId}");

                if (response.StatusCode == System.Net.HttpStatusCode.NotFound)
                {
                    return null;
                }

                response.EnsureSuccessStatusCode();

                var jsonString = await response.Content.ReadAsStringAsync();
                return JsonSerializer.Deserialize<StudentDetailModel>(jsonString, _jsonSerializerOptions);
            }
            catch (HttpRequestException ex)
            {
                Console.WriteLine($"Erro ao obter perfil do aluno {userId}: {ex.Message}");
                return null;
            }
        }

        // Método para GetStudentProfileDetailedAsync (se aplicável ao seu uso de StudentProfileModel)
        public async Task<StudentProfileModel> GetStudentProfileDetailedAsync(string userId)
        {
            try
            {
                var response = await _httpClient.GetAsync($"api/student-profile/{userId}");
                if (response.StatusCode == System.Net.HttpStatusCode.NotFound)
                {
                    return null;
                }
                response.EnsureSuccessStatusCode();

                var jsonString = await response.Content.ReadAsStringAsync();
                // Ajuste aqui se o JSON da API retornar um objeto que mapeia diretamente para StudentProfileModel
                // (e não StudentDetailModel)
                return JsonSerializer.Deserialize<StudentProfileModel>(jsonString, _jsonSerializerOptions);
            }
            catch (HttpRequestException ex)
            {
                Console.WriteLine($"Erro ao obter detalhes de ações recentes do aluno {userId}: {ex.Message}");
                return null;
            }
        }
    }
}