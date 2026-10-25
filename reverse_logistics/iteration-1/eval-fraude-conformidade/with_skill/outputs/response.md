# Arquitetura de Controles Anti-Fraude para Logística Reversa — E-commerce de Eletrônicos

## Diagnóstico

**Contexto operacional:**
- Volume: 1.800 pedidos/mês → ~126 devoluções/mês (7%)
- Canais: Mercado Livre + Amazon
- Categoria: Eletrônicos (alto valor, alto risco de fraude)
- Dor principal: **fraude de troca de produto** — item devolvido não é o item que saiu

Com 126 devoluções/mês em eletrônicos, e a ocorrência confirmada de troca por produto diferente (caixa de notebook com tijolo), o problema não é de processo logístico genérico — é de **ausência de cadeia de custódia com evidências**. Cada devolução aceita sem rastreabilidade é uma porta aberta para perda direta.

Esse cenário tem três causas estruturais:
1. Nenhum registro do estado do produto no momento da coleta
2. Nenhuma validação do item recebido contra o item que saiu
3. Nenhum histórico de comportamento por cliente para identificar padrão

---

## Prioridade absoluta: Controle de Conformidade Item Retirado vs. Item Recebido

### O que registrar no momento da COLETA

| Dado | Como coletar | Obrigatório para eletrônicos |
|---|---|---|
| Fotografia da embalagem fechada | App do entregador ou portal web | Sim |
| Fotografia do produto aberto (antes de lacrá-lo) | App do entregador ou portal web | Sim |
| Fotografia do número de série / IMEI | Zoom no serial do produto | Sim |
| Pesagem bruta com embalagem | Balança no ponto de drop-off ou pelo entregador | Sim |
| Número do lacre colocado na embalagem | Foto do lacre após colocação | Sim |

Para o caso específico de caixa de notebook: o peso de um notebook de 15" é tipicamente 1,8–2,5 kg. Uma caixa com tijolo pesa diferente — esse controle sozinho já captura a fraude na origem.

### O que validar no RECEBIMENTO no CD

```
1. Scan da etiqueta reversa → entrada em QUARENTENA-REVERSA no WMS
2. Foto do volume recebido → comparar com foto da coleta
3. Verificar integridade do lacre → número confere com o registrado na coleta?
4. Pesagem bruta → desvio > 5% do peso registrado na coleta = ALERTA IMEDIATO
5. Abertura da embalagem com câmera ativa → registro em vídeo ou foto
6. Leitura do serial / IMEI → validar contra:
   a. Pedido original (NF-e de saída)
   b. Base do fabricante (se disponível via API)
7. Conferência de acessórios obrigatórios (carregador, caixa interna, manual)
```

**Regra crítica:** Nenhum crédito é liberado antes da conferência de serial. Zero exceções.

---

## Fluxo Completo de Controle Anti-Fraude

### Etapa 1 — Portal de Abertura da Solicitação

Motor de regras automático — bloqueios imediatos:

| Condição | Ação |
|---|---|
| Serial informado não consta no pedido | Bloquear e escalar para análise manual |
| Cliente com > 2 devoluções nos últimos 90 dias | Flag de risco + exigir foto adicional |
| Prazo de arrependimento expirado | Bloquear automaticamente |
| Ticket > R$ 800 | Coleta domiciliar obrigatória com entregador treinado |

### Etapa 2 — Coleta com Registro de Custódia

Para eletrônicos, nunca aceitar drop-off sem pesagem. A malha de coleta deve operar com:
- Entregador com app que fotografa e registra peso antes de lacrar
- Lacre numerado colocado pelo entregador na presença do cliente
- Comprovante de coleta com hash de evidências (foto + peso + serial + número do lacre)

### Etapa 3 — Recebimento e Triagem no CD

```
Produto chega
  → scan da etiqueta reversa
  → entrada em QUARENTENA-REVERSA
  → conferência de lacre (número bate?)
      → não bate: BLOQUEADO-FRAUDE, foto, acionar investigação
      → sim: pesagem
          → desvio > 5%: BLOQUEADO-FRAUDE, foto, acionar investigação
          → dentro da faixa: abrir embalagem com câmera
              → leitura de serial
                  → serial não bate com pedido: BLOQUEADO-FRAUDE
                  → serial bate: grading técnico
```

### Etapa 4 — Grading e Destino

| Classificação | Critério | Destino | Crédito |
|---|---|---|---|
| A-Grade | Produto idêntico, serial confere, sem uso aparente | Retorno ao estoque | 100% |
| B-Grade | Produto correto, com uso ou embalagem danificada | Canal outlet / recondicionado | Parcial |
| C-Grade | Defeito técnico confirmado | Acionamento de garantia do fabricante | Depende da cobertura |
| Fraude confirmada | Item diferente, serial adulterado, peso divergente | BLOQUEADO-FRAUDE, contestação no marketplace | Bloqueado |

### Etapa 5 — Contestação no Marketplace

**Mercado Livre:** Abrir disputa formal com evidências fotográficas e laudos. Prazo: contestar dentro de 5 dias úteis. Evidências aceitas: fotos com timestamp, vídeo da abertura, laudo técnico, nota fiscal original.

**Amazon:** Safe-T Claim (Seller Assurance for E-Commerce Transactions). Prazo: até 60 dias após o reembolso. Evidências: fotos da embalagem recebida, serial, peso, vídeo da abertura.

---

## Infraestrutura de Evidências

### Câmeras na área de triagem
- Câmera fixa apontada para a bancada de abertura de embalagens
- Retenção mínima de 90 dias de gravação
- Associação do vídeo ao número do pedido

### Armazenamento de evidências fotográficas
Cada devolução de eletrônico deve ter pasta de evidências com:
- Foto da coleta (embalagem, serial, lacre)
- Foto do recebimento (estado do volume, lacre)
- Foto da abertura (estado do produto)
- Foto do serial lido na triagem
- Resultado da pesagem (antes e depois)
- Retenção: mínimo 180 dias

---

## Políticas de Cliente por Histórico

| Nível | Critério | Restrição |
|---|---|---|
| Verde | 0–1 devolução em 6 meses | Fluxo padrão |
| Amarelo | 2–3 devoluções em 90 dias | Coleta domiciliar obrigatória + foto prévia |
| Vermelho | > 3 devoluções em 90 dias ou 1 fraude confirmada | Bloqueio automático, revisão manual |

---

## KPIs que você deve acompanhar agora

| KPI | Meta 90 dias |
|---|---|
| Taxa de devolução | < 5% (com bloqueio de fraudes) |
| Fraud Rate | Medir e < 2% |
| Recovery rate em eletrônicos | > 65% |
| % devoluções com evidência fotográfica completa | 100% em 30 dias |
| Contestações bem-sucedidas no marketplace | > 60% das fraudes detectadas |

---

## Roadmap de Implementação

**Semana 1–2 (quick wins sem sistema)**
- Formulário de coleta obrigatório com campos de foto, peso e serial
- Câmera na bancada de triagem do CD
- Planilha de registro de conferência para todas as devoluções de eletrônicos
- Definir peso padrão de cada SKU — base para comparação

**Semana 3–4**
- Configurar locações no WMS: QUARENTENA-REVERSA, BLOQUEADO-FRAUDE, INSPECAO
- Regra de bloqueio no portal para serial não casado com pedido
- Flag de risco no cadastro de clientes com > 2 devoluções em 90 dias

**Mês 2**
- Motor de regras integrado com histórico de devoluções por CPF
- Alerta automático de desvio de peso no recebimento
- Validação de serial contra base de NF-e de saída
- Dashboard de fraudes detectadas por canal
