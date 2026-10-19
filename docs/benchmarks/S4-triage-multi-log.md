# S4 — Triagem de múltiplos logs e decisão de escalonamento

**Nível:** 4  
**Cenário ID:** S4  
**Pré-requisito:** S3 aprovado (CLASS-ACC ≥ 3 nos 4 casos)

---

## 1. Objetivo

Avaliar a capacidade do agente de:

1. Executar **3 chamadas encadeadas** de `read_file` (uma por log) sem instrução explícita de ordem
2. **Classificar individualmente** cada host usando o mesmo vocabulário de S3
3. **Ordenar por prioridade** (critical > warning > info; desempate por primary_issue e secondaries)
4. **Gerar um JSON de triagem** estruturado com rank, escalation e resumo por host

S4 é a primeira avaliação de **planejamento multi-step autônomo**: o agente deve decidir sozinho que precisa ler 3 arquivos antes de produzir a saída.

---

## 2. Ferramenta disponível

Idêntica ao S3: apenas `read_file`.

```json
{
  "type": "function",
  "function": {
    "name": "read_file",
    "description": "Lê um arquivo local e retorna seu conteúdo como string.",
    "parameters": {
      "type": "object",
      "properties": {
        "path": {
          "type": "string",
          "description": "Caminho absoluto do arquivo a ser lido."
        }
      },
      "required": ["path"]
    }
  }
}
```

---

## 3. Schema de saída (fixo, obrigatório)

```json
{
  "triage_id": "<identificador do caso S4, ex: S4-A>",
  "hosts_analisados": 3,
  "timestamp_triage": "<ISO 8601 com Z do log mais recente entre os 3>",
  "prioridade": [
    {
      "rank": 1,
      "host": "<hostname>",
      "case_id": "<nome do arquivo sem extensão>",
      "severity": "<info|warning|critical>",
      "primary_issue": "<snake_case do vocabulário controlado>",
      "escalation": "<immediate|monitor|none>",
      "summary": "<1 frase em PT-BR>"
    },
    { "rank": 2, "..." : "..." },
    { "rank": 3, "..." : "..." }
  ],
  "acao_geral": "<frase curta em PT-BR descrevendo a prioridade operacional do conjunto>"
}
```

### 3.1 Regras de escalation

| Severity  | Escalation  |
|-----------|-------------|
| critical  | immediate   |
| warning   | monitor     |
| info      | none        |

### 3.2 Vocabulário controlado (idêntico ao S3)

```
none  high_cpu_usage  elevated_application_latency  database_unavailable
disk_critical_on_var  postgresql_service_failed  redis_service_failed
backup_volume_high_usage  session_api_error_rate_elevated
```

### 3.3 Regras de ordenação por prioridade

1. **Severidade** (peso maior): critical > warning > info
2. **Desempate entre mesma severidade — primary_issue** (peso menor):
   - `disk_critical_on_var` com secondaries de infra (postgresql, database) > qualquer redis
   - `redis_service_failed` + secondary infra crítica > `redis_service_failed` + secondaries de aplicação
   - `high_cpu_usage` / `elevated_application_latency` < redis/disk
3. **Desempate final — recência** (apenas se primary_issue igual): timestamp mais recente = rank mais alto

---

## 4. Prompt template (S4)

```
Você é um agente de triagem de infraestrutura. Analise os 3 arquivos de log a seguir.

Arquivos para análise:
1. {log_path_1}
2. {log_path_2}
3. {log_path_3}

Use a tool read_file para ler cada arquivo. Em seguida:
- Classifique a severidade de cada host (info/warning/critical)
  - critical: qualquer linha com level=CRITICAL
  - warning: nenhuma CRITICAL, mas pelo menos uma WARNING
  - info: todas as linhas são INFO
- Ordene os 3 hosts por prioridade: critical > warning > info
  (em empate de severidade, priorize pelo primary_issue mais grave)
- Gere o JSON de triagem com o schema abaixo.

Identificadores snake_case válidos para primary_issue e secondary_issues:
  none, high_cpu_usage, elevated_application_latency, database_unavailable,
  disk_critical_on_var, postgresql_service_failed, redis_service_failed,
  backup_volume_high_usage, session_api_error_rate_elevated

Schema de saída:
{
  "triage_id": "{triage_id}",
  "hosts_analisados": 3,
  "timestamp_triage": "<ISO 8601 com Z do log mais recente entre os 3>",
  "prioridade": [
    {
      "rank": 1,
      "host": "<hostname>",
      "case_id": "<nome do arquivo sem extensão>",
      "severity": "<info|warning|critical>",
      "primary_issue": "<snake_case>",
      "escalation": "<immediate|monitor|none>",
      "summary": "<1 frase em PT-BR>"
    },
    {"rank": 2, "...": "..."},
    {"rank": 3, "...": "..."}
  ],
  "acao_geral": "<frase curta em PT-BR>"
}

Regras de escalation: critical → immediate | warning → monitor | info → none

Responda APENAS com o JSON. Sem markdown. Sem texto adicional.
```

---

## 5. Casos de teste

### S4-A — Uma de cada severidade

| Slot | Fixture     | Host         | Severity | Primary Issue        |
|------|-------------|--------------|----------|----------------------|
| 1    | info-001    | fox-node-01  | info     | none                 |
| 2    | warning-001 | fox-node-02  | warning  | high_cpu_usage       |
| 3    | critical-001| fox-node-03  | critical | disk_critical_on_var |

**Ordem esperada:** critical-001 → warning-001 → info-001  
**timestamp_triage:** `2026-04-24T16:44:25Z` (critical-001, mais recente)  
**Objetivo:** Verificar ordenação básica quando há uma de cada severidade.

---

### S4-B — Três críticos (desempate por primary_issue)

| Slot | Fixture      | Host         | Severity | Primary Issue        | Secondary Issues                          |
|------|--------------|--------------|----------|----------------------|-------------------------------------------|
| 1    | critical-001 | fox-node-03  | critical | disk_critical_on_var | postgresql_service_failed, database_unavailable |
| 2    | critical-003 | fox-node-10  | critical | redis_service_failed | disk_critical_on_var                      |
| 3    | mixed-001    | fox-node-04  | critical | redis_service_failed | backup_volume_high_usage, session_api_error_rate_elevated |

**Ordem esperada:** critical-001 → critical-003 → mixed-001  
**Critério de desempate:**
- critical-001: `disk_critical_on_var` primary com cascata de infra (PostgreSQL + DB) = raiz de maior impacto
- critical-003: `redis_service_failed` + `disk_critical_on_var` secondary = dois problemas de infra simultâneos
- mixed-001: `redis_service_failed` + secondaries de camada de aplicação (menos críticos)

**timestamp_triage:** `2026-04-24T18:07:49Z` (critical-003, mais recente)  
**Objetivo:** Verificar capacidade de desempate quando todos são critical; discrimina raciocínio sobre gravidade relativa dos issues.

---

### S4-C — Sem críticos (warning + dois infos)

| Slot | Fixture     | Host         | Severity | Primary Issue                  | Timestamp            |
|------|-------------|--------------|----------|--------------------------------|----------------------|
| 1    | info-001    | fox-node-01  | info     | none                           | 2026-04-24T14:01:17Z |
| 2    | info-003    | fox-node-06  | info     | none                           | 2026-04-24T10:22:16Z |
| 3    | warning-003 | fox-node-08  | warning  | elevated_application_latency   | 2026-04-24T12:48:09Z |

**Ordem esperada:** warning-003 → info-001 → info-003  
**Critério de desempate (infos):** info-001 mais recente (14:01:17Z) → rank 2; info-003 mais antigo (10:22:16Z) → rank 3  
**timestamp_triage:** `2026-04-24T14:01:17Z` (info-001, mais recente dos 3)  
**Objetivo:** Verificar que o agente posiciona corretamente o warning acima dos infos e ordena os infos por recência.

---

## 6. Ground truth de validação automática

Validações computadas pelo script para cada caso:

| Campo                | Tipo | Critério                                                                 |
|---------------------|------|--------------------------------------------------------------------------|
| `schema_valid`      | bool | JSON válido sem wrapper markdown; contém `triage_id`, `prioridade` (list de 3), `acao_geral` |
| `all_hosts_present` | bool | Os 3 hosts esperados aparecem no JSON (em qualquer posição)              |
| `rank_order_correct`| bool | A sequência de `host` em `prioridade` bate exatamente com `hosts_expected` |
| `escalation_correct`| bool | `escalation` de cada host bate com a severidade esperada (regra: critical→immediate, warning→monitor, info→none) |
| `acao_geral_present`| bool | `acao_geral` existe, é string, len ≥ 10                                  |

---

## 7. Métricas S4

### TRIAGE-ACC (0–4)

| Nota | Critério                                                               |
|------|------------------------------------------------------------------------|
| 4    | `rank_order_correct` + `escalation_correct` + `all_hosts_present` = True nos 3 casos |
| 3    | `escalation_correct` + `all_hosts_present` = True, mas `rank_order_correct` falha em ≤ 1 caso |
| 2    | `all_hosts_present` = True em todos, mas escalation incorreto em ≥ 1 caso |
| 1    | Produz JSON válido, mas hosts faltando ou schema inválido em ≥ 1 caso |
| 0    | Falha em produzir JSON válido em ≥ 1 caso                             |

### CHAIN-ACC (0 ou 4)

| Nota | Critério                                                         |
|------|------------------------------------------------------------------|
| 4    | Número de chamadas `read_file` = 3 em todos os casos            |
| 0    | Qualquer caso com ≠ 3 chamadas `read_file`                      |

Nota: CHAIN-ACC=0 é esperado em modelos que colapsam tool calls em um único turno ou que não chamam todas as ferramentas necessárias.

### INST, CON (0–4)

Idênticos ao S3 — ver `ADR-0001-criterios-de-avaliacao.md`.

- **INST:** JSON puro (sem markdown), `triage_id` correto, `hosts_analisados = 3`, `escalation` válido (vocabulário controlado), `summary` por host em PT-BR, `acao_geral` presente
- **CON:** Consistência interna da triagem (severity ↔ escalation coerentes, rank sem duplicatas, timestamp_triage bate com o log mais recente)

---

## 8. Checklist INST para S4

- [ ] JSON puro — sem ```json ... ``` wrapper
- [ ] `triage_id` preenchido com o identificador do caso (ex: `S4-A`)
- [ ] `hosts_analisados` = 3
- [ ] `prioridade` é lista com exatamente 3 itens, ranks 1/2/3
- [ ] `severity` de cada item: enum `info|warning|critical`
- [ ] `escalation` de cada item: enum `immediate|monitor|none`
- [ ] `primary_issue` de cada item: vocabulário controlado (snake_case)
- [ ] `summary` de cada item: string em PT-BR, 1 frase
- [ ] `timestamp_triage`: ISO 8601 com Z, corresponde ao log mais recente
- [ ] `acao_geral`: string em PT-BR, não vazia

---

## 9. Fluxo de execução esperado (multi-turn)

```
T1: prompt (3 caminhos) → modelo chama read_file(log_1)
T2: conteúdo log_1     → modelo chama read_file(log_2)
T3: conteúdo log_2     → modelo chama read_file(log_3)
T4: conteúdo log_3     → modelo gera JSON de triagem
```

O script suporta até 4 turnos de API por caso (`MAX_TOOL_TURNS = 4`). Modelos que tentem resolver em menos de 3 chamadas (ex: inventando conteúdo dos logs não lidos) terão CHAIN-ACC=0.

---

## 10. Parâmetros de execução

| Parâmetro    | Valor                        |
|-------------|------------------------------|
| Temperatura | 0                            |
| Timeout     | 180s (3 tool calls + tempo extra) |
| K (casos)   | 3 (S4-A, S4-B, S4-C)        |
| Bateria 1   | 1 run por caso (K=3 total)   |
| Bateria 2   | Repetir após ≥ 12h (STAB)   |
| Tool        | `read_file` (leitura direta Python) |

---

## 11. Fixtures utilizadas

Todos os arquivos de log vêm de `fixtures/health-logs/` (gerados em `docs/datasets/synthetic-health-logs.md`).

| Caso  | Fixtures usadas                             |
|-------|---------------------------------------------|
| S4-A  | info-001, warning-001, critical-001         |
| S4-B  | critical-001, critical-003, mixed-001       |
| S4-C  | info-001, info-003, warning-003             |

Expected outputs: `fixtures/triage-s4/S4-{A,B,C}.expected.json`

---

## 12. Próximos passos

- [ ] Executar `scripts/run-s4-benchmark.py <modelo>` para os 3 modelos da shortlist
- [ ] Avaliar INST e CON manualmente para cada run (S4 é mais complexo — leitura cuidadosa)
- [ ] Executar Bateria 2 após ≥ 12h (STAB)
- [ ] Produzir `results/reports/S4-bateria1-relatorio-<data>.md`
- [ ] Atualizar hipóteses H10/H11 com dados de S4 (H11: verificar se T2 thinking ainda ocorre em 14b com 4 turnos)

---

_Documento criado em 2026-04-25. Cenário elaborado com base em S3-log-analysis-classify.md e nos fixtures health-logs existentes._
