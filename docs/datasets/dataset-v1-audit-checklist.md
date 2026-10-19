# Dataset v1 Audit Checklist

## Objetivo

Revisar a coerência semântica e estrutural do dataset sintético `fixtures/health-logs/` antes da execução dos benchmarks.

## Escopo

Aplicar esta checklist aos 12 casos iniciais:

- info-001
- info-002
- info-003
- warning-001
- warning-002
- warning-003
- critical-001
- critical-002
- critical-003
- mixed-001
- mixed-002
- mixed-003

## Critérios de revisão por caso

Para cada caso, verificar:

### 1. Estrutura

- [ ] Existe `.log`
- [ ] Existe `.expected.json`
- [ ] `case_id` corresponde ao nome do arquivo
- [ ] Todos os campos obrigatórios existem
- [ ] JSON está válido

### 2. Vocabulário controlado

- [ ] `primary_issue` usa um label permitido
- [ ] `secondary_issues` usam apenas labels permitidos
- [ ] Não há frases livres nos campos categóricos

## Labels permitidos

- `none`
- `high_cpu_usage`
- `elevated_application_latency`
- `database_unavailable`
- `disk_critical_on_var`
- `postgresql_service_failed`
- `redis_service_failed`
- `backup_volume_high_usage`
- `session_api_error_rate_elevated`

### 3. Coerência semântica

- [ ] A severidade esperada condiz com o log
- [ ] O `primary_issue` representa o principal problema do caso
- [ ] Os `secondary_issues` realmente aparecem no log
- [ ] O `expected_summary` reflete o caso corretamente
- [ ] `requires_action` condiz com o impacto observado

### 4. Coerência benchmark

- [ ] O caso ajuda a diferenciar modelos
- [ ] O caso não é trivial demais
- [ ] O caso não é ambíguo sem necessidade
- [ ] O caso não conflita com as próprias guidelines do dataset

## Tabela de auditoria

| Caso | Estrutura | Vocabulário | Semântica | Observações | Ação |
|------|-----------|-------------|-----------|-------------|------|
| info-001 | pendente | pendente | pendente |  | manter |
| info-002 | pendente | pendente | pendente |  | revisar |
| info-003 | pendente | pendente | pendente |  | manter |
| warning-001 | pendente | pendente | pendente |  | manter |
| warning-002 | pendente | pendente | pendente |  | revisar |
| warning-003 | pendente | pendente | pendente |  | manter |
| critical-001 | pendente | pendente | pendente |  | manter |
| critical-002 | pendente | pendente | pendente |  | manter |
| critical-003 | pendente | pendente | pendente |  | manter |
| mixed-001 | pendente | pendente | pendente |  | manter |
| mixed-002 | pendente | pendente | pendente |  | manter |
| mixed-003 | pendente | pendente | pendente |  | manter |

## Foco inicial

Priorizar revisão manual dos casos com maior chance de inconsistência:

- `info-002`
- `warning-002`

## Regra de decisão

Ao final da revisão, cada caso deve cair em uma destas ações:

- `manter`
- `ajustar`
- `substituir`

## Critério para congelar v1

O dataset v1 só deve ser considerado congelado quando:

- todos os 12 casos tiverem sido revisados;
- não houver conflito entre severidade e `primary_issue`;
- não houver labels fora do vocabulário controlado;
- não houver sumários incoerentes com o log e com o ground truth.
