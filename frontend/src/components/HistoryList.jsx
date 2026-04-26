import React from 'react';
import { formatCallIdDate } from '../utils';

const HistoryList = ({ logs, viewLog, selectedLog }) => {
    return (
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
                        <div className="text-xs font-medium flex justify-between text-gray-400">
                            <span>#{log.id?.split('_')[1] || log.id}</span>
                            <span>{formatCallIdDate(log.id)}</span>
                        </div>
                    </div>
                ))}
                {logs.length === 0 && <div className="text-center text-gray-400 mt-10 text-sm font-medium">No calls yet</div>}
            </div>
        </div>
    );
};

export default HistoryList;
