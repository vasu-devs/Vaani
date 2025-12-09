import React, { useState, useEffect } from 'react';
import { Play, Phone, FileText, AlertTriangle, RefreshCw, StopCircle } from 'lucide-react';
import axios from 'axios';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer
} from 'recharts';

// Configure axios base URL
axios.defaults.baseURL = 'http://localhost:8001';

function App() {
    const [phoneNumber, setPhoneNumber] = useState('');
    const [debtAmount, setDebtAmount] = useState('1500');
    const [debtorName, setDebtorName] = useState('John Doe');
    const [agentName, setAgentName] = useState('Rachel');
    const [agentVoice, setAgentVoice] = useState('asteria');
    const [userDetails, setUserDetails] = useState('');
    const [isCalling, setIsCalling] = useState(false);

    const [logs, setLogs] = useState([]);
    const [selectedLog, setSelectedLog] = useState(null);
    const [stats, setStats] = useState({ totalCalls: 0, avgRisk: 0, passRate: 0 });

    // Helper to format date from call_id
    const formatCallIdDate = (callId) => {
        if (!callId) return 'N/A';
        // Match call-YYYYMMDD_HHmmss
        const match = callId.match(/call-(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})/);
        if (!match) return callId;

        const [_, y, m, d, h, min] = match;
        const date = new Date(y, m - 1, d, h, min);
        // Returns "Dec 09, 15:18"
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
        });
    };

    useEffect(() => {
        fetchHistory();
        const interval = setInterval(fetchHistory, 5000);
        return () => clearInterval(interval);
    }, []);

    const fetchHistory = async () => {
        try {
            const res = await axios.get('/api/history');
            setLogs(res.data);

            // Calculate stats
            const total = res.data.length;
            const totalRisk = res.data.reduce((acc, log) => acc + (log.risk_score || 0), 0);

            // Calculate Pass Rate (PTP or Callback)
            const passed = res.data.filter(l => l.call_outcome === 'PTP' || l.call_outcome === 'Callback_Requested').length;

            setStats({
                totalCalls: total,
                avgRisk: total ? (totalRisk / total).toFixed(1) : 0,
                passRate: total ? Math.round((passed / total) * 100) + '%' : '0%'
            });

            // FIX: Auto-update selected log if meaningful data changed (Real-time badges)
            setSelectedLog(prev => {
                if (!prev) return null;
                const freshLog = res.data.find(l => l.id === prev.id);

                if (freshLog) {
                    // Check for changes in Risk, Outcome, or Flags
                    const hasChanged =
                        freshLog.risk_score !== prev.risk_score ||
                        freshLog.call_outcome !== prev.call_outcome ||
                        JSON.stringify(freshLog.legal_flags) !== JSON.stringify(prev.legal_flags) ||
                        freshLog.matrix_quadrant !== prev.matrix_quadrant;

                    if (hasChanged) {
                        return freshLog; // Update view silently
                    }
                }
                return prev; // Keep existing state if no change
            });

        } catch (err) {
            console.error("Failed to fetch history", err);
        }
    };

    const handleCall = async (e) => {
        e.preventDefault();
        setIsCalling(true);
        try {
            await axios.post('/api/call', {
                phone_number: phoneNumber,
                debt_amount: parseInt(debtAmount),
                debtor_name: debtorName,
                agent_name: agentName,
                agent_voice: agentVoice,
                user_details: userDetails
            });
            alert(`Calling ${phoneNumber} as ${agentName}... Check logs shortly.`);
        } catch (err) {
            alert("Failed to trigger call: " + err.message);
        } finally {
            setIsCalling(false);
        }
    };

    const viewLog = async (id) => {
        try {
            const res = await axios.get(`/api/logs/${id}`);
            setSelectedLog(res.data);
        } catch (err) {
            console.error(err);
        }
    };

    return (
        <div className="flex h-screen bg-[#F3F4F6] text-gray-900 font-sans p-4 gap-4 overflow-hidden selection:bg-black/10">

            <div className="w-96 bg-white rounded-[2rem] shadow-sm p-8 flex flex-col h-full border border-white/50">
                <div className="flex items-center gap-3 mb-10 text-gray-900">
                    <svg className="w-10 h-10" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" fill="none" aria-label="Vaani Logo">
                        <g fill="currentColor">
                            <rect x="10" y="20" width="8" height="60" rx="1" />
                            <rect x="22" y="30" width="8" height="40" rx="1" />
                            <rect x="34" y="40" width="8" height="20" rx="1" />

                            <rect x="58" y="40" width="8" height="20" rx="1" />
                            <rect x="70" y="30" width="8" height="40" rx="1" />
                            <rect x="82" y="20" width="8" height="60" rx="1" />
                        </g>
                        <rect x="42" y="48" width="16" height="4" fill="currentColor" opacity="0.5" />
                    </svg>
                    <h1 className="text-3xl font-extrabold tracking-tight">Vaani</h1>
                </div>

                <div className="mb-8">
                    <h2 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-6">Configuration</h2>
                    <form onSubmit={handleCall} className="space-y-5">
                        <div className="space-y-1">
                            <label className="text-xs font-bold text-gray-500 ml-1">TARGET NUMBER</label>
                            <input
                                type="text"
                                value={phoneNumber}
                                onChange={(e) => setPhoneNumber(e.target.value)}
                                placeholder="+15550000000"
                                className="w-full p-4 bg-gray-50 rounded-2xl text-gray-900 font-medium placeholder-gray-400 focus:bg-white focus:ring-2 focus:ring-black/5 transition-all outline-none"
                                required
                            />
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1">
                                <label className="text-xs font-bold text-gray-500 ml-1">AMOUNT</label>
                                <input
                                    type="number"
                                    value={debtAmount}
                                    onChange={(e) => setDebtAmount(e.target.value)}
                                    className="w-full p-4 bg-gray-50 rounded-2xl text-gray-900 font-medium outline-none focus:bg-white focus:ring-2 focus:ring-black/5 transition-all"
                                />
                            </div>
                            <div className="space-y-1">
                                <label className="text-xs font-bold text-gray-500 ml-1">NAME</label>
                                <input
                                    type="text"
                                    value={debtorName}
                                    onChange={(e) => setDebtorName(e.target.value)}
                                    className="w-full p-4 bg-gray-50 rounded-2xl text-gray-900 font-medium outline-none focus:bg-white focus:ring-2 focus:ring-black/5 transition-all"
                                />
                            </div>
                        </div>

                        <div className="pt-2 space-y-5">
                            <div className="space-y-1">
                                <label className="text-xs font-bold text-gray-500 ml-1">AGENT PERONA</label>
                                <div className="grid grid-cols-2 gap-2">
                                    <input
                                        type="text"
                                        value={agentName}
                                        onChange={(e) => setAgentName(e.target.value)}
                                        placeholder="Name"
                                        className="w-full p-3 bg-gray-50 rounded-xl text-sm font-medium outline-none"
                                    />
                                    <select
                                        value={agentVoice}
                                        onChange={(e) => setAgentVoice(e.target.value)}
                                        className="w-full p-3 bg-gray-50 rounded-xl text-sm font-medium outline-none appearance-none"
                                    >
                                        <option value="asteria">Asteria (F)</option>
                                        <option value="luna">Luna (F)</option>
                                        <option value="orion">Orion (M)</option>
                                        <option value="arcas">Arcas (M)</option>
                                    </select>
                                </div>
                            </div>
                            <div className="space-y-1">
                                <label className="text-xs font-bold text-gray-500 ml-1">CONTEXT</label>
                                <textarea
                                    value={userDetails}
                                    onChange={(e) => setUserDetails(e.target.value)}
                                    placeholder="Add context..."
                                    className="w-full p-4 bg-gray-50 rounded-2xl text-sm font-medium outline-none h-24 resize-none transition-all focus:bg-white focus:ring-2 focus:ring-black/5"
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={isCalling}
                            className={`w-full flex items-center justify-center gap-2 text-white font-bold text-lg py-4 rounded-full transition-all m-0 shadow-lg hover:shadow-xl ${isCalling ? 'bg-gray-400' : 'bg-black hover:bg-gray-900 active:scale-[0.98]'}`}
                        >
                            {isCalling ? 'CONNECTING...' : <><Play className="w-5 h-5 fill-current" /> START CALL</>}
                        </button>
                    </form>
                </div>

                <div className="mt-auto">
                    <button className="flex items-center justify-center gap-2 text-xs font-bold text-red-500 hover:text-red-600 hover:bg-red-50 py-3 rounded-xl w-full transition-colors">
                        <StopCircle className="w-4 h-4" /> STOP ALL SYSTEMS
                    </button>
                </div>
            </div>

            {/* Main Layout - Column */}
            <div className="flex-1 flex flex-col gap-4 h-full overflow-hidden">

                {/* 2. Stats Bento Grid */}
                <div className="grid grid-cols-3 gap-4 shrink-0">
                    <div className="bg-white rounded-[2rem] p-8 shadow-sm flex items-center justify-between border border-white/50">
                        <div>
                            <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">RUNS</p>
                            <p className="text-5xl font-extrabold text-gray-900 tracking-tight">{stats.totalCalls}</p>
                        </div>
                        <div className="w-12 h-12 bg-gray-50 rounded-full flex items-center justify-center text-gray-900">
                            <RefreshCw className="w-5 h-5" />
                        </div>
                    </div>
                    <div className="bg-white rounded-[2rem] p-8 shadow-sm flex items-center justify-between border border-white/50">
                        <div>
                            <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">AVG RISK</p>
                            <p className="text-5xl font-extrabold text-gray-900 tracking-tight">{stats.avgRisk}</p>
                        </div>
                        <div className="w-12 h-12 bg-orange-50 rounded-full flex items-center justify-center text-orange-500">
                            <AlertTriangle className="w-5 h-5" />
                        </div>
                    </div>
                    <div className="bg-white rounded-[2rem] p-8 shadow-sm flex items-center justify-between border border-white/50">
                        <div>
                            <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">SUCCESS</p>
                            <p className="text-5xl font-extrabold text-gray-900 tracking-tight">{stats.passRate}</p>
                        </div>
                        <div className="w-12 h-12 bg-green-50 rounded-full flex items-center justify-center text-green-500">
                            <FileText className="w-5 h-5" />
                        </div>
                    </div>
                </div>

                {/* Bottom Section */}
                <div className="flex-1 flex gap-4 overflow-hidden">

                    {/* 3. History List */}
                    <div className="w-96 bg-white rounded-[2rem] shadow-sm p-6 flex flex-col border border-white/50">
                        <h3 className="text-lg font-bold text-gray-900 mb-6 px-2">Recent Calls</h3>
                        <div className="flex-1 overflow-y-auto space-y-2 pr-2">
                            {logs.map(log => (
                                <div
                                    key={log.id}
                                    onClick={() => viewLog(log.id)}
                                    className={`p-4 rounded-2xl cursor-pointer transition-all ${selectedLog?.id === log.id ? 'bg-black text-white shadow-lg' : 'bg-gray-50 hover:bg-gray-100 text-gray-900'}`}
                                >
                                    <div className="flex justify-between items-center mb-1">
                                        <span className="font-bold text-sm">{log.debtor_name || 'Unknown'}</span>
                                        <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${selectedLog?.id === log.id ? 'bg-white/20 text-white' :
                                            log.risk_score > 50 ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-600'
                                            }`}>
                                            Risk {log.risk_score}
                                        </span>
                                    </div>
                                    <div className={`text-xs font-medium flex justify-between ${selectedLog?.id === log.id ? 'text-gray-400' : 'text-gray-400'}`}>
                                        <span>#{log.id.split('_')[1]}</span>
                                        <span>{formatCallIdDate(log.id)}</span>
                                    </div>
                                </div>
                            ))}
                            {logs.length === 0 && <div className="text-center text-gray-400 mt-10 text-sm font-medium">No calls yet</div>}
                        </div>
                    </div>

                    {/* 4. Terminal / Transcript */}
                    <div className="flex-1 bg-[#111] rounded-[2rem] shadow-2xl flex flex-col overflow-hidden text-gray-300 relative">

                        {/* Dark Header */}
                        <div className="px-8 py-5 border-b border-white/5 bg-[#111] flex justify-between items-center z-10">
                            <div className="flex items-center gap-3">
                                <div className="flex gap-2">
                                    <div className="w-3 h-3 rounded-full bg-red-500/80"></div>
                                    <div className="w-3 h-3 rounded-full bg-yellow-500/80"></div>
                                    <div className="w-3 h-3 rounded-full bg-green-500/80"></div>
                                </div>
                                <span className="ml-4 font-mono text-sm font-medium text-gray-400">
                                    {selectedLog ? `vaani-cli --log ${selectedLog.id}` : "vaani-cli --listen"}
                                </span>
                            </div>
                        </div>

                        {/* Sticky Risk Badges (Dark Mode Style) */}
                        {selectedLog && (
                            <div className="px-8 py-4 bg-[#111]/90 backdrop-blur-sm border-b border-white/5 z-10 flex flex-wrap gap-3 items-center">
                                {selectedLog.risk_score > 85 && (
                                    <span className="px-4 py-1.5 rounded-full text-xs font-bold bg-red-500 text-white animate-pulse shadow-red-500/20 shadow-lg">
                                        CRITICAL RISK
                                    </span>
                                )}
                                {selectedLog.legal_flags?.bankruptcy_risk && (
                                    <span className="px-3 py-1 rounded-full text-xs font-bold bg-white/10 text-red-400 border border-white/5">
                                        BANKRUPTCY
                                    </span>
                                )}
                                {selectedLog.legal_flags?.attorney_represented && (
                                    <span className="px-3 py-1 rounded-full text-xs font-bold bg-white/10 text-orange-400 border border-white/5">
                                        ATTORNEY REP
                                    </span>
                                )}
                                <span className={`px-3 py-1 rounded-full text-xs font-bold bg-white/10 border border-white/5 ${selectedLog.call_outcome === 'PTP' ? 'text-green-400' :
                                    selectedLog.call_outcome === 'Refusal' ? 'text-red-400' : 'text-gray-300'
                                    }`}>
                                    {selectedLog.call_outcome || 'Pending'}
                                </span>
                                <span className="px-3 py-1 rounded-full text-xs font-bold bg-white/5 text-blue-400 border border-white/5">
                                    {selectedLog.matrix_quadrant || 'Analysing...'}
                                </span>
                            </div>
                        )}

                        {/* Chat Area */}
                        <div className="flex-1 overflow-y-auto p-8 space-y-6 scrollbar-thin scrollbar-thumb-gray-800 scrollbar-track-transparent">
                            {!selectedLog && (
                                <div className="flex flex-col items-center justify-center h-full text-gray-600 gap-4">
                                    <div className="w-16 h-1 bg-gray-800 rounded-full animate-pulse"></div>
                                    <p className="font-mono text-sm">System Ready. Waiting for dispatch.</p>
                                </div>
                            )}

                            {selectedLog?.transcript?.map((msg, idx) => (
                                <div key={idx} className="flex gap-6 group hover:bg-white/[0.02] -mx-4 px-4 py-2 rounded-xl transition-colors">
                                    <div className={`w-24 text-right font-mono text-xs pt-1 uppercase tracking-wider ${msg.role === 'ChatRole.AGENT' || msg.role === 'assistant' ? 'text-indigo-400' : 'text-emerald-400'}`}>
                                        {msg.speaker || (msg.role === 'ChatRole.AGENT' || msg.role === 'assistant' ? 'AI_AGENT' : 'CUSTOMER')}
                                    </div>
                                    <div className="flex-1 text-gray-300 text-base font-light leading-relaxed">
                                        {msg.content}
                                    </div>
                                </div>
                            ))}

                            {selectedLog && (
                                <div className="mt-12 pt-6 border-t border-white/5 flex justify-between text-xs font-mono text-gray-600">
                                    <span>SESSION_ID: {selectedLog.id}</span>
                                    <span>END_OF_STREAM</span>
                                </div>
                            )}
                        </div>

                    </div>
                </div>
            </div>
        </div>
    )
}

export default App
