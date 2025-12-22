import React from 'react';

const LogTerminal = ({ selectedLog }) => {
    return (
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
                    {selectedLog.call_outcome && (
                        <span className={`px-3 py-1 rounded-full text-xs font-bold bg-white/10 border border-white/5 ${selectedLog.call_outcome === 'PTP' ? 'text-green-400' :
                            selectedLog.call_outcome === 'Refusal' ? 'text-red-400' : 'text-gray-300'
                            }`}>
                            {selectedLog.call_outcome}
                        </span>
                    )}
                    {selectedLog.matrix_quadrant && (
                        <span className="px-3 py-1 rounded-full text-xs font-bold bg-white/5 text-blue-400 border border-white/5">
                            {selectedLog.matrix_quadrant}
                        </span>
                    )}
                </div>
            )}

            {/* Chat Area */}
            <div className="flex-1 overflow-y-auto p-8 space-y-6 scrollbar-dark">
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
    );
};

export default LogTerminal;
