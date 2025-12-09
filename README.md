# 🎙️ Vaani - AI Debt Collection Command Center

> **Vaani** is a next-generation, voice-native AI platform designed for ethical, compliant, and efficient debt collection. It combines real-time conversational AI, risk analysis, and a modern "Bento-style" command center to revolutionize how financial recovery is managed.

![Vaani Dashboard](frontend/public/favicon.svg) 
*(Note: Replace with actual screenshot)*

---

## 🌟 Key Features

### 🧠 **Intelligent Voice Agents**
*   **Human-like Conversation:** Powered by **LiveKit Agents** and **Groq (Llama 3)**, Vaani agents negotiate naturally, handle interruptions, and adapt to user sentiment.
*   **Low Latency:** Uses **Deepgram Nova-2** for lightning-fast Speech-to-Text (STT) and Aura for Text-to-Speech (TTS).
*   **Configurable Personas:** Dispatch agents with different voices (Asteria, Orion) and strategies tailored to specific debtors.

### 🛡️ **Real-time Risk & Compliance ("Sherlock")**
*   **Live Analysis:** Every conversation is analyzed in real-time for compliance risks.
*   **FDCPA Guardrails:** Automatically detects **Bankruptcy** mentions, **Attorney Representation**, or **Cease & Desist** requests.
*   **Debtor Profiling:** Categorizes debtors into quadrants (e.g., *Strategic Defaulter*, *Hardship Case*) to suggest better recovery strategies.

### 💻 **Modern Command Center (Bento UI)**
*   **Visual Dispatch:** a clean, minimalist dashboard to configure and launch calls.
*   **Live Transcripts:** Watch the conversation unfold in a "Terminal-style" dark mode interface.
*   **Risk Badges:** Dynamic pill indicators show call outcome (PTP - Promise to Pay, Refusal) and risk scores instantly.
*   **History & Analytics:** Track total runs, pass rates, and average risk scores over time.

---

## 🏗️ Architecture & Tech Stack

Vaani is built as a modular application with three clear layers:

### 1. **Frontend (The Command Center)**
*   **Framework:** React + Vite
*   **Styling:** Tailwind CSS (Custom "Modern Minimalist" / Bento Design System)
*   **State:** Real-time polling via Axios
*   **Visuals:** Recharts (Analytics), Lucide-React (Icons)

### 2. **Backend (API & State Management)**
*   **Server:** FastAPI (Python)
*   **Endpoints:** 
    *   `/api/call`: Dispatches the AI agent.
    *   `/api/history`: Retrieves call logs and risk artifacts.
*   **Storage:** Local JSON-based persistence (for portability/demo).

### 3. **AI Voice Server (The "Brain")**
*   **Framework:** LiveKit Agents
*   **LLM:** Groq (Llama-3-8b-instant / 70b)
*   **Transcriber:** Deepgram API
*   **Synthesizer:** Deepgram Aura
*   **VAD:** Silero VAD (Voice Activity Detection)

---

## 🚀 Getting Started

Follow these steps to set up Vaani from scratch.

### 📋 Prerequisites
*   **Python 3.10+**
*   **Node.js 18+** & `npm`
*   **LiveKit Server** (Local or Cloud project)
*   **API Keys** for:
    *   [LiveKit Cloud](https://cloud.livekit.io/) (URL, API Key, Secret)
    *   [Groq](https://console.groq.com/) (API Key)
    *   [Deepgram](https://console.deepgram.com/) (API Key)

---

### ⚙️ Installation

#### 1. Clone the Repository
```bash
git clone https://github.com/your-username/vaani.git
cd vaani
```

#### 2. Backend & Agent Setup
Create a virtual environment and install dependencies.

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Configuration:**
Create a `.env.local` file in the root directory:

```env
# LiveKit Configuration
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret

# AI Models
GROQ_API_KEY=gsk_...
DEEPGRAM_API_KEY=...

# App Settings
PHONENUMBER=... (Optional default)
```

#### 3. Frontend Setup
Navigate to the frontend directory and install packages.

```bash
cd frontend
npm install
```

---

## 🏃‍♂️ Running the Application

You will need **three** separate terminal windows to run the full stack.

### Terminal 1: The SIP/API Server (Backend)
This handles the API requests from the frontend and manages the call state.
```bash
# In root directory
python run_server.py
```
*Runs on: http://localhost:8001*

### Terminal 2: The Voice Agent worker
This connects to LiveKit and waits for a room to be created (which happens when you click "Start Call").
```bash
# In root directory
python run_agent.py dev
```

### Terminal 3: The Frontend Dashboard
```bash
# In /frontend directory
npm run dev
```
*Runs on: http://localhost:5173* (usually)

---

## 🎮 Usage Guide

1.  **Open the Dashboard:** Go to your frontend URL (e.g., `http://localhost:5173`).
2.  **Configure a Call:**
    *   **Target Number:** Enter the phone number (with country code, e.g., `+1...`) or SIP URI.
    *   **Amount:** The debt value to collect.
    *   **Persona:** Choose an Agent (e.g., "Rachel") and Voice (e.g., "Asteria").
    *   **Context:** Add specific notes (e.g., "Debtor lost job recently").
3.  **Dispatch:** Click the black **"START CALL"** button.
4.  **Monitor:**
    *   The "Terminal" card on the right will show the **Live Transcript**.
    *   Watch the **Risk Badges** appear in real-time as the AI analyzes the user's intent.
    *   The **Stats Grid** will update automatically after the call.

---

## 📂 Project Structure

```
vaani/
├── app/
│   ├── api/            # FastAPI routes (server.py)
│   ├── services/       # Core Logic
│   │   ├── risk_analysis.py  # "Sherlock" Risk Engine
│   │   └── voice_agent.py    # LiveKit Agent Definition
│   └── state/          # JSON file handling (simple DB)
├── frontend/           # React Application
│   ├── src/
│   │   └── App.jsx     # Main Dashboard UI
│   └── public/         # Static assets (Favicon)
├── call_logs/          # Stored JSON logs of calls
├── run_server.py       # Entry point for API
├── run_agent.py        # Entry point for Agent
└── requirements.txt    # Python Dependencies
```

---

## ⚠️ Troubleshooting

*   **"Connection Refused"**: Ensure the backend server is running on port 8001.
*   **"Agent not joining"**: Check your LiveKit credentials in `.env.local` and ensure `run_agent.py` shows "Connected to LiveKit".
*   **"No Audio"**: If testing cleanly, ensure your machine's microphone permissions are allowed for the browser or SIP client.

---

**Vaani** — *Redefining Debt Recovery with Empathy & Intelligence.*
