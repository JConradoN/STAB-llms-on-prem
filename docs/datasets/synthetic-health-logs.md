# Synthetic Health Logs Dataset

## Objetivo

Definir um conjunto de dados sintéticos para benchmark de modelos locais em tarefas de observabilidade, health check e structured output.

O dataset existe para:

- reduzir dependência de um único `health.sh`;
- garantir cobertura de níveis de alerta relevantes;
- permitir comparação reproduzível entre modelos e prompts;
- separar validação estrutural de acerto semântico.

## Motivação

Um benchmark útil para agentes de observabilidade precisa conter casos controlados e comparáveis.

Logs reais são úteis, mas frequentemente:

- não cobrem todos os padrões desejados;
- mudam ao longo do tempo;
- dificultam comparação justa entre execuções;
- misturam ruído não controlado.

Por isso, este projeto adota fixtures sintéticas como base mínima de avaliação.

## Escopo inicial

O conjunto inicial deve conter 12 casos:

- 3 casos `info`
- 3 casos `warning`
- 3 casos `critical`
- 3 casos `mixed`

## Estrutura de diretórios

```text
fixtures/health-logs/
  info/
  warning/
  critical/
  mixed/
```

## Convenção de nomes

Cada caso deve ter dois arquivos:

- um arquivo `.log` com o log bruto;
- um arquivo `.expected.json` com o ground truth esperado.

Exemplo:

```text
fixtures/health-logs/warning/warning-001.log
fixtures/health-logs/warning/warning-001.expected.json
```

## Convenções de campos

### `case_id`

- Deve ser exatamente o nome do arquivo `.log` sem extensão.
- Exemplo:
  - arquivo: `warning-001.log`
  - `case_id`: `warning-001`

### `primary_issue`

- Deve usar **apenas** um identificador do vocabulário controlado definido neste documento.
- Não usar frases livres.
- Deve representar o problema principal do caso.

### `secondary_issues`

- Deve ser uma lista de identificadores do mesmo vocabulário controlado.
- Não usar frases livres.
- Deve listar apenas problemas secundários relevantes.

## Vocabulário controlado

Os únicos identificadores permitidos para `primary_issue` e `secondary_issues` são:

- `none`
- `high_cpu_usage`
- `elevated_application_latency`
- `database_unavailable`
- `disk_critical_on_var`
- `postgresql_service_failed`
- `redis_service_failed`
- `backup_volume_high_usage`
- `session_api_error_rate_elevated`

## Definições dos labels

### `none`

- Usar quando não houver problema operacional relevante no caso.

### `high_cpu_usage`

- Usar quando o principal sinal de degradação for uso elevado de CPU.

### `elevated_application_latency`

- Usar quando o problema principal ou secundário for aumento perceptível de latência da aplicação.

### `database_unavailable`

- Usar quando o banco estiver indisponível ou inacessível.

### `disk_critical_on_var`

- Usar quando o volume `/var` estiver em nível crítico de ocupação.

### `postgresql_service_failed`

- Usar quando o serviço PostgreSQL estiver falho, parado ou incapaz de iniciar.

### `redis_service_failed`

- Usar quando o serviço Redis estiver indisponível ou falho.

### `backup_volume_high_usage`

- Usar quando o volume de backup estiver com uso elevado, mas não necessariamente em falha crítica.

### `session_api_error_rate_elevated`

- Usar quando a API de sessão apresentar taxa de erro elevada.

## Campos mínimos do ground truth

Cada arquivo `.expected.json` deve conter, no mínimo:

- `case_id`
- `severity_expected`
- `primary_issue`
- `secondary_issues`
- `host`
- `timestamp`
- `requires_action`
- `expected_summary`

## Regras de severidade

### Info

Usar para casos com:

- operação normal;
- eventos informativos;
- ausência de degradação relevante.

### Warning

Usar para casos com:

- degradação moderada;
- risco operacional;
- necessidade de acompanhamento;
- impacto ainda contido.

### Critical

Usar para casos com:

- indisponibilidade;
- falha persistente;
- impacto operacional imediato;
- múltiplos sinais graves.

### Mixed

Usar para casos com:

- múltiplos sinais em severidades diferentes;
- necessidade de priorização do problema principal;
- presença de mais de um evento relevante no mesmo log.

Observação:
- Casos da pasta `mixed/` podem ter `severity_expected` final igual a `warning` ou `critical`, conforme a prioridade operacional do evento principal.

## Requisitos do dataset

Cada fixture deve ser:

- curta o suficiente para leitura rápida;
- rica o suficiente para exigir interpretação;
- consistente com um ambiente Linux/servidor plausível;
- reproduzível;
- livre de dados sensíveis reais.

## O que variar entre os casos

Ao longo do dataset, variar:

- CPU
- disco
- serviços
- banco de dados
- latência
- taxa de erro
- múltiplos alertas
- recuperação parcial
- ruído textual
- timestamps e hosts

## Objetivo de uso

Este dataset será usado para:

- comparar S2 vs S2B;
- comparar modelos locais;
- medir structured output reliability;
- medir aderência ao vocabulário controlado.

## Próximos passos

1. Atualizar e revisar os fixtures existentes.
2. Criar os demais casos do conjunto inicial.
3. Integrar o dataset aos scripts de benchmark.
4. Expandir o conjunto apenas após a primeira rodada de experimentos.
