# MindCare AI 🧠💙
> **Compassionate AI Mental Health Support & Clinical Psychoeducation Companion**

MindCare AI is an evidence-based mental health platform designed to provide real-time emotional validation, psychological root-cause analysis, and practical therapeutic coping strategies (CBT, DBT, Schema Therapy, and Mindfulness).

Integrated with the *Psychologie et Sérénité* clinical ontology (53 concepts, 100 clinical articles), MindCare AI grounds every conversation in peer-reviewed psychological science.

---

## ✨ Key Features

- **⚡ Real-Time SSE Token Streaming**: Server-Sent Events (SSE) streaming ensures instantaneous Time-to-First-Token (TTFT) with zero waiting.
- **📚 Evidence-Based Psychological RAG**: Analyzes the user's struggle and retrieves relevant clinical concepts (e.g. Clark & Wells Model, Cognitive Distortions, Attachment Theory) and peer-reviewed articles.
- **🛡️ 5-Pillar Therapeutic Response**:
  1. *Empathetic Validation & Safe Space*
  2. *Psychological Insight & Root Cause Analysis*
  3. *Step-by-Step Coping Exercises (CBT / Grounding / Behavioral Activation)*
  4. *Clinical Psychology References & Recommended Articles*
  5. *Compassionate Follow-Up*
- **🔄 Multi-Model Failover Pool**: Resilient, zero-downtime model routing (`gemini-3-flash-preview` → `gemini-flash-lite-latest` → `gemini-3.5-flash-lite`).
- **📊 3.5ms Local Mood Analysis**: High-speed, zero-quota emotion classifier preserving 100% of API limits for conversations.
- **🔒 Privacy & Safety First**: Real-time crisis detection routing to emergency hotlines (iCall India 9152987821 / USA 988).

---

## 🚀 Quickstart & Setup

### 1. Clone & Navigate
```bash
git clone https://github.com/Navilkanth/mindcare-AI.git
cd mindcare-AI
```

### 2. Virtual Environment & Dependencies
```bash
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Mac / Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Add your free Google Gemini API key from [Google AI Studio](https://aistudio.google.com/):
```env
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_MODEL=gemini-3-flash-preview
MAX_TOKENS=1500
TEMPERATURE=0.7
REQUEST_TIMEOUT=45
```

### 4. Run Locally
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.
API documentation is available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

---

## ☁️ Deployment on Vercel

This repository includes a production `vercel.json` configured for serverless Python deployment:
1. Push to your GitHub repository:
   ```bash
   git push -u origin main
   ```
2. Import the repository on [Vercel](https://vercel.com/).
3. In **Settings > Environment Variables**, add:
   - `GEMINI_API_KEY`: Your Gemini API key.
   - `OPENAI_MODEL`: `gemini-3-flash-preview`.
4. Deploy!

---

## 📁 Architecture Overview
```text
mindcare-ai/
├── agent/
│   ├── core.py             # Multi-model streaming engine & failover
│   ├── psych_kb.py         # Clinical concept & article retriever
│   ├── prompts.py          # 5-Pillar therapeutic system prompts
│   ├── lc_memory.py        # Sliding-window session memory
│   └── safety.py           # Crisis keyword detector
├── api/
│   └── routes/             # chat, mood, history endpoints
├── config/
│   └── settings.py         # App configuration & model parameters
├── data/
│   ├── psychology_knowledge.json  # 53 clinical concepts, 100 articles
│   └── database.py         # SQLite WAL high-concurrency layer
├── external/
│   └── psychologie.py      # Client for psychologieetserenite.com API
├── frontend/
│   ├── index.html          # Landing page
│   ├── chat.html           # Real-time chat interface
│   ├── css/style.css       # Glassmorphism dark UI & rich markdown styling
│   └── js/app.js           # 60fps SSE token rendering & session control
├── main.py                 # FastAPI application
├── vercel.json             # Vercel serverless configuration
└── requirements.txt        # Python dependencies
```

---

## 📜 License
MIT License. Clinical ontology attribution: Gildas Garrec (*Psychologie et Sérénité*).
