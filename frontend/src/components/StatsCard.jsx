import React from 'react';

const StatsCard = ({ title, value, icon: Icon, colorClass, bgClass }) => {
    return (
        <div className="bg-white rounded-[2rem] p-8 shadow-sm flex items-center justify-between border border-white/50">
            <div>
                <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">{title}</p>
                <p className="text-5xl font-extrabold text-gray-900 tracking-tight">{value}</p>
            </div>
            <div className={`w-12 h-12 ${bgClass} rounded-full flex items-center justify-center ${colorClass}`}>
                <Icon className="w-5 h-5" />
            </div>
        </div>
    );
};

export default StatsCard;
