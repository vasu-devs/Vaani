export const formatCallIdDate = (callId) => {
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
