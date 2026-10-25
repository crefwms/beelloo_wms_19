# Arquitetura de Logística Reversa no Odoo 17 — CD Guarulhos

## Diagnóstico rápido

Antes de propor a estrutura, duas perguntas que mudam a arquitetura:
- Qual o volume de devoluções por mês (unidades)?
- Os produtos têm número de série (eletrônicos, eletrodomésticos)?

Assumindo operação de médio volume com produtos serializados, aqui está a arquitetura recomendada.

---

## Locações obrigatórias no Odoo 17

Crie as seguintes locações em **Inventário > Configuração > Locações**, todas como filhas de um nó pai `REVERSA` separado do estoque regular:

| Locação | Tipo | Função |
|---|---|---|
| `QUARENTENA-REVERSA` | Interno | Produto recebido, ainda não inspecionado |
| `TRIAGEM-TECNICA` | Interno | Em processo de grading pelo técnico |
| `INSPECAO` | Interno | Aguardando decisão ou análise de fraude |
| `RECONDICIONAMENTO` | Interno | Em reparo/limpeza para B-Grade |
| `ESTOQUE-OUTLET` | Interno | B-Grade aprovado para venda |
| `DESCARTE` | Interno | C-Grade aguardando destinação final |
| `BLOQUEADO-FRAUDE` | Interno | Item retido por suspeita, aguardando jurídico |

**Criação no Odoo:**
```
Inventário > Configuração > Locações
→ Nova locação pai: "LOGISTICA-REVERSA" (tipo: Interno)
→ Criar cada sublocation acima como filha
→ NUNCA criar como filha do local de estoque regular
```

---

## Regra crítica de segregação

Crie um status intermediário `RETORNO-PENDENTE-VALIDACAO` antes da reintegração ao estoque regular. **Nenhum produto devolvido volta ao estoque sem passar por esse status.** Isso evita que A-Grade não validado tecnicamente entre na disponibilidade de venda.

Fluxo de reintegração:
```
TRIAGEM-TECNICA → [grading A-Grade] → RETORNO-PENDENTE-VALIDACAO → [validação supervisor] → Estoque Regular
```

---

## Fluxo operacional completo

```
1. CHEGADA
   → Scan da etiqueta reversa na doca
   → WMS cria transferência: Cliente → QUARENTENA-REVERSA
   → Registro fotográfico + peso bruto

2. INSPEÇÃO DE SAFETY (antes de abrir)
   → Checklist: embalagem danificada? bateria? líquido? odor?
   → Se risco: mover para INSPECAO com flag de segurança

3. TRIAGEM TÉCNICA
   → Mover para TRIAGEM-TECNICA
   → Conferência: serial vs. pedido original, pesagem, fotos
   → Grading: A / B / C

4. DECISÃO DE DESTINO
   → A-Grade → RETORNO-PENDENTE-VALIDACAO → Estoque Regular
   → B-Grade → RECONDICIONAMENTO → ESTOQUE-OUTLET
   → C-Grade → DESCARTE
   → Fraude confirmada → BLOQUEADO-FRAUDE

5. EVENTO FINANCEIRO
   → A-Grade validado: liberar estorno 100%
   → B-Grade: liberar estorno parcial (conforme política)
   → C-Grade com defeito de fábrica: acionar garantia fornecedor
   → Fraude: bloquear crédito
```

---

## Configurações no Odoo 17

### Picking Types dedicados

Crie em **Inventário > Configuração > Tipos de Operação**:

| Nome | Origem padrão | Destino padrão |
|---|---|---|
| `Recebimento Devolução` | Clientes | QUARENTENA-REVERSA |
| `Triagem LR` | QUARENTENA-REVERSA | TRIAGEM-TECNICA |
| `Classificação LR` | TRIAGEM-TECNICA | (definido na triagem) |
| `Reintegração Estoque` | RETORNO-PENDENTE-VALIDACAO | Estoque Regular |
| `Baixa LR` | DESCARTE | Virtual/Perdas |

### Rastreamento por número de série
- Ative `Rastreamento: Por Número de Série` no produto
- Ao receber a devolução, leia o serial e valide contra o pedido original
- Prefixo recomendado para lotes de devolução: `DEV-AAAAMM-NNNNN`

### Controle de acesso
- Apenas `Gerente de Logística Reversa` executa o picking type `Reintegração Estoque`
- Operadores de triagem operam apenas `Triagem LR` e `Classificação LR`

### Automações (Odoo Automated Actions)
- Alerta: produto em `QUARENTENA-REVERSA` há mais de 24h sem movimentação → notificação supervisor
- Alerta: produto em `INSPECAO` há mais de 48h → escalonamento automático
- Trigger: conclusão de `Reintegração Estoque` → disparar evento de estorno no financeiro

---

## Separação física no CD

O sistema resolve a segregação lógica. A física precisa da sua atenção:

- Demarcação de área com fita ou gradis — separado da área de picking de pedidos novos
- Câmera na bancada de triagem (essencial para evidência em disputas)
- Prateleiras exclusivas com etiquetas coloridas:
  - 🔴 Vermelho: quarentena / triagem
  - 🟡 Amarelo: recondicionamento / inspeção
  - 🟢 Verde: aprovado aguardando reintegração
  - ⚫ Cinza: descarte

---

## KPIs que você deve monitorar desde o dia 1

| KPI | Meta inicial |
|---|---|
| Dock-to-Stock (A-Grade) | < 48h |
| Tempo médio em quarentena | < 24h |
| % reclassificações após grading | < 2% |
| Itens parados > 5 dias na reversa | 0 |

---

## Checklist de implantação

- [ ] Criar estrutura de locações no Odoo separada do estoque regular
- [ ] Configurar picking types dedicados para cada etapa
- [ ] Ativar rastreamento por serial nos SKUs relevantes
- [ ] Configurar grupos de acesso por perfil
- [ ] Configurar automações de alerta para itens parados
- [ ] Delimitar fisicamente a área no CD
- [ ] Treinar equipe no fluxo e nos critérios de grading
- [ ] Definir SLA por etapa e monitorar semanalmente
