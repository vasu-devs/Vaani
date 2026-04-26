import React, { useState, useEffect, useCallback } from 'react';
import { FileText, AlertTriangle, RefreshCw } from 'lucide-react';
import axios from 'axios';
import Sidebar from './components/Sidebar';
import StatsCard from './components/StatsCard';
import HistoryList from './components/HistoryList';
import LogTerminal from './components/LogTerminal';

// Configure axios base URL — reads from env with fallback
axios.defaults.baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

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
    const [stats, setStats] = useState({ totalCalls: 0, avgRisk: 0, passRate: '0%' });

    const fetchHistory = useCallback(async () => {
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

            // Auto-update selected log if meaningful data changed (Real-time badges)
            setSelectedLog(prev => {
                if (!prev) return null;
                const freshLog = res.data.find(l => l.id === prev.id);

                if (freshLog) {
                    const hasChanged =
                        freshLog.risk_score !== prev.risk_score ||
                        freshLog.call_outcome !== prev.call_outcome ||
                        JSON.stringify(freshLog.legal_flags) !== JSON.stringify(prev.legal_flags) ||
                        freshLog.matrix_quadrant !== prev.matrix_quadrant;

                    if (hasChanged) {
                        return freshLog;
                    }
                }
                return prev;
            });

        } catch (err) {
            console.error("Failed to fetch history", err);
        }
    }, []);

    useEffect(() => {
        fetchHistory();
        const interval = setInterval(fetchHistory, 5000);
        return () => clearInterval(interval);
    }, [fetchHistory]);

    const handleCall = useCallback(async (e) => {
        e.preventDefault();

        const parsedAmount = parseFloat(debtAmount);
        if (Number.isNaN(parsedAmount) || parsedAmount <= 0) {
            alert("Please enter a valid debt amount.");
            return;
        }

        setIsCalling(true);
        try {
            await axios.post('/api/call', {
                phone_number: phoneNumber,
                debt_amount: parsedAmount,
                debtor_name: debtorName,
                agent_name: agentName,
                agent_voice: agentVoice,
                user_details: userDetails
            });
            alert(`Calling ${phoneNumber} as ${agentName}... Check logs shortly.`);
        } catch (err) {
            const detail = err.response?.data?.detail;
            alert("Failed to trigger call: " + (detail || err.message));
        } finally {
            setIsCalling(false);
        }
    }, [phoneNumber, debtAmount, debtorName, agentName, agentVoice, userDetails]);

    const viewLog = useCallback(async (id) => {
        try {
            const res = await axios.get(`/api/logs/${id}`);
            const data = res.data;

            // Flatten risk_analysis fields to top level for LogTerminal compatibility
            if (data.risk_analysis) {
                const ra = data.risk_analysis;
                data.call_outcome = data.call_outcome || ra.call_outcome;
                data.legal_flags = data.legal_flags || ra.legal_flags;
                data.matrix_quadrant = data.matrix_quadrant || ra.matrix_quadrant;
                data.risk_score = data.risk_score ?? ra.risk_score;
            }

            setSelectedLog(data);
        } catch (err) {
            console.error("Failed to load log:", err);
        }
    }, []);

    return (
        <div className="flex h-screen bg-[#F3F4F6] text-gray-900 font-sans p-4 gap-4 overflow-hidden selection:bg-black/10">

            {/* 1. Floating Sidebar Card */}
            <Sidebar
                phoneNumber={phoneNumber} setPhoneNumber={setPhoneNumber}
                debtAmount={debtAmount} setDebtAmount={setDebtAmount}
                debtorName={debtorName} setDebtorName={setDebtorName}
                agentName={agentName} setAgentName={setAgentName}
                agentVoice={agentVoice} setAgentVoice={setAgentVoice}
                userDetails={userDetails} setUserDetails={setUserDetails}
                isCalling={isCalling} handleCall={handleCall}
            />

            {/* Main Layout - Column */}
            <div className="flex-1 flex flex-col gap-4 h-full overflow-hidden">

                {/* 2. Stats Bento Grid */}
                <div className="grid grid-cols-3 gap-4 shrink-0">
                    <StatsCard
                        title="RUNS"
                        value={stats.totalCalls}
                        icon={RefreshCw}
                        bgClass="bg-gray-50"
                        colorClass="text-gray-900"
                    />
                    <StatsCard
                        title="AVG RISK"
                        value={stats.avgRisk}
                        icon={AlertTriangle}
                        bgClass="bg-orange-50"
                        colorClass="text-orange-500"
                    />
                    <StatsCard
                        title="SUCCESS"
                        value={stats.passRate}
                        icon={FileText}
                        bgClass="bg-green-50"
                        colorClass="text-green-500"
                    />
                </div>

                {/* Bottom Section */}
                <div className="flex-1 flex gap-4 overflow-hidden">

                    {/* 3. History List */}
                    <HistoryList
                        logs={logs}
                        viewLog={viewLog}
                        selectedLog={selectedLog}
                    />

                    {/* 4. Terminal / Transcript */}
                    <LogTerminal
                        selectedLog={selectedLog}
                    />
                </div>
            </div>
        </div>
    );
}

export default App;
