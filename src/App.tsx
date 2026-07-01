import React, { useState, useEffect } from 'react';
import { BASE_URL } from './lib/gemini';
import { 
  Copy,
  Download,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Zap,
  Code2,
  ShieldCheck,
  Cpu,
  Database,
  FileText,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

// Phase Stepper Component
const PhaseStepper = ({ currentPhase }: { currentPhase: number }) => {
  const phases = [
    { id: 1, label: 'Understanding', icon: '🧠' },
    { id: 2, label: 'Conversion', icon: '🔄' },
    { id: 3, label: 'APL Execution', icon: '⚡' },
    { id: 4, label: 'Python Execution', icon: '🐍' },
    { id: 5, label: 'Validation', icon: '✓' },
  ];

  return (
    <div className="flex items-center justify-center gap-4 flex-wrap">
      {phases.map((phase, idx) => (
        <React.Fragment key={phase.id}>
          <div className={`flex flex-col items-center gap-1 transition-all ${
            currentPhase >= phase.id ? 'opacity-100' : 'opacity-40'
          }`}>
            <div className={`flex items-center justify-center w-12 h-12 rounded-lg border-2 transition-all font-semibold ${
              currentPhase > phase.id ? 'bg-emerald-100 border-emerald-300 text-emerald-700' :
              currentPhase === phase.id ? 'bg-indigo-100 border-indigo-500 text-indigo-700 shadow-lg animate-pulse' :
              'bg-slate-100 border-slate-300 text-slate-500'
            }`}>
              <span className="text-xl">{phase.icon}</span>
            </div>
            <span className={`text-[11px] font-bold uppercase tracking-wide ${
              currentPhase >= phase.id ? 'text-slate-900' : 'text-slate-400'
            }`}>
              {phase.label}
            </span>
            <span className="text-[9px] text-slate-400">
              {currentPhase > phase.id ? '✓' : currentPhase === phase.id ? '...' : '○'}
            </span>
          </div>
          {idx < phases.length - 1 && (
            <div className={`w-8 h-1 mb-6 transition-all ${
              currentPhase > phase.id ? 'bg-emerald-300' : 'bg-slate-200'
            }`}></div>
          )}
        </React.Fragment>
      ))}
    </div>
  );
};

// Code Display Component
const CodeDisplay = ({ code, language = 'python', title }: any) => {
  const lines = typeof code === 'string' 
    ? code.split('\n') 
    : JSON.stringify(code, null, 2).split('\n');
  
  return (
    <div className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
      <div className="px-4 py-3 bg-slate-900 border-b border-slate-800 flex items-center justify-between">
        <span className="text-[11px] font-bold text-slate-300 uppercase tracking-wider">{title}</span>
        <span className="text-[9px] font-mono text-slate-500 bg-slate-800 px-2 py-1 rounded">{language}</span>
      </div>
      <div className="relative overflow-x-auto max-h-96 overflow-y-auto custom-scrollbar">
        <div className="flex">
          <div className="w-12 bg-slate-900 border-r border-slate-800 flex flex-col items-center pt-4 text-[10px] font-mono text-slate-600 select-none flex-shrink-0">
            {lines.map((_, i) => (
              <div key={i} className="h-5 leading-5">{String(i + 1).padStart(2, '0')}</div>
            ))}
          </div>
          <pre className="flex-1 p-4 font-mono text-xs text-slate-100 leading-5">
{typeof code === 'string' ? code : JSON.stringify(code, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
};

// Collapsible Section Component
const CollapsibleSection = ({ title, icon: Icon, children, defaultOpen = false }: any) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  return (
    <div className="border border-slate-200 rounded-lg overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-3 bg-slate-50 hover:bg-slate-100 transition-colors flex items-center justify-between"
      >
        <div className="flex items-center gap-2">
          <Icon className="w-4 h-4 text-indigo-600" />
          <span className="font-semibold text-slate-900">{title}</span>
        </div>
        {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
      </button>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t border-slate-200 p-4 bg-white"
          >
            {children}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

interface MigrationState {
  apl_code?: string;
  understanding?: any;
  python_code?: string;
  conversion?: any;
  apl_output?: any;
  python_output?: any;
  comparison?: any;
  error?: string;
  timestamp?: string;
}

const normalizeUnderstanding = (understanding: any) => {
  if (!understanding || typeof understanding !== 'object') return null;

  const program_type = understanding.program_type ?? understanding.programType ?? understanding.operator ?? undefined;
  const variables_detected = understanding.variables_detected ?? understanding.variablesDetected ?? understanding.variables ?? [];
  const operations_detected = understanding.operations_detected ?? understanding.operationsDetected ?? understanding.operations ?? [];
  const business_summary = understanding.business_summary ?? understanding.businessSummary ?? understanding.explanation ?? '';
  const rawConfidence = understanding.confidence_score ?? understanding.confidence ?? understanding.score ?? undefined;

  let confidence = typeof rawConfidence === 'number' ? rawConfidence : parseFloat(String(rawConfidence ?? ''));
  if (Number.isNaN(confidence)) {
    confidence = undefined;
  }

  if (confidence !== undefined && confidence > 1) {
    confidence = confidence / 100;
  }

  return {
    program_type,
    variables_detected: Array.isArray(variables_detected) ? variables_detected : [variables_detected].filter(Boolean),
    operations_detected: Array.isArray(operations_detected) ? operations_detected : [operations_detected].filter(Boolean),
    business_summary,
    confidence_score: confidence,
  };
};

function App() {
  const [aplCode, setAplCode] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentPhase, setCurrentPhase] = useState(0);
  const [result, setResult] = useState<MigrationState | null>(null);
  const [backendStatus, setBackendStatus] = useState<{ status: string; version?: string } | null>(null);
  const [copyFeedback, setCopyFeedback] = useState('');

  // Check backend health
  useEffect(() => {
    let mounted = true;
    const checkHealth = async () => {
      try {
        const res = await fetch(`${BASE_URL}/api/health`);
        if (!mounted) return;
        if (res.ok) {
          const json = await res.json();
          setBackendStatus(json);
        } else {
          setBackendStatus({ status: 'unreachable' });
        }
      } catch (e) {
        if (!mounted) return;
        setBackendStatus({ status: 'down' });
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 5000);
    return () => { 
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const handleMigration = async (code: string) => {
    if (!code.trim()) return;
    
    setIsProcessing(true);
    setCurrentPhase(1);
    setResult(null);
    
    const state: MigrationState = { apl_code: code, timestamp: new Date().toISOString() };
    
    try {
      // Phase 1: Understanding
      try {
        const res = await fetch(`${BASE_URL}/api/understand`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ apl_code: code })
        });
        state.understanding = res.ok ? await res.json() : { error: await res.text() };
      } catch (e) {
        state.understanding = { error: String(e) };
      }
      setCurrentPhase(2);

      // Phase 2: Conversion
      try {
        const res = await fetch(`${BASE_URL}/api/convert`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ apl_code: code, understanding: state.understanding })
        });
        state.conversion = res.ok ? await res.json() : { error: await res.text() };
        state.python_code = state.conversion?.python_code || state.conversion || '';
      } catch (e) {
        state.conversion = { error: String(e) };
      }
      setCurrentPhase(3);

      // Phase 3: APL Execution
      try {
        const res = await fetch(`${BASE_URL}/api/validate/apl`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ apl_code: code })
        });
        state.apl_output = res.ok ? await res.json() : { error: await res.text() };
      } catch (e) {
        state.apl_output = { error: String(e) };
      }
      setCurrentPhase(4);

      // Phase 4: Python Execution
      try {
        const res = await fetch(`${BASE_URL}/api/validate/python`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ python_code: state.python_code })
        });
        state.python_output = res.ok ? await res.json() : { error: await res.text() };
      } catch (e) {
        state.python_output = { error: String(e) };
      }
      setCurrentPhase(5);

      // Phase 5: Validation/Comparison
      try {
        const res = await fetch(`${BASE_URL}/api/compare`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ apl_result: state.apl_output, python_result: state.python_output })
        });
        state.comparison = res.ok ? await res.json() : { error: await res.text() };
      } catch (e) {
        state.comparison = { error: String(e) };
      }

      setResult(state);
    } catch (err) {
      console.error('Migration error:', err);
      setResult({ ...state, error: String(err) });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result as string;
      setAplCode(content);
    };
    reader.onerror = () => {
      alert('Failed to read file');
    };
    reader.readAsText(file);
  };

  const handleCopyPython = () => {
    const code = result?.python_code;
    if (!code) return;
    navigator.clipboard.writeText(typeof code === 'string' ? code : JSON.stringify(code, null, 2));
    setCopyFeedback('Python code copied!');
    setTimeout(() => setCopyFeedback(''), 2000);
  };

  const handleDownloadPython = () => {
    const code = result?.python_code;
    if (!code) return;
    const element = document.createElement('a');
    element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(
      typeof code === 'string' ? code : JSON.stringify(code, null, 2)
    ));
    element.setAttribute('download', 'migration_output.py');
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const isBackendHealthy = backendStatus?.status === 'healthy';
  const understanding = result?.understanding ? normalizeUnderstanding(result.understanding) : null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-start justify-between mb-6">
            <div>
              <h1 className="text-4xl font-bold text-slate-900 tracking-tight">
                APL to Python Migration Platform
              </h1>
              <p className="text-slate-500 mt-1">AI-Assisted Legacy Code Modernization & Validation</p>
            </div>
            <div className={`px-4 py-2 rounded-lg border ${
              isBackendHealthy 
                ? 'bg-emerald-50 border-emerald-200 text-emerald-700' 
                : 'bg-rose-50 border-rose-200 text-rose-700'
            }`}>
              <div className="text-xs font-bold uppercase tracking-wider flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${isBackendHealthy ? 'bg-emerald-500' : 'bg-rose-500'}`}></div>
                {isBackendHealthy ? 'System Healthy' : 'Backend Unavailable'}
              </div>
              <div className="text-[11px] text-slate-600 mt-1 font-mono">
                {backendStatus?.version && `v${backendStatus.version}`}
              </div>
            </div>
          </div>

          {/* System Status Panel */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
            {[
              { label: 'Understanding Agent', status: true },
              { label: 'Conversion Agent', status: true },
              { label: 'APL Runtime', status: isBackendHealthy },
              { label: 'Python Runtime', status: isBackendHealthy },
              { label: 'Validation Engine', status: isBackendHealthy },
            ].map((item, i) => (
              <div key={i} className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg">
                <div className="text-[10px] font-bold text-slate-600 uppercase tracking-wider flex items-center gap-2">
                  <div className={`w-1.5 h-1.5 rounded-full ${item.status ? 'bg-emerald-500' : 'bg-rose-500'}`}></div>
                  {item.label}
                </div>
              </div>
            ))}
          </div>

          {/* Pipeline Progress */}
          <div className="bg-white border border-slate-200 rounded-xl p-4">
            <div className="text-xs font-bold text-slate-600 uppercase tracking-wider mb-4">Migration Pipeline Progress</div>
            <PhaseStepper currentPhase={currentPhase} />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        <AnimatePresence mode="wait">
          {isProcessing && (
            <motion.div
              key="processing"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-40"
            >
              <div className="bg-white rounded-xl shadow-2xl p-8 max-w-md text-center space-y-6">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-indigo-100">
                  <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-slate-900">Processing</h3>
                  <p className="text-slate-500 text-sm mt-2">Running Phase {currentPhase} of 5...</p>
                </div>
                <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-indigo-600 transition-all duration-300"
                    style={{ width: `${(currentPhase / 5) * 100}%` }}
                  ></div>
                </div>
              </div>
            </motion.div>
          )}

          {!isProcessing && (
            <motion.div
              key="content"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="grid grid-cols-1 lg:grid-cols-3 gap-6"
            >
              {/* LEFT COLUMN: APL Input */}
              <div className="space-y-6">
                <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
                  <h2 className="text-lg font-bold text-slate-900 mb-4">APL Code Input</h2>
                  <div className="space-y-4">
                    {/* File Upload */}
                    <div>
                      <label className="text-xs font-semibold text-slate-700 mb-2 block">Upload .apl File</label>
                      <input 
                        type="file" 
                        accept=".apl" 
                        onChange={handleFileUpload}
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm cursor-pointer hover:border-indigo-400 transition-colors"
                      />
                    </div>
                    <div className="text-xs text-slate-400 text-center">or paste code below</div>
                    <textarea
                      value={aplCode}
                      onChange={(e) => setAplCode(e.target.value)}
                      placeholder="Paste your APL code here...&#10;Example:&#10;sum ← +/&#10;sum ⍳ 10"
                      className="w-full h-64 p-3 font-mono text-sm text-slate-900 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none placeholder:text-slate-500"
                    />
                    <div className="flex gap-2">
                      <button
                        onClick={() => { setAplCode(''); setResult(null); setCurrentPhase(0); }}
                        className="flex-1 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-lg transition-colors"
                      >
                        Clear
                      </button>
                      <button
                        onClick={() => handleMigration(aplCode)}
                        disabled={!aplCode.trim() || isProcessing}
                        className="flex-1 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white font-semibold rounded-lg transition-colors"
                      >
                        Run Migration
                      </button>
                    </div>
                  </div>
                </div>

                {/* Project Achievements */}
                <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
                  <h3 className="text-sm font-bold text-slate-900 mb-3 uppercase tracking-wider">Completed Capabilities</h3>
                  <div className="space-y-2">
                    {[
                      'Understanding Agent',
                      'Conversion Agent',
                      'Dyalog APL Execution',
                      'Python Execution',
                      'Output Validation',
                      'Provider Architecture',
                      'End-to-End Pipeline',
                    ].map((capability, i) => (
                      <div key={i} className="flex items-center gap-2 text-sm">
                        <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                        <span className="text-slate-700">{capability}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* CENTER COLUMN: Results */}
              <div className="space-y-6">
                {result ? (
                  <>
                    {/* Understanding Results */}
                    <CollapsibleSection 
                      title="Phase 1: Understanding Results" 
                      icon={Cpu}
                      defaultOpen
                    >
                      {result.understanding?.error ? (
                        <div className="text-sm text-rose-600 bg-rose-50 p-3 rounded border border-rose-200 flex gap-2">
                          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                          <div>{result.understanding.error}</div>
                        </div>
                      ) : understanding ? (
                        <div className="space-y-3 text-sm">
                          {understanding.program_type !== undefined && (
                            <div>
                              <div className="text-slate-600 font-semibold">Program Type</div>
                              <div className="text-slate-900">{String(understanding.program_type)}</div>
                            </div>
                          )}
                          {understanding.variables_detected.length > 0 && (
                            <div>
                              <div className="text-slate-600 font-semibold">Variables Detected</div>
                              <div className="text-slate-900">{understanding.variables_detected.join(', ')}</div>
                            </div>
                          )}
                          {understanding.operations_detected.length > 0 && (
                            <div>
                              <div className="text-slate-600 font-semibold">Operations</div>
                              <div className="text-slate-900">{understanding.operations_detected.join(', ')}</div>
                            </div>
                          )}
                          {understanding.business_summary !== undefined && (
                            <div>
                              <div className="text-slate-600 font-semibold">Business Summary</div>
                              <div className="text-slate-700 leading-relaxed">{String(understanding.business_summary)}</div>
                            </div>
                          )}
                          {understanding.confidence_score !== undefined && (
                            <div>
                              <div className="text-slate-600 font-semibold">Confidence Score</div>
                              <div className="text-slate-900 font-mono">{Number.isFinite(understanding.confidence_score) ? `${(understanding.confidence_score * 100).toFixed(1)}%` : 'N/A'}</div>
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="text-sm text-slate-500">No understanding data available.</div>
                      )}
                    </CollapsibleSection>

                    {/* Python Code */}
                    <CollapsibleSection 
                      title="Phase 2: Converted Python Code" 
                      icon={Code2}
                      defaultOpen
                    >
                      {result.conversion?.error ? (
                        <div className="text-sm text-rose-600 bg-rose-50 p-3 rounded border border-rose-200 flex gap-2">
                          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                          <div>{result.conversion.error}</div>
                        </div>
                      ) : (
                        <div className="space-y-3">
                          <CodeDisplay 
                            code={result.python_code} 
                            language="python"
                            title="Generated Python"
                          />
                          <div className="flex gap-2">
                            <button
                              onClick={handleCopyPython}
                              className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-lg transition-colors"
                            >
                              <Copy className="w-4 h-4" />
                              Copy Python Code
                            </button>
                            <button
                              onClick={handleDownloadPython}
                              className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-lg transition-colors"
                            >
                              <Download className="w-4 h-4" />
                              Download
                            </button>
                          </div>
                          {copyFeedback && (
                            <div className="text-xs text-emerald-600 bg-emerald-50 p-2 rounded border border-emerald-200 flex items-center gap-2">
                              <CheckCircle2 className="w-4 h-4" />
                              {copyFeedback}
                            </div>
                          )}
                        </div>
                      )}
                    </CollapsibleSection>
                  </>
                ) : (
                  <div className="bg-slate-50 border border-slate-200 rounded-xl p-8 text-center h-96 flex flex-col items-center justify-center">
                    <div className="w-12 h-12 rounded-full bg-slate-200 flex items-center justify-center mb-4">
                      <FileText className="w-6 h-6 text-slate-400" />
                    </div>
                    <p className="text-slate-500 text-sm">Run a migration to see results</p>
                  </div>
                )}
              </div>

              {/* RIGHT COLUMN: Validation */}
              <div className="space-y-6">
                {result ? (
                  <>
                    {/* APL Output */}
                    <CollapsibleSection 
                      title="Phase 3: APL Execution" 
                      icon={Zap}
                    >
                      {result.apl_output?.error ? (
                        <div className="text-sm text-rose-600 bg-rose-50 p-3 rounded border border-rose-200 flex gap-2">
                          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                          <div>{result.apl_output.error}</div>
                        </div>
                      ) : (
                        <pre className="text-xs bg-slate-950 text-slate-100 p-3 rounded border border-slate-800 max-h-48 overflow-auto font-mono">
{JSON.stringify(result.apl_output, null, 2)}
                        </pre>
                      )}
                    </CollapsibleSection>

                    {/* Python Output */}
                    <CollapsibleSection 
                      title="Phase 4: Python Execution" 
                      icon={Database}
                    >
                      {result.python_output?.error ? (
                        <div className="text-sm text-rose-600 bg-rose-50 p-3 rounded border border-rose-200 flex gap-2">
                          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                          <div>{result.python_output.error}</div>
                        </div>
                      ) : (
                        <pre className="text-xs bg-slate-950 text-slate-100 p-3 rounded border border-slate-800 max-h-48 overflow-auto font-mono">
{JSON.stringify(result.python_output, null, 2)}
                        </pre>
                      )}
                    </CollapsibleSection>

                    {/* Validation Results */}
                    <CollapsibleSection 
                      title="Phase 5: Validation Result" 
                      icon={ShieldCheck}
                      defaultOpen
                    >
                      {result.comparison?.error ? (
                        <div className="text-sm text-rose-600 bg-rose-50 p-3 rounded border border-rose-200 flex gap-2">
                          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                          <div>{result.comparison.error}</div>
                        </div>
                      ) : (
                        <div className="space-y-4">
                          <div className="flex items-center gap-3 p-3 bg-emerald-50 border border-emerald-200 rounded-lg">
                            <div className={`w-3 h-3 rounded-full ${result.comparison?.match ? 'bg-emerald-500' : 'bg-rose-500'}`}></div>
                            <span className={`font-semibold ${result.comparison?.match ? 'text-emerald-700' : 'text-rose-700'}`}>
                              {result.comparison?.match ? 'PASS - Parity Validation Successful' : 'FAIL - Output Mismatch'}
                            </span>
                          </div>

                          {result.comparison?.score !== undefined && (
                            <div>
                              <div className="text-sm font-semibold text-slate-900">Similarity Score</div>
                              <div className="flex items-center gap-2 mt-2">
                                <div className="flex-1 h-2 bg-slate-200 rounded-full overflow-hidden">
                                  <div 
                                    className="h-full bg-indigo-600 transition-all"
                                    style={{ width: `${(result.comparison.score * 100)}%` }}
                                  ></div>
                                </div>
                                <span className="font-mono text-sm font-semibold">{(result.comparison.score * 100).toFixed(1)}%</span>
                              </div>
                            </div>
                          )}

                          {result.comparison?.issues && result.comparison.issues.length > 0 && (
                            <div>
                              <div className="text-sm font-semibold text-slate-900 mb-2">Issues Found</div>
                              <div className="space-y-2">
                                {result.comparison.issues.map((issue: any, i: number) => (
                                  <div key={i} className="text-xs text-slate-700 bg-slate-50 p-2 rounded border border-slate-200">
                                    {typeof issue === 'string' ? issue : JSON.stringify(issue)}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {result.comparison?.details && (
                            <div className="text-xs font-mono bg-slate-50 p-3 rounded border border-slate-200 max-h-24 overflow-auto">
                              <pre>{JSON.stringify(result.comparison.details, null, 2)}</pre>
                            </div>
                          )}
                        </div>
                      )}
                    </CollapsibleSection>
                  </>
                ) : (
                  <div className="bg-slate-50 border border-slate-200 rounded-xl p-8 text-center h-96 flex flex-col items-center justify-center">
                    <div className="w-12 h-12 rounded-full bg-slate-200 flex items-center justify-center mb-4">
                      <ShieldCheck className="w-6 h-6 text-slate-400" />
                    </div>
                    <p className="text-slate-500 text-sm">Validation results will appear here</p>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white mt-12">
        <div className="max-w-7xl mx-auto px-6 py-6 text-center text-sm text-slate-500">
          <p>APL to Python Migration Platform • All data processed by real backend APIs • No mock data</p>
        </div>
      </footer>
    </div>
  );
}

export default App;

