import express from "express";
import path from "path";
import { createServer as createViteServer } from "vite";
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function startServer() {
  const app = express();
  const PORT = Number(process.env.PORT) || 3000;

  app.use(express.json({ limit: '50mb' }));
  app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
    res.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    if (req.method === 'OPTIONS') {
      res.sendStatus(204);
      return;
    }
    next();
  });

  // API Health Check
  app.get("/api/health", (req, res) => {
    res.json({ status: "ok", service: "APL-Migration-Backend", version: "1.0.0" });
  });

  // Mock migration endpoints used by the frontend
  app.post('/api/understand', (req, res) => {
    const code = String(req.body?.apl_code || '');
    res.json({
      program_type: code.includes('⍴') ? 'array-manipulation' : 'data-processing',
      variables_detected: ['input', 'output'],
      operations_detected: ['transform', 'summarize'],
      business_summary: 'The APL program processes data and produces a derived result.',
      confidence_score: 0.92,
    });
  });

  app.post('/api/convert', (req, res) => {
    const code = String(req.body?.apl_code || '');
    res.json({
      python_code: `# Converted from APL\nresult = ${code ? 'process_data()' : 'None'}\nprint(result)`,
      explanation: 'A basic Python translation generated for deployment.',
    });
  });

  app.post('/api/validate/apl', (req, res) => {
    res.json({ status: 'ok', output: 'APL execution completed successfully.' });
  });

  app.post('/api/validate/python', (req, res) => {
    res.json({ status: 'ok', output: 'Python execution completed successfully.' });
  });

  app.post('/api/compare', (req, res) => {
    res.json({ match: true, message: 'APL and Python outputs are consistent.' });
  });

  // Mock API for Migration Jobs (Enterprise Storage Simulation)
  let migrationJobs: any[] = [];

  app.get("/api/jobs", (req, res) => {
    res.json(migrationJobs);
  });

  app.post("/api/jobs", (req, res) => {
    const job = {
      id: `JOB-${Date.now()}`,
      status: 'pending',
      createdAt: new Date().toISOString(),
      ...req.body
    };
    migrationJobs.push(job);
    res.status(201).json(job);
  });

  // Vite middleware for development
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), 'dist');
    app.use(express.static(distPath));
    app.get('*', (req, res) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running on http://0.0.0.0:${PORT}`);
  });
}

startServer();
