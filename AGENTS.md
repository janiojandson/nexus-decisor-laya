# TEMPLATE — AGENTS.md (Padrão Unificado de Módulo Nexus)
> Versão 2.3 · 25/09/2026 · Laya REAL ativa (:8000) · OmniRoute com Volume Persistente (:8080) · Postgres Central Unificado (:5432)

---

# AGENTE: [Nome do Agente / Microsserviço]
**Módulo:** [ex: nexus-cerebro / buscador / financas-backend / operacional]
**Versão do Agente:** 2.2.0
**Porta do Serviço:** [ver tabela oficial abaixo]
**Decisor de Sistema 1:** Laya ✅ (Railway: `http://nexus-decisor-laya.railway.internal:8000/v1/systemone` · dev local: `http://localhost:8000/v1/systemone` ou `https://nexus-decisor-laya-production.up.railway.app/v1/systemone`)

## 🎯 1. MISSÃO E ESCOPO

- **Objetivo Primário:** [1-2 frases com a função crítica deste agente]
- **Escopo Permitido:** [rotas Express, tabelas PostgreSQL, webhooks autorizados]

**Limites Estritos de Contenção (Anti-Regressão):**
- Nunca reescrever mais de 40 linhas sem validação prévia — apenas diffs cirúrgicos.
- Nunca alterar contratos de rotas existentes sem retrocompatibilidade.
- Toda comunicação inter-serviços pela Railway Private Mesh (`*.railway.internal:PORTA`).

## 🏗️ 2. ARQUITETURA DE 4 CAMADAS (Universal: Telegram, Terminal, OpenCode e IDE)

```
Entrada (Telegram | Terminal CLI | OpenCode / IDE | Webhook | Cron)
  → CAMADA 1 — LAYA (Sistema 1)  [✅ ATIVA — <1s, R$0 de tokens]
      Triagem rápida CPU: identifica destino, risco operacional e necessidade de LLM.
      Atua UNIVERSALMENTE em todas as chamadas do Cérebro (não apenas no Telegram).
      CLI Local / OpenCode: node tools/laya-local.js "sua diretriz"
  → CAMADA 2 — CÉREBRO (Orquestrador Sistema 2) [✅ 100% Desinchado]
      pensarEAgir + tool calling distribuído + despacho aos Membros da frota.
  → CAMADA 3 — OMNIROUTE (Maestro de Chaves & IA) [✅ Volume /app/data Persistente]
      Centraliza rotação, 7 contas Antigravity, pools free (Groq, Gemini, OpenRouter) e chaves pagas.
      Rotas semânticas: auto/best-coding, auto/best-fast, auto/best-free, auto/best-reasoning.
  → CAMADA 4 — PROVIDERS & MEMBROS [✅ Execução Final]
      Google Gemini · Groq · OpenRouter · Modal GLM-5.1 · Membro Sistema · Membro Memória · Membro GitHub.
```

## 💰 3. REGRA DE OURO DE INFRAESTRUTURA & ECONOMIA (VOLUMES & BANCO)

Ao criar um novo projeto ou refatorar projetos existentes, **NUNCA instancie banco ou volume redundante**:

1. **Postgres Principal Unificado (Regra de Custo Zero de Infra):**
   - **NÃO crie containers PostgreSQL adicionais** (cada container gasta RAM e volume desnecessários).
   - Use SEMPRE o **`Postgres` Principal** (`postgres.railway.internal:5432`).
   - Para isolamento de projetos, crie um **Database dedicado** dentro do servidor principal (ex: `financas_db`, `railway`).
   - String de conexão: `postgresql://postgres:eyxuLapofrztxnKcfhRZVgBAajjfAuUY@postgres.railway.internal:5432/NOME_DO_SEU_DB`

2. **Diretriz de Volumes Persistentes (Railway):**
   - **Serviços Stateless (Custo Zero de Disco):** Não adicione volume a microsserviços de lógica pura (ex: `buscador`, `licitacoes`, `membro-sistema`).
   - **Serviços Stateful Críticos (Volume Obrigatório):**
     - `Postgres`: `/var/lib/postgresql/data` (dados relacionais).
     - `nexus-omniroute`: `/app/data` (blindagem permanente de contas Antigravity e chaves SQLite).
     - `nexus-decisor-laya`: `/data` (cache de PyTorch/HF, evita re-download de ~1GB).
     - `comunicacao-hub`: `/app/storage` (sessões de WhatsApp).

## 📡 4. PROTOCOLO LAYA (Sistema 1 no Terminal, OpenCode e Telegram)

A Laya é acessível por qualquer ferramenta (Node, Python, cURL, OpenCode):

- **Como usar no OpenCode / Terminal:**
  ```bash
  node tools/laya-local.js "como está o mercado financeiro hoje?"
  # Retorna em <1s: Destino: mercado_financeiro (100%) | Risco: 0.7/2 | Precisa LLM: NÃO
  ```
- **Como o Cérebro usa internamente:**
  Todo comando que entra via `pensarEAgir` (seja por API HTTP do OpenCode, porta 3000, ou Telegram) passa primeiro pela função `triagemLaya()` registrando telemetria e intenção antes de gastar qualquer token.

## 🔌 5. TABELA OFICIAL DE PORTAS (Topologia Homologada)

| Serviço | Porta | Domínio Interno Railway | Domínio Público / Local |
|---|---|---|---|
| **nexus-cerebro** | **3000** | `nexus-cerebro.railway.internal:3000` | `nexus-cerebro-production-a7c0.up.railway.app` |
| **nexus-membro-github** | **3001** | `tranquil-eagerness.railway.internal:3001` | Interno |
| **nexus-membro-sistema** | **3002** | `nexus-membro-sistema.railway.internal:3002` | Interno |
| **nexus-membro-memoria** | **3003** | `nexus-membro-memoria.railway.internal:3003` | Interno |
| **Mercado Financeiro** | **4000** | `operacional.railway.internal:4000` | `operacional-production-57d9.up.railway.app` |
| **Postgres Principal** | **5432** | `postgres.railway.internal:5432` | Proxy TCP externo 25561 |
| **nexus-decisor-laya** | **8000** | `nexus-decisor-laya.railway.internal:8000` | `nexus-decisor-laya-production.up.railway.app` |
| **nexus-omniroute** | **8080** | `nexus-omniroute.railway.internal:8080` | `nexus-omniroute-production.up.railway.app` |

---

## 📜 6. FONTE DA VERDADE DO ECOSSISTEMA

### Documento Mestre & NotebookLM:
- **Caminho Local:** `D:\Programas\Desenvolvendo\Documento_Mestre_Projeto_SaaS`
- **Caderno NotebookLM:** *Nexus Holding — Ecossistema Geral*
- Toda nova regra de banco unificado, portas e volumes deve ser sincronizada nesses arquivos para manter o cérebro institucional e os agentes alinhados.

---

## 📊 7. REGRAS DE ARQUITETURA VISUAL E DESACOPLAMENTO DE DASHBOARDS (POSTGRESQL + LOOKER STUDIO)
1. **Zero Webhook para Planilhas**: Sempre que a demanda envolver a criação de dashboards, painéis de auditoria, relatórios gerenciais ou cálculos de métricas sobre dados operacionais já armazenados no PostgreSQL do Railway, a IA NÃO deve criar lógicas de apresentação, requisições HTTP secundárias (webhooks) ou integrações via código para planilhas como o Google Sheets.
2. **Responsabilidade Única do Backend**: A aplicação (backend) deve manter a responsabilidade única de registrar os dados brutos em alta velocidade (fire-and-forget), preservando a latência exigida (sub-25ms) e o rate limit das rotas críticas.
3. **Google Looker Studio Passivo**: Para visualização de métricas e comparativos, a IA deve sugerir apenas a criação de Views SQL estruturadas no PostgreSQL e orientar a conexão direta, gratuita e passiva do Google Looker Studio à URL Pública do banco (`zephyr.proxy.rlwy.net:25561`).

