# TEMPLATE — AGENTS.md (Padrão Unificado de Módulo Nexus)
> Versão 2.1 · 25/09/2026 · Laya REAL deployada (NandhaKishorM/laya) · Copie para a raiz de cada módulo como `AGENTS.md`

---

# AGENTE: [Nome do Agente / Microsserviço]
**Módulo:** [ex: nexus-cerebro / buscador / financas-backend]
**Versão do Agente:** 2.0.0
**Porta do Serviço:** [ver tabela oficial abaixo]
**Decisor de Sistema 1:** Laya ✅ (Railway: `http://nexus-decisor-laya.railway.internal:8000/v1/systemone` · dev local: `http://localhost:8000/v1/systemone`)

## 🎯 1. MISSÃO E ESCOPO

- **Objetivo Primário:** [1-2 frases com a função crítica deste agente]
- **Escopo Permitido:** [rotas Express, tabelas PostgreSQL, webhooks autorizados]

**Limites Estritos de Contenção (Anti-Regressão):**
- Nunca reescrever mais de 40 linhas sem validação prévia — apenas diffs cirúrgicos.
- Nunca alterar contratos de rotas existentes sem retrocompatibilidade.
- Toda comunicação inter-serviços pela Railway Private Mesh (`*.railway.internal:PORTA`).

## 🏗️ 2. ARQUITETURA DE 4 CAMADAS (sem sobreposição)

```
Entrada (Telegram | Painel | Webhook | Cron)
  → CAMADA 1 — LAYA (Sistema 1)  [✅ ATIVA — modo sombra no cérebro]
      Triagem ~200-400ms CPU, R$0: precisa LLM? qual destino? qual risco?
      → Não precisa LLM: despacho DIRETO ao membro/setor (após fase sombra)
      → Precisa: segue para Camada 2
  → CAMADA 2 — CÉREBRO (orquestrador) [✅ existe]
      pensarEAgir + tool calling + despacho aos membros
  → CAMADA 3 — OMNIROUTE (maestro de LLM) [✅ existe]
      Rotas auto/* escolhem modelo + chave + provider
  → CAMADA 4 — PROVIDERS [✅ 52+ conexões]
      GLM-5.1 (Modal) · OAuth Google (agy/antigravity/kiro) · OpenRouter · NVIDIA...
```

**Papel de cada camada (não invadir o vizinho):**
- Laya = portão barato (decide SE e PARA ONDE)
- Cérebro = orquestração (COMO executar, tool calling)
- OmniRoute = roteamento de LLM (QUAL modelo e chave)
- Providers = execução final

## 📡 3. PROTOCOLO LAYA (ativo)

- **Endpoint Railway (produção):** `POST http://nexus-decisor-laya.railway.internal:8000/v1/systemone`
- **Endpoint dev local:** `POST http://localhost:8000/v1/systemone`
- **Timeout:** 1.5s com fallback automático para a Camada 2 (cérebro) — falha nunca bloqueia.
- **Primitivas:** `choice` (máx. 15-20 opções) · `score` (níveis descritos) · `noul` (sim/não com probabilidade).
- **Gating:** usar `answer_confidence` (probabilidade calibrada). ≥ 0.88 age direto · < 0.70 valida via `auto/best-fast`.
- **Risco** score 0-2 (normalizar /2): > 0.65 exige confirmação humana ou caminho deliberado.
- **Checkpoint:** multilingual (pt-BR) · CPU ~200-400ms · volume persistente para cache.

### Payload de entrada (contrato futuro):
```json
{
  "state": { "origem": "telegram|painel|webhook|cron", "mensagem": "..." },
  "questions": {
    "destino":     { "type": "choice", "options": ["memoria","sistema","github","mercado_financeiro","licitacoes","buscador","descarte"] },
    "risco":       { "type": "scale", "range": [0.0, 1.0] },
    "precisa_llm": { "type": "boolean" }
  }
}
```

## 🧠 4. CAMADA GENERATIVA (Sistema 2 — via OmniRoute)

- **NUNCA hardcode modelo.** Usar as rotas auto do gateway:
  - `auto/best-coding` — default para código + tool calling
  - `auto/best-fast` — validações rápidas e triagem
  - `auto/best-free` — tarefas de baixo custo
  - `auto/best-reasoning` — raciocínio profundo
- **Condição de disparo:** Laya retornar `precisa_llm: true` ou confiança < 0.70 (quando Laya existir).
- **Formato de saída:** JSON puro ou Markdown estrito, sem introduções.
- **Cérebro já 100% OmniRoute:** `OMNIROUTE_BASE_URL=http://nexus-omniroute.railway.internal:8080/v1`

## 🔌 5. TABELA OFICIAL DE PORTAS (verificada no Railway em 25/09/2026)

| Serviço | Porta | Status |
|---|---|---|
| nexus-cerebro | 3000 | ✅ ativo |
| nexus-membro-github | 3001 | ✅ ativo |
| nexus-membro-sistema | 3002 | ✅ ativo |
| nexus-membro-memoria | 3003 | ✅ ativo |
| Mercado Financeiro | 4000 | ✅ ativo (contrato oficial) |
| nexus-omniroute | **8080** | ✅ ativo (⚠️ NÃO é 20128 no Railway — 20128 é só local) |
| nexus-decisor-laya | 8080 no Railway (dominio publico resolve a porta) · 8000 em dev local | ✅ **ATIVO** (Laya real, checkpoint multilingual) |
| Finanças-Backend / Frontend | ver Railway | ✅ ativos (portas automáticas) |
| buscador / licitacoes / comunicacao-hub | ver Railway | ✅ ativos (portas automáticas) |

**Regras:** nunca invadir 3000-3003 nem 4000. Portas de serviços gerenciados pelo Railway usam `RAILWAY_PUBLIC_DOMAIN`.

## 💻 USO LOCAL (terminal / IDE)

A Laya aceita qualquer cliente HTTP. CLI de exemplo (`tools/laya-local.js`):

```bash
node tools/laya-local.js "me mostra o status dos servicos"
# 📌 Destino: sistema (94%) | ⚠️ Risco: 0.87/2 | 🧠 Precisa LLM: NÃO | 🛡️ Ação: despacho direto
```

- `LAYA_URL` env: default = domínio público do Railway; use `http://localhost:8000` para Laya local.
- Contrato: `POST {url}/v1/systemone` · types: `choice` / `score` / `noul` · gating: `answer_confidence`.

## 🛡️ 6. SEGURANÇA OBRIGATÓRIA

- Shell só via allowlist (ver `membro-sistema/src/tools/shellExec.js`).
- Segredos SÓ em variáveis de ambiente do Railway — nunca no código.
- `x-nexus-key` obrigatório em endpoints de execução.
- Timeouts: LLM até 5 min (GLM cold start) · Laya 1.5s · HTTP interno 30s.

---

## 📜 7. FONTE DA VERDADE DO ECOSSISTEMA

### Documento Mestre (Caminho Local)
`D:\Programas\Desenvolvendo\Documento_Mestre_Projeto_SaaS`

**Papel:** Contém as diretrizes mestras, a topologia de rede oficial e os documentos que alimentam o **NotebookLM** (caderno *Nexus Holding — Ecossistema Geral*) e o **Obsidian Vault** (via `nexus-membro-memoria` :3003).

### Instruções Locais do Módulo
- Cada módulo **pode** conter sua subpasta `docs/instructions/` para regras de negócio específicas.
- Essas regras são **sempre subordinadas** ao Documento Mestre — em caso de conflito, o Documento Mestre prevalece.

### Protocolo de Sincronização Obrigatório
1. Toda alteração em **portas**, **contratos de rotas** ou **novas rotinas** que envolvam a Laya (:8080) deve ser **registrada** para atualização no `Documento_Mestre_Projeto_SaaS`.
2. Após o registro, **sincronizar** com o **NotebookLM** (caderno *Nexus Holding — Ecossistema Geral*) para manter a base de conhecimento do ecossistema coerente com a infraestrutura real.
3. O módulo-memória (`:3003`) é o ponto de ponte entre o código e o Obsidian Vault — notas de mudança de topologia devem ser cimentadas no cofre via `escrever_obsidian` quando aplicável.

---

*Este arquivo é lido automaticamente por opencode, Antigravity e agentes. Mantenha atualizado a cada mudança de porta/contrato.*
