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
            setStats({
                totalCalls: total,
                avgRisk: total ? (totalRisk / total).toFixed(1) : 0,
                passRate: 'N/A'
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
        <div className="flex h-screen bg-gray-100 text-gray-900 font-sans">
            {/* Sidebar / Configuration */}
            <div className="w-1/4 bg-white border-r border-gray-200 p-6 flex flex-col">
                <div className="flex items-center gap-2 mb-8 text-indigo-600">
                    <Phone className="w-8 h-8" />
                    <h1 className="text-2xl font-bold tracking-tight">Vaani</h1>
                </div>

                <div className="mb-8">
                    <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4">Configuration</h2>
                    <form onSubmit={handleCall} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Target Number</label>
                            <input
                                type="text"
                                value={phoneNumber}
                                onChange={(e) => setPhoneNumber(e.target.value)}
                                placeholder="+15550000000"
                                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all outline-none"
                                required
                            />
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Amount ($)</label>
                                <input
                                    type="number"
                                    value={debtAmount}
                                    onChange={(e) => setDebtAmount(e.target.value)}
                                    className="w-full p-2 border border-gray-300 rounded-lg outline-none"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                                <input
                                    type="text"
                                    value={debtorName}
                                    onChange={(e) => setDebtorName(e.target.value)}
                                    className="w-full p-2 border border-gray-300 rounded-lg outline-none"
                                />
                            </div>
                        </div>

                        <div className="border-t border-gray-100 my-4 pt-4">
                            <h3 className="text-sm font-semibold text-gray-900 mb-3">Agent Settings</h3>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Agent Name</label>
                                    <input
                                        type="text"
                                        value={agentName}
                                        onChange={(e) => setAgentName(e.target.value)}
                                        className="w-full p-2 border border-gray-300 rounded-lg outline-none"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Agent Voice</label>
                                    <select
                                        value={agentVoice}
                                        onChange={(e) => setAgentVoice(e.target.value)}
                                        className="w-full p-2 border border-gray-300 rounded-lg outline-none bg-white"
                                    >
                                        <option value="asteria">Asteria (Female, US)</option>
                                        <option value="luna">Luna (Female, US)</option>
                                        <option value="orion">Orion (Male, US)</option>
                                        <option value="arc">Arc (Male, US)</option>
                                        <option value="helios">Helios (Male, UK)</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Additional Context / Details</label>
                                    <textarea
                                        value={userDetails}
                                        onChange={(e) => setUserDetails(e.target.value)}
                                        placeholder="E.g. User lost job recently, be empathetic..."
                                        className="w-full p-2 border border-gray-300 rounded-lg outline-none h-24 text-sm"
                                    />
                                </div>
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={isCalling}
                            className={`w-full flex items-center justify-center gap-2 text-white font-medium py-3 rounded-lg transition-all ${isCalling ? 'bg-gray-400' : 'bg-indigo-600 hover:bg-indigo-700 shadow-md'}`}
                        >
                            {isCalling ? 'Starting...' : <><Play className="w-4 h-4" /> Start Outbound Call</>}
                        </button>
                    </form>
                </div>

                <div className="mt-auto">
                    <button className="flex items-center gap-2 text-sm text-gray-500 hover:text-red-600 transition-colors">
                        <StopCircle className="w-4 h-4" /> Stop All Agents
                    </button>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex flex-col p-8 overflow-hidden">

                {/* Top Cards */}
                <div className="grid grid-cols-3 gap-6 mb-8">
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-500 font-medium">TOTAL RUNS</p>
                            <p className="text-3xl font-bold text-gray-900 mt-1">{stats.totalCalls}</p>
                        </div>
                        <div className="p-3 bg-indigo-50 rounded-lg">
                            <RefreshCw className="w-6 h-6 text-indigo-600" />
                        </div>
                    </div>
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-500 font-medium">AVG RISK SCORE</p>
                            <p className="text-3xl font-bold text-gray-900 mt-1">{stats.avgRisk}<span className="text-sm text-gray-400 font-normal">/100</span></p>
                        </div>
                        <div className="p-3 bg-orange-50 rounded-lg">
                            <AlertTriangle className="w-6 h-6 text-orange-600" />
                        </div>
                    </div>
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-500 font-medium">PASS RATE</p>
                            <p className="text-3xl font-bold text-gray-900 mt-1">{stats.passRate}</p>
                        </div>
                        <div className="p-3 bg-green-50 rounded-lg">
                            <FileText className="w-6 h-6 text-green-600" />
                        </div>
                    </div>
                </div>

                {/* Content Area */}
                <div className="flex-1 flex gap-6 overflow-hidden">

                    {/* History List */}
                    <div className="w-1/3 bg-white rounded-xl shadow-sm border border-gray-100 flex flex-col overflow-hidden">
                        <div className="p-4 border-b border-gray-100 flex justify-between items-center bg-gray-50">
                            <h3 className="font-semibold text-gray-700">Call History</h3>
                            <span className="text-xs bg-white border px-2 py-1 rounded text-gray-500">{logs.length} records</span>
                        </div>
                        <div className="flex-1 overflow-y-auto p-2 space-y-2">
                            {logs.map(log => (
                                <div
                                    key={log.id}
                                    onClick={() => viewLog(log.id)}
                                    className={`p-4 rounded-lg cursor-pointer border transition-all hover:shadow-md ${selectedLog?.id === log.id ? 'bg-indigo-50 border-indigo-200 ring-1 ring-indigo-200' : 'bg-white border-gray-100 hover:border-gray-300'}`}
                                >
                                    <div className="flex justify-between items-start mb-2">
                                        <span className="font-medium text-gray-900 text-sm">John Doe</span>
                                        <span className={`text-xs px-2 py-0.5 rounded-full ${log.risk_score > 50 ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
                                            Risk: {log.risk_score}
                                        </span>
                                    </div>
                                    <div className="text-xs text-gray-500 flex justify-between">
                                        <span>{log.id}</span>
                                        <span>{new Date(log.timestamp.replace('_', ' ').replace(/(\d{8}) (\d{6})/, '$1 $2')).toLocaleTimeString()}</span>
                                    </div>
                                </div>
                            ))}
                            {logs.length === 0 && <div className="p-8 text-center text-gray-400 text-sm">No calls recorded yet.</div>}
                        </div>
                    </div>

                    {/* Logs Viewer */}
                    <div className="flex-1 bg-gray-900 rounded-xl shadow-lg border border-gray-800 flex flex-col overflow-hidden text-gray-300 font-mono text-sm">
                        <div className="p-4 border-b border-gray-800 flex justify-between items-center bg-gray-800/50">
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full bg-red-500"></div>
                                <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                                <div className="w-3 h-3 rounded-full bg-green-500"></div>
                                <span className="ml-4 font-semibold text-gray-200">
                                    {selectedLog ? `Transcript: ${selectedLog.id}` : "Real-time Logs"}
                                </span>
                            </div>
                        </div>

                        <div className="flex-1 overflow-y-auto p-6 space-y-4">
                            {!selectedLog && (
                                <div className="text-gray-500 italic text-center mt-20">Select a call to view transcript...</div>
                            )}

                            {selectedLog?.transcript?.map((msg, idx) => (
                                <div key={idx} className="flex gap-4">
                                    <div className={`min-w-[80px] font-bold text-right ${msg.role === 'ChatRole.AGENT' || msg.role === 'assistant' ? 'text-blue-400' : 'text-green-400'}`}>
                                        {msg.role === 'ChatRole.AGENT' || msg.role === 'assistant' ? '[Agent]' : '[Defaulter]'}
                                    </div>
                                    <div className="text-gray-300">
                                        {msg.content}
                                    </div>
                                </div>
                            ))}

                            {selectedLog && (
                                <div className="mt-8 border-t border-gray-800 pt-4 text-xs text-gray-500">
                                    End of Log. Final Risk Score: {selectedLog.risk_score}
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
