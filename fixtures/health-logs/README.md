# Health Logs Fixtures

## Objetivo

Esta pasta contém fixtures sintéticas para benchmark de modelos locais em tarefas de:

- classificação de severidade;
- resumo operacional;
- geração de JSON estruturado;
- comparação entre prompts e modelos.

## Estrutura

```text
fixtures/health-logs/
  info/
  warning/
  critical/
  mixed/
```

## Convenção

Cada caso possui:

- um arquivo `.log` com o input bruto;
- um arquivo `.expected.json` com o ground truth esperado.

Exemplo:

```text
warning/warning-001.log
warning/warning-001.expected.json
```

## Regras

- Não editar fixtures já usadas em benchmark sem registrar a mudança.
- Se um caso precisar ser corrigido, criar nova versão ou novo identificador.
- O conteúdo deve ser sintético, mas plausível para ambiente Linux/servidor.
- O ground truth deve refletir a interpretação operacional esperada, não apenas o formato.

## Convenções de campos

### `case_id`

- Deve ser exatamente o nome do arquivo `.log` sem extensão.
- Exemplo:
  - `warning-001.log` → `"case_id": "warning-001"`

### `primary_issue`

- Deve usar apenas labels do vocabulário controlado.
- Não usar frase livre.

### `secondary_issues`

- Deve ser uma lista de labels do vocabulário controlado.

## Vocabulário controlado

Os únicos labels permitidos são:

- `none`
- `high_cpu_usage`
- `elevated_application_latency`
- `database_unavailable`
- `disk_critical_on_var`
- `postgresql_service_failed`
- `redis_service_failed`
- `backup_volume_high_usage`
- `session_api_error_rate_elevated`

## Campos esperados no `.expected.json`

- `case_id`
- `severity_expected`
- `primary_issue`
- `secondary_issues`
- `host`
- `timestamp`
- `requires_action`
- `expected_summary`

## Casos iniciais

- `info/info-001`
- `warning/warning-001`
- `critical/critical-001`
- `mixed/mixed-001`
