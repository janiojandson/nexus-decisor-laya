#!/usr/bin/env node
/**
 * 🧠 LAYA LOCAL — Consulta o Sistema 1 do Nexus diretamente do terminal.
 *
 * Uso:
 *   node tools/laya-local.js "me mostra o status dos servicos"
 *   LAYA_URL=http://localhost:8000 node tools/laya-local.js "analise este codigo"
 *
 * URL padrão: domínio público do Railway (não precisa de porta — o proxy resolve).
 * Defina LAYA_URL para apontar para localhost (Laya instalada na máquina) ou outra instância.
 */

const LAYA_URL = process.env.LAYA_URL || 'https://nexus-decisor-laya-production.up.railway.app/v1/systemone';

const PERGUNTAS_NEXUS = {
    destino: {
        type: 'choice',
        instructions: 'Para qual setor do ecossistema Nexus encaminhar esta mensagem?',
        criteria: {
            memoria: 'buscas de memoria, historico, obsidian, pesquisas anteriores',
            sistema: 'status de servicos, shell, arquivos, portas, saude',
            github: 'repositorios, commits, pull requests, deploy railway',
            mercado_financeiro: 'trading, candles, bybit, ativos, precos, fluxo',
            licitacoes: 'editais, PNCP, comprasnet, propostas',
            buscador: 'leads, prospeccao, google maps, cnpj',
            comunicacao: 'whatsapp, telegram, chatbots, mensageria',
            descarte: 'cumprimentos e mensagens sem acao',
        },
    },
    risco: {
        type: 'score',
        instructions: 'Nivel de risco operacional de 0 a 2',
        criteria: [
            'leitura segura sem alteracoes',
            'alteracao de dados ou codigo',
            'destruicao, transacao financeira ou deploy critico',
        ],
    },
    precisa_llm: {
        type: 'noul',
        instructions: 'Esta mensagem exige sintese, analise ou redacao em linguagem natural?',
    },
};

async function main() {
    const mensagem = process.argv.slice(2).join(' ').trim();

    if (!mensagem || mensagem === '-h' || mensagem === '--help') {
        console.log('Uso: node tools/laya-local.js "mensagem ou comando para triagem"');
        console.log('Env:  LAYA_URL (default: https://nexus-decisor-laya-production.up.railway.app/v1/systemone)');
        process.exit(0);
    }

    const t0 = Date.now();
    let resposta;
    try {
        const res = await fetch(LAYA_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                state: { origem: 'terminal_local', body: mensagem },
                questions: PERGUNTAS_NEXUS,
            }),
        });

        if (!res.ok) {
            console.error(`❌ Laya respondeu HTTP ${res.status} (verifique LAYA_URL=${LAYA_URL}).`);
            process.exit(1);
        }
        resposta = await res.json();
    } catch (erro) {
        console.error(`❌ Laya inacessível: ${erro.message}`);
        console.log('   Dica: para rodar 100% local, instale com pip install "laya[serve]" e use LAYA_URL=http://localhost:8000');
        process.exit(1);
    }

    const a = resposta.answers || {};
    const conf = (v) => `${Math.round((v ?? 0) * 100)}%`;

    console.log('');
    console.log('🧠 [LAYA — Sistema 1]');
    console.log(`📌 Destino:      ${a.destino?.choice ?? '?'} (confiança ${conf(a.destino?.answer_confidence)})`);
    console.log(`⚠️  Risco:        ${a.risco?.score ?? '?'}/2 (confiança ${conf(a.risco?.confidence)})`);
    console.log(`🧠 Precisa LLM:  ${(a.precisa_llm?.noul ?? 0) >= 0.5 ? 'SIM' : 'NÃO'} (prob ${conf(a.precisa_llm?.noul)})`);
    console.log(`🛡️  Ação:         ${a.precisa_llm?.noul === undefined ? '?' : ((a.precisa_llm.noul >= 0.5) ? 'fluxo LLM' : 'despacho direto')}`);
    console.log(`⏱️  Latência:     ${Date.now() - t0}ms${resposta.routing?.model ? ` | modelo: ${resposta.routing.model}` : ''}`);
    console.log('');
}

main();
