const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const path = require('path');
const http = require('http');

const app = express();
const PORT = process.env.PORT || 8080;

// Backend API URL (ACI private IP in VNet)
const BACKEND_URL = process.env.BACKEND_URL || 'http://10.0.4.5:8000';

// Create HTTP agent with extended keep-alive timeout for long-running SSE connections
const httpAgent = new http.Agent({
    keepAlive: true,
    keepAliveMsecs: 300000,  // 5 minutes keep-alive
    maxSockets: 100,
    timeout: 600000  // 10 minutes socket timeout
});

// Proxy API requests to backend
app.use('/api', createProxyMiddleware({
    target: BACKEND_URL,
    changeOrigin: true,
    pathRewrite: {
        '^/api': '/api'
    },
    agent: httpAgent,
    // Increase timeout for long-running requests (10 minutes)
    proxyTimeout: 600000,
    timeout: 600000,
    // Support streaming responses (SSE)
    onProxyRes: (proxyRes, req, res) => {
        // Disable buffering for streaming responses
        if (proxyRes.headers['content-type']?.includes('text/event-stream')) {
            res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate');
            res.setHeader('X-Accel-Buffering', 'no');
            res.setHeader('Connection', 'keep-alive');
            res.flushHeaders();
        }
        // Log response for debugging
        console.log(`Proxy response: ${req.method} ${req.path} -> ${proxyRes.statusCode}`);
    },
    onProxyReq: (proxyReq, req, res) => {
        // Log request for debugging
        console.log(`Proxy request: ${req.method} ${req.path}`);
    },
    onError: (err, req, res) => {
        console.error('Proxy error:', err.message);
        if (!res.headersSent) {
            res.status(502).json({ error: 'Backend service unavailable', details: err.message });
        }
    }
}));

// Serve static files from the build directory
app.use(express.static(path.join(__dirname, 'static')));

// Serve index.html for all other routes (SPA support)
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'static', 'index.html'));
});

// Create server with extended timeouts for SSE
const server = app.listen(PORT, () => {
    console.log(`Frontend server running on port ${PORT}`);
    console.log(`Proxying API requests to ${BACKEND_URL}`);
});

// Extend server timeouts for long-running SSE connections
server.keepAliveTimeout = 620000;  // 10 minutes + buffer
server.headersTimeout = 630000;    // Slightly higher than keepAliveTimeout
server.timeout = 0;                // Disable request timeout (handled by proxy)

console.log('Server timeouts configured for SSE streaming');
