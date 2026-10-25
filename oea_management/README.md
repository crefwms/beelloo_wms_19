# OEA Management

Módulo Odoo 18 para assistência no processo de certificação **OEA (Operador Econômico Autorizado)**.

## Funcionalidades

### Gestão de Requisitos Normativos
- Cadastro de requisitos conforme **IN RFB 1.985/2020**
- Classificação por tipo: Operacional, Documental, Sistêmico, Gerencial
- Modalidades: OEA-Conformidade e OEA-Segurança
- Tracking de complexidade e referência legal
- Importação de requisitos via Trello (JSON)

### Itens de Ação e Evidências
- Workflow completo: Rascunho → Em Andamento → Pendente Revisão → Validado/Rejeitado
- Controle de responsável e datas
- Anexos de evidências
- Vinculação a registros Odoo (picking, lote, funcionário, etc.)
- Hierarquia de itens (sub-itens)
- Aprovação formal com aprobador e data

### Auditorias
- Planejamento de auditorias internas e externas
- Checklist de requisitos por auditoria
- Geração automática de itens de ação
- Acompanhamento de progresso

### SGSI (Sistema de Gestão de Segurança da Informação)
- Gestão de ativos de TI
- Classificação de criticidade
- Registro de riscos com análise de impacto/probabilidade
- Matriz de risco (baixo, médio, alto, crítico)
- Gestão de incidentes de segurança
- Ações de contenção, erradicação e recuperação

### Relatórios
- Conformidade por requisito
- Relatório de auditoria
- Consolidado geral
- Evolução temporal
- Riscos e incidentes

## Instalação

1. Copie o módulo para a pasta `addons` do Odoo
2. Atualize a lista de aplicativos
3. Instale o módulo "OEA Management"

## Configuração

### Grupos de Segurança
- **OEA Manager**: Acesso total (criar, editar, excluir)
- **Usuário**: Acesso de leitura e criação de itens

### Sequências
O módulo cria automaticamente sequências para:
- Código de auditoria (`OEA/AUDIT/YYYY/`)
- Código de incidente (`INC/YYYYMMDDHHMMSS`)

### Atividades Automáticas
- Verificação diária de itens atrasados
- Agendamento automático de revisões

## Uso

### Fluxo de Trabalho de Conformidade

1. **Cadastre os Requisitos**
   - Acesse: `OEA > Requisitos`
   - Cada requisito representa um artigo da IN RFB

2. **Crie Itens de Ação**
   - Acesse: `OEA > Itens de Ação`
   - Vincule ao requisito correspondente
   - Defina responsável e data prevista

3. **Colete Evidências**
   - Adicione anexos aos itens
   - Vincule registros Odoo relevantes

4. **Workflow**
   - `Iniciar` → `Pendente Revisão` → `Validar` ou `Rejeitar`

### Realizando uma Auditoria

1. Crie uma nova auditoria: `OEA > Auditorias > Novo`
2. Adicione os requisitos a verificar
3. Use "Gerar Itens de Ação" para criar automaticamente os itens
4. Acompanhe o progresso

### Gestão de Riscos

1. Cadastre ativos: `OEA > SGSI > Ativos de TI`
2. Registre riscos vinculados aos ativos
3. Defina estratégia de tratamento

### Incidentes de Segurança

1. Registre incidentes: `OEA > SGSI > Incidentes`
2. Acompanhe o ciclo de vida
3. Documente ações tomadas

## Relatórios

Acesse `OEA > Relatórios` para gerar:
- Conformidade por requisito
- Consolidado geral
- Evolução temporal
- Riscos e incidentes

## Integração Trello

Para importar requisitos do Trello:

1. Exporte o board como JSON
2. Acesse: `OEA > Importar do Trello`
3. Carregue o arquivo JSON

## Requisitos do Sistema

- Odoo 18
- Módulos dependentes: `base`, `mail`, `web`, `stock`, `hr`, `product`

## Autor

- **Cassiano Cavalciuk** / Medoo
- Website: https://medoo.dev

## Licença

LGPL-3
