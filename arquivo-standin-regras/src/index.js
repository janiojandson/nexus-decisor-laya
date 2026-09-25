// src/index.js
// 🚀 LAYA — Sistema 1 do Nexus (Porta 8000)
// API de decisão rápida: POST /decide · GET /health · GET /stats

import express from 'express';
import { decidir } from './motor.js';

const app = express();
app.use(express.json({ limit: '256kb' }));

const PORT = process.env.PORT || 8000;
const LAYA_API_KEY = process.env.LAYA_API_KEY || null; // opcional: se setado, exige x-laya-key

// ======================================================
// 🔐 AUTENTICAÇÃO (opcional — rede privada Railway)
// ======================================================
app.use((req, res, next) => {
    if (!LAYA_API_KEY) return next(); // modo aberto na private mesh
    if (req.path === '/health') return next();
    const chave = req.headers['x-laya-key'] || req.headers['authorization']?.replace('Bearer ', '');
    if (chave !== LAYA_API_KEY) return res.status(401).json({ success: false, error: 'Acesso negado.' });
    next();
});

// ======================================================
// 🎯 POST /decide — CONTRATO OFICIAL
// ======================================================
let stats = { total: 0, por_destino: {}, latencia_media_ms: 0, iniciado_em: new Date().toISOString() };

app.post('/decide', (req, res) => {
    const { state, questions } = req.body || {};

    if (!state || typeof state.mensagem !== 'string' || !state.mensagem.trim()) {
        return res.status(400).json({
            success: false,
            error: 'Payload inválido: informe { state: { origem, mensagem }, questions: { destino, risco, precisa_llm } }',
        });
    }

    const resultado = decidir({ origem: state.origem, mensagem: state.mensagem });

    // Respeitar apenas as perguntas feitas (contrato flexível)
    if (questions && typeof questions === 'object' && !Array.isArray(questions)) {
        const pedidas = Object.keys(questions);
        if (pedidas.length > 0) {
            resultado.answers = Object.fromEntries(
                pedidas.filter(q => resultado.answers[q]).map(q => [q, resultado.answers[q]])
            );
        }
    }

    // Estatísticas
    stats.total++;
    const d = resultado.answers.destino?.choice || 'n/a';
    stats.por_destino[d] = (stats.por_destino[d] || 0) + 1;
    stats.latencia_media_ms = Math.round(((stats.latencia_media_ms * (stats.total - 1)) + resultado.meta.duracao_ms) / stats.total * 100) / 100;

    res.json(resultado);
});

// ======================================================
// 🏥 GET /health · GET /stats
// ======================================================
app.get('/health', (_req, res) => {
    res.json({
        status: 'healthy',
        servico: 'nexus-decisor-laya',
        sistema: '1 (decisão rápida)',
        uptime: Math.round(process.uptime()),
        motor: 'laya-v1-hybrid-rules',
        timestamp: new Date().toISOString(),
    });
});

app.get('/stats', (_req, res) => {
    res.json({ ...stats, uptime_s: Math.round(process.uptime()) });
});

app.listen(PORT, '0.0.0.0', () => {
    console.log(`🧠 [LAYA] Sistema 1 ativo na porta ${PORT} — decisão rápida, zero tokens.`);
    console.log(`🎯 [LAYA] POST /decide · GET /health · GET /stats`);
});
