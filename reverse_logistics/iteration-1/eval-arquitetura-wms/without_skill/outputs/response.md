# Logística Reversa no CD de Guarulhos com Odoo 17

## 1. Locações a Criar no Odoo 17

No Odoo 17, as locações são configuradas em **Inventário > Configuração > Locações**. Para logística reversa, você precisará das seguintes locações, todas filhas de um local pai dedicado:

### Estrutura de Locações Recomendada

```
CD Guarulhos (Virtual/Pai)
├── ESTOQUE REGULAR (Interno)
│   ├── Picking
│   ├── Packing
│   └── Expedição
└── LOGÍSTICA REVERSA (Interno)
    ├── LR-RECEBIMENTO        → Doca de entrada exclusiva para devoluções
    ├── LR-TRIAGEM            → Onde o produto é inspecionado e classificado
    ├── LR-APROVADO           → Produto avaliado como BOM, apto para retornar ao estoque
    ├── LR-REFURBISH          → Produto que precisa de recondicionamento/manutenção
    ├── LR-QUARENTENA         → Produto aguardando decisão ou laudo técnico
    ├── LR-DESCARTE           → Produto sem condição de retorno ou revenda
    └── LR-FORNECEDOR         → Produto a ser devolvido ao fornecedor
```

> **Regra fundamental**: Nenhuma dessas locações de LR deve ser filha de "Estoque Regular". Isso garante separação física e sistêmica.

---

## 2. Fluxo Operacional de Logística Reversa

### Etapa 1 — Recebimento da Devolução

1. O operador recebe o pedido de devolução (RMA) criado pelo setor comercial ou atendimento.
2. No Odoo, abre-se uma **Transferência de Recebimento** com origem externa (cliente) e destino `LR-RECEBIMENTO`.
3. A mercadoria entra fisicamente pela **doca exclusiva de devolução** (separada da doca de recebimento de fornecedores).
4. O produto é bipado/contado e a transferência é validada no sistema.

### Etapa 2 — Triagem e Inspeção

1. O produto é movido de `LR-RECEBIMENTO` para `LR-TRIAGEM` via transferência interna.
2. O técnico/operador de triagem realiza inspeção física e registra o resultado em um campo personalizado.
3. Com base no resultado, o produto é direcionado para uma das locações de destino.

### Etapa 3 — Classificação e Destinação

| Resultado da Triagem | Locação de Destino | Ação no Odoo |
|---|---|---|
| Produto sem avaria, lacrado | LR-APROVADO | Transferência interna para LR-APROVADO, depois reintegração ao estoque regular |
| Produto com defeito recuperável | LR-REFURBISH | Transferência para LR-REFURBISH + ordem de manutenção |
| Produto com suspeita/laudo pendente | LR-QUARENTENA | Transferência para LR-QUARENTENA + nota interna |
| Produto irrecuperável | LR-DESCARTE | Transferência para LR-DESCARTE + baixa (scrap) |
| Defeito de fabricação | LR-FORNECEDOR | Transferência para LR-FORNECEDOR + RMA ao fornecedor |

### Etapa 4 — Reintegração ao Estoque (quando aprovado)

1. Produto em `LR-APROVADO` é transferido para a locação correta do Estoque Regular.
2. Obrigatório verificar lote/série e data de validade antes da reintegração.
3. A transferência deve exigir confirmação de supervisor (validação em dois passos).

---

## 3. Como Evitar Mistura com Estoque Novo

### 3.1 Separação por Locação (Controle Sistêmico)

- Nunca configure as locações de LR como sublocações do estoque regular.
- Desative o flag **"Reservar Estoque"** nas locações LR para que não entrem nos cálculos de disponibilidade de venda.

### 3.2 Separação por Lote/Número de Série

- Ative rastreamento por lote ou número de série para os produtos que passam por devolução.
- Ao receber a devolução, crie um novo lote com prefixo identificador (ex.: `DEV-2024-XXXXX`).

### 3.3 Sinalização Física no CD

- Use etiquetas coloridas: vermelha para triagem, amarela para quarentena, verde para aprovado.
- Delimite fisicamente a área de LR com fita zebrada ou gradis.
- Use prateleiras/porta-paletes exclusivos para LR.

### 3.4 Regras de Rotas e Operações no Odoo

- Crie tipos de operação exclusivos para LR (ex.: "Recebimento Devolução", "Transferência Triagem LR", "Reintegração Estoque").
- Use regras de roteamento para que movimentações de devoluções nunca tenham como destino direto o estoque regular.

### 3.5 Controle de Acesso

- Restrinja via grupos de usuário quem pode executar a transferência de `LR-APROVADO → Estoque Regular`.
- Apenas supervisores ou responsável pela qualidade devem ter essa permissão.

### 3.6 Relatórios e Rastreabilidade

- Configure alertas automáticos (automações do Odoo) para notificar o supervisor quando um produto permanecer em LR-QUARENTENA por mais de X dias sem movimentação.

---

## 4. Checklist de Implantação

- [ ] Criar estrutura de locações LR no Odoo (separada do estoque regular)
- [ ] Desativar flag de reserva de estoque nas locações LR
- [ ] Ativar rastreamento por lote/série nos SKUs relevantes
- [ ] Criar tipos de operação exclusivos para cada etapa do fluxo LR
- [ ] Configurar grupos de acesso por perfil de usuário
- [ ] Delimitar fisicamente a área no CD com sinalização
- [ ] Treinar operadores no fluxo e nas regras de triagem
- [ ] Definir SLA por categoria (triagem em até 24h, quarentena máx. 5 dias úteis)
- [ ] Configurar automações/alertas para itens parados em quarentena
- [ ] Documentar o procedimento operacional padrão (POP) para a equipe

---

## 5. Resumo dos Pontos Críticos

1. **Separação física + sistêmica**: a locação LR deve ser completamente independente do estoque regular no Odoo e no layout do CD.
2. **Fluxo obrigatório de triagem**: nenhum produto devolvido vai direto para o estoque — sempre passa por `LR-RECEBIMENTO` e `LR-TRIAGEM` antes de qualquer decisão.
3. **Rastreabilidade por lote**: o prefixo de lote diferenciado permite identificar a origem do produto em qualquer ponto da cadeia.
4. **Aprovação humana na reintegração**: o retorno ao estoque regular deve ser uma ação deliberada e controlada, não automática.
5. **Gestão de SLA**: produtos parados em quarentena ou triagem geram custo e risco; defina prazos e monitore ativamente.
