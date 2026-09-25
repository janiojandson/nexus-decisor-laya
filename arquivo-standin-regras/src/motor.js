// src/motor.js
// 🧠 LAYA — Motor de Decisão (Sistema 1)
// Híbrido determinístico: regras exatas → scoring de intenções → risco → necessidade de LLM
// Zero tokens, zero alucinação de formato, <40ms alvo.

// ======================================================
// 🗺️ INTENÇÕES E VOCABULÁRIO (por destino)
// ======================================================
const VOCABULARIO_DESTINOS = {
    memoria: {
        palavras: ['memoria', 'memória', 'lembra', 'lembre', 'historico', 'histórico', 'ontem', 'anteontem',
            'pesquisa anterior', 'ultima pesquisa', 'última pesquisa', 'hipocampo', 'obsidian', 'nota', 'notas',
            'cofre', 'aprendeu', 'aprendizado', 'sabe sobre', 'o que descobrimos', 'insight'],
        peso: 1.0,
    },
    sistema: {
        palavras: ['status', 'porta', 'portas', 'servico', 'serviço', 'shell', 'comando', 'arquivo', 'arquivos',
            'disco', 'processo', 'log', 'logs', 'saude', 'saúde', 'uptime', 'memoria do sistema', 'cpu',
            'versao', 'versão', 'diagnostico', 'diagnóstico', 'heartbeat', 'membros online'],
        peso: 1.0,
    },
    github: {
        palavras: ['repositorio', 'repositório', 'repo', 'commit', 'pull request', 'pr ', 'clone', 'clonar',
            'github', 'branch', 'merge', 'issues', 'fork', 'star', 'subir codigo', 'subir código',
            'push', 'deploy no railway', 'lancar no railway', 'lançar no railway'],
        peso: 1.0,
    },
    mercado_financeiro: {
        palavras: ['candle', 'candles', 'trading', 'bybit', 'mercado', 'preco', 'preço', 'ativo', 'ativos',
            'klines', 'fluxo', 'whale', 'absorção', 'absorcao', 'book imbalance', 'timeframe', 'ordem',
            'b3', 'binance', 'bitcoin', 'btc', 'cripto', 'acao', 'ação', 'acoes', 'ações'],
        peso: 1.0,
    },
    licitacoes: {
        palavras: ['licitacao', 'licitação', 'licitacoes', 'licitações', 'edital', 'editais', 'pncp',
            'comprasnet', 'proposta comercial', 'pregao', 'pregão', 'orgao publico', 'órgão público',
            'contratação publica', 'contratacao publica'],
        peso: 1.0,
    },
    buscador: {
        palavras: ['lead', 'leads', 'prospeccao', 'prospecção', 'buscar cliente', 'clientes potenciais',
            'google maps', 'cnpj', 'instagram', 'tiktok', 'gerar lead', 'lista de empresas', 'contato'],
        peso: 1.0,
    },
    comunicacao: {
        palavras: ['whatsapp', 'telegram', 'mensagem', 'mensagens', 'chatbot', 'bot', 'enviar para',
            'broadcast', 'fila de mensagem', 'baileys', 'atendimento'],
        peso: 1.0,
    },
    descarte: {
        palavras: ['oi', 'ola', 'olá', 'bom dia', 'boa tarde', 'boa noite', 'valeu', 'vlw', 'ok',
            'obrigado', 'obrigada', 'tchau', 'beleza', 'show', 'top', '👍', '❤️'],
        peso: 0.8,
    },
};

// ======================================================
// ⚠️ GATILHOS DE RISCO OPERACIONAL
// ======================================================
const GATILHOS_RISCO = [
    { padrao: /\b(deletar|apagar|remover|deletar tudo|dropar|drop|formatar|limpar tudo)\b/i, peso: 0.9 },
    { padrao: /\b(pagar|pagamento|comprar|assinatura|cartao|cartão|transacao|transação|pix|boleto|investir)\b/i, peso: 0.85 },
    { padrao: /\b(deploy em producao|deploy em produção|producao agora|produção agora|force push|reset --hard)\b/i, peso: 0.8 },
    { padrao: /\b(criar|alterar|modificar|editar|atualizar|renomear|mover|enviar|commit|push|publicar)\b/i, peso: 0.45 },
    { padrao: /\b(status|listar|mostrar|ver|ler|consultar|buscar|pesquisar|quanto|quantos|qual|quando)\b/i, peso: 0.1 },
];

// ======================================================
// 🧠 GATILHOS DE NECESSIDADE DE LLM (Síntese/criação)
// ======================================================
const GATILHOS_LLM = [
    /\b(analis\w+|resum\w+|escrev\w+|redig\w+|cri\w+ um|criar um|elabor\w+|compar\w+|avali\w+|sintetiz\w+)\b/i,
    /\b(como|por que|porque|explique|explicar|o que acha|sua opiniao|sua opinião|sugest\w+|recomend\w+)\b/i,
    /\b(plano|estrategia|estratégia|passo a passo|ideias|brainstorm|monetiz\w+|pitch)\b/i,
];

const GATILHOS_DIRETO = [
    /^(\/|!)?(status|saude|saúde|health|versao|versão|uptime|membros|ferramentas|ajuda|help)\b/i,
    /^(\/|!)?(oi|ola|olá|bom dia|boa tarde|boa noite)\b/i,
];

// ======================================================
// 🔢 MOTOR DE SCORING
// ======================================================
function normalizar(texto) {
    return String(texto || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
}

function classificarDestino(mensagem) {
    const msg = ' ' + normalizar(mensagem) + ' ';
    const msgSemAcento = normalizar(mensagem);
    let scores = {};

    for (const [destino, cfg] of Object.entries(VOCABULARIO_DESTINOS)) {
        let score = 0;
        for (const palavra of cfg.palavras) {
            const p = normalizar(palavra);
            // Match exato de palavra/frase vale mais; substring vale menos
            if (msg.includes(' ' + p + ' ')) score += 1.0 * cfg.peso;
            else if (msgSemAcento.includes(p)) score += 0.6 * cfg.peso;
        }
        scores[destino] = score;
    }

    let melhor = null;
    let segundo = null;
    for (const [destino, score] of Object.entries(scores)) {
        if (!melhor || score > scores[melhor]) {
            segundo = melhor;
            melhor = destino;
        } else if (!segundo || score > scores[segundo]) {
            segundo = destino;
        }
    }

    const topo = scores[melhor] || 0;
    const vice = scores[segundo] || 0;

    if (topo === 0) {
        return { choice: 'descarte', confidence: 0.3, scores }; // sem sinal: conservador
    }

    // Confiança: força do topo + margem sobre o vice (0.30 a 0.97)
    const forca = Math.min(topo / 3, 1);           // 3+ hits = força máxima
    const margem = topo > 0 ? (topo - vice) / topo : 0;
    const confidence = Math.round(Math.min(0.30 + forca * 0.45 + margem * 0.25, 0.97) * 100) / 100;

    return { choice: melhor, confidence, scores };
}

function classificarRisco(mensagem) {
    let risco = 0.10; // base: leitura
    for (const gatilho of GATILHOS_RISCO) {
        if (gatilho.padrao.test(mensagem)) risco = Math.max(risco, gatilho.peso);
    }
    return { score: Math.round(risco * 100) / 100, confidence: 0.9 };
}

function classificarNecessidadeLLM(mensagem, destino) {
    const msg = String(mensagem || '');

    // Comando direto curto → sem LLM
    if (GATILHOS_DIRETO.some(p => p.test(msg.trim())) && msg.length < 60) {
        return { boolean: false, confidence: 0.95 };
    }

    // Cumprimento/descarte → sem LLM
    if (destino === 'descarte' && msg.length < 40) {
        return { boolean: false, confidence: 0.92 };
    }

    // Síntese/análise/criação → LLM
    const pedeSintese = GATILHOS_LLM.some(p => p.test(msg));
    if (pedeSintese) {
        return { boolean: true, confidence: 0.93 };
    }

    // Mensagem longa/complexa → LLM (mesmo com destino claro)
    if (msg.length > 220) {
        return { boolean: true, confidence: 0.85 };
    }

    // Pergunta com interrogação → provável LLM
    if (/\?/.test(msg)) {
        return { boolean: true, confidence: 0.75 };
    }

    // Default: consulta direta ao destino, sem LLM
    return { boolean: false, confidence: 0.7 };
}

// ======================================================
// 🎯 DECISÃO COMPLETA
// ======================================================
export function decidir({ origem = 'desconhecida', mensagem = '' } = {}) {
    const t0 = process.hrtime.bigint();

    const destino = classificarDestino(mensagem);
    const risco = classificarRisco(mensagem);
    const precisaLLM = classificarNecessidadeLLM(mensagem, destino.choice);

    // Ajuste: risco alto SEMPRE exige caminho deliberado (LLM/humano)
    if (risco.score > 0.65) {
        precisaLLM.boolean = true;
        precisaLLM.confidence = Math.max(precisaLLM.confidence, 0.9);
    }

    const duracaoMs = Number(process.hrtime.bigint() - t0) / 1e6;

    return {
        success: true,
        answers: {
            destino: { choice: destino.choice, confidence: destino.confidence },
            risco: { score: risco.score, confidence: risco.confidence },
            precisa_llm: { boolean: precisaLLM.boolean, confidence: precisaLLM.confidence },
        },
        meta: {
            origem,
            duracao_ms: Math.round(duracaoMs * 100) / 100,
            motor: 'laya-v1-hybrid-rules',
            scores_detalle: destino.scores,
        },
    };
}
