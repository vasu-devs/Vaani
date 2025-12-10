# 🎙️ Vaani (Odeon) - Intelligent Debt Collection Command Center

> **Vaani** (also known as *Odeon*) is a production-grade, voice-native AI platform designed to transform debt collection into an ethical, data-driven, and highly efficient process. By combining **LiveKit's Real-time Transport**, **Groq's Low-Latency Inference**, and **Deepgram's Voice Intelligence**, Vaani enables autonomous negotiation that feels human, compliant, and empathetic.

[![Visualize in MapMyRepo](https://mapmyrepo.vasudev.live/badge.svg)](https://mapmyrepo.vasudev.live/?user=vasu-devs&repo=Vaani)

---

## 🌟 Capabilities & Features

### 🧠 **Conversational Voice Intelligence**
*   **Human-Parity Latency:** Powered by **Groq (Llama 3)** and **Deepgram Nova-2**, ensuring sub-500ms voice-to-voice response times.
*   **Interruptibility:** Full duplex communication allows debtors to interrupt the agent naturally, just like a real phone call.
*   **Dynamic Personas:** Dispatch agents with distinct personalities (e.g., *Rachel: Empathetic*, *Orion: Firm*) and voices (*Asteria, Luna, Arcas*) tailored to the debtor's profile.

### 🕵️ **"Sherlock" Real-Time Risk Engine**
Vaani doesn't just talk; it thinks. The integrated **Sherlock** engine analyzes conversations in real-time to ensure compliance and optimize recovery.
*   **FDCPA Guardrails:** Automatically detects and handles high-risk triggers like **Bankruptcy**, **Attorney Representation**, or **Cease & Desist** requests, flagging them for human review immediately.
*   **Matrix Profiling:** Categorizes debtors into strategic quadrants based on "Willingness" vs. "Ability" to pay:
    *   *Strategic Defaulter* (High Ability, Low Willingness)
    *   *Hardship Case* (Low Ability, High Willingness)
*   **Outcome Prediction:** Instantly tags calls as *Promise to Pay (PTP)*, *Refusal*, or *Dispute*.

### 💻 **The Command Center (Bento UI)**
A modern, react-based dashboard for flight control.
*   **Live Dispatch:** Configure debt amount, debtor details, and agent persona, then dispatch calls via SIP/VoIP.
*   **Terminal Transcript:** Watch the conversation unfold in a hacker-style CLI interface with real-time speaker identification.
*   **Live Risk Badges:** Dynamic pill indicators pop up instantly when risks (e.g., "Bankruptcy Detected") are identified.
*   **Analytics Dashboard:** Track pass rates, average risk scores, and call outcomes over time.

---

## 🏗️ Technical Architecture

Vaani operates on a modular 3-tier architecture designed for scalability and real-time performance.

### 1. **Frontend (Dashboard)**
*   **Framework:** React 18 + Vite
*   **Styling:** Tailwind CSS (Custom "Bento" Design System)
*   **Networking:** Axios (Polling for state/logs)
*   **Visualization:** Recharts (Analytics), Lucide-React (Icons)

### 2. **Backend (Orchestrator)**
*   **Server:** FastAPI (Python)
*   **Role:** Manages the active call list, stores call logs, and serves the API for the frontend.
*   **Database:** JSON-based persistence (File System) for easy portability and demo purposes.

### 3. **AI Voice Worker (The Brain)**
*   **Framework:** [LiveKit Agents](https://github.com/livekit/agents)
*   **LLM:** **Groq** (Llama-3-70b-versatile for Risk, Llama-3-8b-instant for Chat)
*   **STT (Ears):** **Deepgram Nova-2** (8kHz phone optimization)
*   **TTS (Mouth):** **Deepgram Aura** (Low latency specific models)
*   **VAD:** Silero (Voice Activity Detection)

---

## 🚀 Installation & Setup

### Prerequisites
*   **Python 3.10+**
*   **Node.js 18+**
*   **LiveKit Cloud Account** (or local instance)
*   **API Keys:** Groq, Deepgram, LiveKit

### 1. Clone the Repository
```bash
git clone https://github.com/vasu-devs/Vaani.git
cd Vaani
```

### 2. Backend & Agent Setup
The backend and the AI worker run in the same python environment.

```bash
# Create virtual environment
python -m venv venv
# Activate (Windows)
venv\Scripts\activate
# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
# Note: requirements.txt may be minimal, ensure you have all core packages:
pip install livekit-agents livekit-server-sdk livekit-plugins-groq livekit-plugins-deepgram livekit-plugins-silero python-dotenv fastapi uvicorn
```

**Environment Configuration:**
Create a `.env.local` file in the root directory:

```env
# LiveKit Config (from Cloud Project Settings)
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=API_...
LIVEKIT_API_SECRET=Secret_...

# AI Models
GROQ_API_KEY=gsk_...
DEEPGRAM_API_KEY=...
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

---

## 🏃‍♂️ Usage Guide

Running Vaani requires **three** concurrent terminal processes.

### Terminal 1: API Server
Starts the FastAPI backend to handle frontend requests and store logs.
```bash
# From root directory
python run_server.py
```
*   *Local URL:* `http://localhost:8001`
*   *Docs:* `http://localhost:8001/docs`

### Terminal 2: AI Worker
Connects to LiveKit and waits for a room (call) to start.
```bash
# From root directory
python run_agent.py dev
```
*   *Status:* Should see `Connected to LiveKit` and `Waiting for job...`

### Terminal 3: Frontend
Launches the Command Center UI.
```bash
# From frontend/ directory
npm run dev
```
*   *Local URL:* `http://localhost:5173`

---

## 🎮 Workflow Demo

1.  **Launch:** Open the frontend at `localhost:5173`.
2.  **Config:** Enter the target phone number (SIP URI or PSTN if configured) and the debt amount.
3.  **Dispatch:** Click **"START CALL"**.
    *   *Behind the scenes:* The frontend calls the API -> API creates a token -> LiveKit triggers the Agent -> Agent dials out (or waits for join).
4.  **Visualize:**
    *   Observe the **Transcript** printing in real-time.
    *   See **Risk Badges** appear (e.g., if you say "I'm bankrupt").
    *   Watch the **Call Outcome** update automatically when the call ends.

---

## ⚠️ Troubleshooting

| Issue | Solution |
| :--- | :--- |
| **Connection Refused (Frontend)** | Ensure `run_server.py` is running on port 8001. |
| **Agent Not Joining** | Check `.env.local` credentials. Ensure you are running `python run_agent.py dev`. |
| **Import Error: fasting/uvicorn** | Run the detailed pip install command in the Setup section above. |
| **No Audio** | Check your Deepgram API key credits and ensure your mic is enabled if testing locally. |

---

**Built with 🖤 by Vasudev.**
