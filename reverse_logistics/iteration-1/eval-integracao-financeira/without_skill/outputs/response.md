# Mapeamento de Eventos Logísticos para Aceleração do Estorno em Devoluções na Magalu

## Contexto do Problema

Ao vender no Magalu (Magazine Luiza), o prazo de crédito de 15 dias após uma devolução gera insatisfação no cliente, reclamações e queda de reputação do seller. O desafio é **mapear eventos logísticos verificáveis** para antecipar a liberação do estorno sem assumir risco financeiro antes da triagem.

---

## 1. Entendendo o Fluxo Atual de Devolução no Magalu

O processo padrão segue estas etapas:

1. Cliente solicita devolução
2. Aprovação da solicitação
3. Geração de etiqueta de postagem reversa
4. Cliente posta o produto
5. Objeto em trânsito (rastreamento ativo)
6. Recebimento no CD do seller ou do Magalu
7. Triagem/inspeção física
8. Aprovação do estorno pelo seller
9. Processamento do reembolso pelo Magalu

O gargalo está nas etapas 6 a 9.

---

## 2. Mapeamento dos Eventos Logísticos como Gatilhos de Decisão

**Evento 1 - Postagem pelo cliente:** Iniciar comunicação proativa; não liberar crédito.

**Evento 2 - Objeto em trânsito:** Atualizar prazo estimado ao cliente.

**Evento 3 - Objeto entregue no CD:** Evento crítico — iniciar triagem com SLA de 24-48h; para produtos de baixo valor sem histórico de fraude, considerar antecipação do estorno.

**Evento 4 - Triagem aprovada:** Liberar estorno imediatamente via integração com API do Magalu.

**Evento 5 - Triagem recusada:** Iniciar contestação com registro fotográfico como evidência.

---

## 3. Estratégia para Antecipar Sem Assumir Risco

- **Estorno condicional pós-entrega no CD** para produtos abaixo de threshold de valor (ex: R$ 150) com cliente sem histórico de fraude
- **SLA interno de triagem em 24-48h** com check-list padronizado e registro fotográfico obrigatório
- **Integração via API do Magalu** para aprovação automática ao fim da triagem
- **Comunicação proativa por evento** para reduzir reclamações independente do prazo

---

## 4. Matriz de Risco por Evento

| Evento | Ação | Risco | Condição |
|---|---|---|---|
| Solicitação criada | Comunicar início | Nenhum | Sempre |
| Objeto postado | Reservar crédito internamente | Alto | Nunca liberar |
| Em trânsito | Atualizar prazo ao cliente | Alto | Nunca liberar |
| Entregue no CD | Liberar para baixo valor | Baixo | Valor < threshold + sem fraude |
| Triagem aprovada | Liberar estorno | Zero | Sempre |
| Triagem recusada | Contestação documentada | Gerenciado | Com evidência |

---

## 5. Conclusão

Ao transformar o processo de devolução em um **pipeline orientado a eventos**, é possível reduzir o prazo real de 15 para 5-7 dias, reduzir reclamações via comunicação proativa, e antecipar estornos com segurança para produtos de baixo valor — mantendo a triagem como proteção financeira para produtos de maior valor.
