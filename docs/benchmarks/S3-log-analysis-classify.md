# S3 – Análise de log estruturado, classificação de severidade e geração de resumo

## 1. Identificação

- **Nome**: S3 – Análise de log estruturado, classificação de severidade e geração de resumo
- **Nível**: 3 (conforme `docs/benchmarks/evaluation-framework.md`, seção 2)
- **Data de criação**: 2026-04-24
- **Cenários anteriores**: S1 (health check estático), S2 (health check com parsing e JSON)

## 2. Objetivo

O agente deve:

1. Ler um arquivo de log em formato syslog estruturado via tool `read_file`.
2. Analisar as linhas do log.
3. Classificar a severidade global: `info`, `warning` ou `critical`.
4. Identificar o `primary_issue` e os `secondary_issues`.
5. Determinar `requires_action` (boolean).
6. Gerar um `summary` operacional em português do Brasil (1 a 2 frases).
7. Retornar o resultado como JSON puro, sem markdown.

Diferença em relação ao S2: em S3 não há execução de script — a tarefa é ler, interpretar e classificar.
A única tool disponível é `read_file`.

## 3. Tools disponíveis

Apenas `read_file`. Sem `run_bash`, sem `rename_file`, sem qualquer outra tool.

| Tool | Descrição | Parâmetros |
|------|-----------|------------|
| `read_file` | Lê um arquivo local e retorna seu conteúdo como string. | `path` (string) — caminho absoluto do arquivo |

O script implementa `read_file` via `Path(path).read_text(encoding='utf-8')` — sem subprocess.

## 4. Schema JSON de saída

O modelo deve retornar JSON puro com exatamente este schema:

```json
{
  "case_id": "<string>",
  "severity": "<info|warning|critical>",
  "primary_issue": "<string ou 'none'>",
  "secondary_issues": ["<string>", ...],
  "host": "<string>",
  "timestamp": "<string ISO 8601 com Z>",
  "requires_action": <boolean>,
  "summary": "<string em português do Brasil>"
}
```

### Tipos e restrições

| Campo | Tipo | Restrição |
|-------|------|-----------|
| `case_id` | string | identificador do fixture (ex: `info-001`) |
| `severity` | string | exatamente `info`, `warning` ou `critical` |
| `primary_issue` | string | problema principal, ou `"none"` se tudo OK |
| `secondary_issues` | array de strings | lista de problemas secundários; `[]` se nenhum |
| `host` | string | hostname extraído do log |
| `timestamp` | string | timestamp da última linha do log, ISO 8601 com sufixo `Z` |
| `requires_action` | boolean | `true` se severity for `warning` ou `critical`; `false` se `info` |
| `summary` | string | 1 a 2 frases em português do Brasil; entre 20 e 300 caracteres |

## 5. Prompt fixo do cenário S3

DECISÃO: texto fixo, nunca alterar entre runs nem entre baterias.
O placeholder `{log_path}` é substituído pelo caminho absoluto do fixture no script.

```
Leia o arquivo de log em {log_path} e analise seu conteúdo.
Com base nas linhas do log, gere um JSON com o seguinte schema:
{
  "case_id": "<identificador do caso, ex: info-001>",
  "severity": "<info|warning|critical>",
  "primary_issue": "<problema principal identificado, ou 'none' se tudo OK>",
  "secondary_issues": ["<lista de problemas secundários>"],
  "host": "<hostname extraído do log>",
  "timestamp": "<timestamp da última linha do log em ISO 8601 com Z>",
  "requires_action": <true se severity for warning ou critical, false se info>,
  "summary": "<resumo operacional em português do Brasil, 1 a 2 frases>"
}
Regras de classificação:
- critical: qualquer linha com level=CRITICAL
- warning: nenhuma CRITICAL, mas pelo menos uma WARNING
- info: todas as linhas são INFO
Responda APENAS com o JSON. Sem markdown. Sem texto adicional.
```

## 6. Regras de classificação (ground truth)

| Condição | Severidade resultante |
|----------|-----------------------|
| Qualquer linha com `level=CRITICAL` | `critical` |
| Nenhuma `CRITICAL`, mas pelo menos uma `WARNING` | `warning` |
| Todas as linhas são `INFO` | `info` |

A regra é aplicada à severidade global do arquivo — não linha a linha.

## 7. Casos de teste

K = 4 runs, um por caso de fixture. Ordem de execução: info-001 → warning-001 → critical-001 → mixed-001.

| Case | Fixture | Severidade esperada | Primary issue | Ação requerida |
|------|---------|---------------------|---------------|----------------|
| `info-001` | `fixtures/health-logs/info/info-001.log` | `info` | `none` | `false` |
| `warning-001` | `fixtures/health-logs/warning/warning-001.log` | `warning` | `high_cpu_usage` | `true` |
| `critical-001` | `fixtures/health-logs/critical/critical-001.log` | `critical` | `database_unavailable` | `true` |
| `mixed-001` | `fixtures/health-logs/mixed/mixed-001.log` | `critical` | `redis_service_failed` | `true` |

Ground truth completo em cada `*.expected.json`. Não editar fixtures já usados em benchmark sem registrar a mudança.

## 8. Validação automática por caso

O script verifica automaticamente os seguintes campos por run:

| Campo | Comparação |
|-------|------------|
| `severity_match` | `response.severity == expected.severity_expected` |
| `primary_issue_match` | `response.primary_issue == expected.primary_issue` |
| `secondary_issues_match` | `set(response.secondary_issues) == set(expected.secondary_issues)` (ordem não importa) |
| `requires_action_match` | `response.requires_action == expected.requires_action` |
| `host_match` | `response.host == expected.host` |
| `timestamp_match` | `response.timestamp == expected.timestamp` |
| `summary_present` | `isinstance(summary, str) and 20 <= len(summary) <= 300` |

`matches_total` = soma dos bool acima.

### class_acc_auto

| Condição | Nota |
|----------|------|
| `severity_match AND primary_issue_match AND requires_action_match` | 4 |
| `severity_match AND primary_issue_match` | 3 |
| Apenas `severity_match` | 2 |
| `severity_match = False` | 0 |

### parse_acc_auto

| Condição | Nota |
|----------|------|
| `primary_issue_match AND secondary_issues_match AND host_match` | 4 |
| `primary_issue_match` (secondary ou host incorretos) | 3 |
| `json_valid AND NOT primary_issue_match` | 2 |
| `json_valid = False` | 0 |

## 9. Métricas específicas de S3

Aplicam-se em conjunto com as métricas base do ADR-0001 (CON, TOOL-CON, INST, TOOL-ACC, STAB).

### CLASS-ACC (classificação de severidade)

| Nota | Critério |
|------|----------|
| 4 | Severidade bate com expected em todos os K runs |
| 3 | Bate na maioria dos runs |
| 2 | Bate em menos da metade dos runs |
| 0 | Nunca bate |

### PARSE-ACC (extração de campos)

| Nota | Critério |
|------|----------|
| 4 | `primary_issue`, `secondary_issues` e `host` corretos em todos os K runs |
| 3 | `primary_issue` correto mas `secondary_issues` incompletos |
| 2 | Campos parcialmente corretos |
| 0 | Extração falha ou incorreta sistematicamente |

### SUMMARY-QUAL (qualidade do resumo)

Avaliação sempre manual. Não é calculada automaticamente.

| Nota | Critério |
|------|----------|
| 4 | Resumo preciso, em português, menciona o `primary_issue` e contexto |
| 3 | Resumo presente e compreensível mas com imprecisão menor |
| 2 | Resumo genérico ou incompleto |
| 1 | Resumo em idioma errado ou sem relação com o log |
| 0 | Campo ausente ou vazio |

## 10. Checklist de aderência a instruções (INST — S3)

Para cada run, verificar:

- [ ] O modelo chamou `read_file` (não `run_bash`, não tool inventada).
- [ ] O argumento `path` corresponde ao caminho do fixture fornecido no prompt.
- [ ] A resposta final é JSON puro, sem markdown, sem texto adicional.
- [ ] O campo `severity` usa exatamente um dos valores permitidos: `info`, `warning`, `critical`.
- [ ] O campo `summary` está em português do Brasil.
- [ ] Nenhum campo obrigatório está ausente.

## 11. Registro de resultados (summary)

Arquivo: `results/benchmarks/S3-{modelo_safe}-{data}-summary.md`

Notas por dimensão a preencher manualmente após leitura dos 4 arquivos de run:

- **CON**: _preencher após leitura dos 4 runs_
- **TOOL-CON**: _preencher após leitura dos 4 runs_
- **INST**: _preencher após leitura dos 4 runs_
- **TOOL-ACC**: _preencher após leitura dos 4 runs_
- **CLASS-ACC** (agregado): _preencher — derivar de class_acc_auto por case_
- **PARSE-ACC** (agregado): _preencher — derivar de parse_acc_auto por case_
- **SUMMARY-QUAL** (agregado): _avaliação manual sempre_
- **STAB**: n/a — aguardar Bateria 2 (mínimo 12h em sessão separada)

---

_Referências: `docs/decisions/ADR-0001-criterios-de-avaliacao.md`, `docs/benchmarks/evaluation-framework.md`_

_Gerado em: 2026-04-24_
