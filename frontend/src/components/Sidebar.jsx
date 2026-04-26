import React from 'react';
import { Play, StopCircle } from 'lucide-react';

const Sidebar = ({
    phoneNumber, setPhoneNumber,
    debtAmount, setDebtAmount,
    debtorName, setDebtorName,
    agentName, setAgentName,
    agentVoice, setAgentVoice,
    userDetails, setUserDetails,
    isCalling, handleCall
}) => {
    return (
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
                            <label className="text-xs font-bold text-gray-500 ml-1">AGENT PERSONA</label>
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
                <button
                    onClick={() => {
                        if (window.confirm('Are you sure you want to reset all systems?')) {
                            window.location.reload();
                        }
                    }}
                    className="flex items-center justify-center gap-2 text-xs font-bold text-red-500 hover:text-red-600 hover:bg-red-50 py-3 rounded-xl w-full transition-colors"
                >
                    <StopCircle className="w-4 h-4" /> STOP ALL SYSTEMS
                </button>
            </div>
        </div>
    );
};

export default Sidebar;
