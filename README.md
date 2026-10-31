<div align="center">

# ConceptIQ (JARVIS AI Tutor)

**A Universal Adaptive Learning Platform & Personal AI Professor**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![React 19](https://img.shields.io/badge/React-19.0+-61DAFB.svg?style=flat&logo=react)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6.svg?style=flat&logo=typescript)](https://www.typescriptlang.org/)
[![Tailwind CSS v4](https://img.shields.io/badge/Tailwind-v4-38B2AC.svg?style=flat&logo=tailwind-css)](https://tailwindcss.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-8.0+-47A248.svg?style=flat&logo=mongodb)](https://www.mongodb.com/)
[![Google Gemini](https://img.shields.io/badge/Google_Gemini-2.5_Flash_/_Lite-4285F4.svg?style=flat&logo=google)](https://ai.google.dev/)
[![Wispr Flow](https://img.shields.io/badge/Speech-Wispr_Flow_Dictation-8B5CF6.svg?style=flat)](https://wisprflow.ai/)
[![Test Coverage](https://img.shields.io/badge/Tests-61%2F61_Passing_(100%25)-brightgreen.svg?style=flat)](#testing--verification)

*An adaptive AI tutor that understands how you think, diagnoses what you misunderstand, and continuously adapts to how you learn.*

---

</div>

## Overview

**ConceptIQ** is an intelligent AI tutoring system and adaptive knowledge engine. It moves beyond conventional chatbot wrappers and static quiz platforms by pairing a **real-time streaming JARVIS-inspired neural HUD** with a mathematically rigorous cognitive architecture:

1. **Deterministic Mastery Modeling**: Uses **Bayesian Knowledge Tracing (BKT)** to track true student mastery ($P(L)$) through pure binary observations. The LLM diagnoses reasoning, but *never* manipulates student mastery or correctness scores arbitrarily.
2. **Adaptive Topological Curriculum (DAG)**: Validated topological sort ensuring students never encounter concepts whose foundational prerequisites remain unmastered.
3. **Automated Misconception Classification**: Diagnoses student thinking, reasoning errors, and speech transcripts (e.g. Wispr Flow voice dictation) to detect nuanced mental models (like the *Byte Increment Fallacy* in pointer arithmetic).
4. **Ebbinghaus Spaced Repetition**: Implements a modified 5-box **Leitner Scheduler** with timestamp-aware urgency tracking to schedule timely reviews before decay occurs.
5. **Progressive SSE Token Streaming**: Streams educational derivations, intuitive analogies, LaTeX mathematical equations, and interactive C/Python code snippets in real time over Server-Sent Events.

---

## Key Capabilities

### 1. Universal Tutoring Architecture
- **Subject-Agnostic Academic Hierarchy**: `Subject` $\rightarrow$ `Topic` $\rightarrow$ `Concept` with single-ownership rules and strict cross-subject prerequisite boundary enforcement.
- **Five Interaction Modes**:
  - **`DOUBT`**: Instant, focused doubt resolution without mutating BKT states.
  - **`EXPLAIN`**: Multi-tiered explanations (analogy $\rightarrow$ formal definition $\rightarrow$ concrete code/math $\rightarrow$ pitfalls).
  - **`TEACH`**: Step-by-step guided instruction advancing along the learner's frontier.
  - **`PRACTICE`**: Formal diagnostic assessments triggering BKT Bayesian updates and Leitner advancement.
  - **`ANALYZE`**: Detailed post-attempt breakdown identifying verified vs candidate misconceptions.

### 2. High-Performance JARVIS Neural Interface
- **Restrained HUD Design**: Minimal dark graphite canvas (`#06080A`), cyan illumination (`#00D9FF`), fine technical typography, and rotating segmented arcs.
- **State-Driven Neural Core**:
  - `IDLE`: Subtle ambient orbital drift.
  - `LISTENING`: Gentle pulse responding to student speech/input.
  - `THINKING`: Rapid progressive neural node excitation while synthesizing answers.
  - `RESPONDING`: Rhythmic cyan transmission during live SSE token streaming.
  - `ERROR`: Restrained warning state with graceful fallback.
- **Full KaTeX & Markdown Rendering**: Live rendering of inline and block math (`\(\int u\,dv = uv - \int v\,du\)`), formatted markdown tables, and syntax-highlighted code blocks with a one-click clipboard copy utility.

### 3. Rigorous Cognitive Backend Invariants
- **Backend Correctness Authority**: The deterministic Python evaluator is the sole authority for question correctness. If an LLM diagnosis contradicts the answer key, the backend evaluator overrides it automatically.
- **Lazy Mastery Initialization**: Student mastery is lazy-initialized on first contact. Unassessed concepts are tracked explicitly as `UNASSESSED`—**never presented as zero knowledge**.
- **No Floating Hallucinations**: Misconceptions proposed by AI are categorized as `CANDIDATE` until backed by repeated evidence count.

---

## Architecture

```
                          ConceptIQ Architecture
 ┌────────────────────────────────────────────────────────────────────────┐
 │                        REACT 19 FRONTEND (Vite)                        │
 │                                                                        │
 │   Minimal Navigation  │  JARVIS Neural Core  │  Educational Renderer   │
 │   (Home/Learn/Ask/    │  (State-driven HUD   │  (KaTeX Math + Code     │
 │    Practice/Progress) │   Radial Reticles)   │   One-Click Copy)       │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │ HTTP / Server-Sent Events (SSE)
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │                         FASTAPI BACKEND ENGINE                         │
 │                                                                        │
 │  ┌───────────────────────┐      ┌───────────────────────────────────┐  │
 │  │ UniversalTutorService │◄────►│  Google Gemini 2.5 Flash / Lite   │  │
 │  │ (Token Streaming SSE) │      │  (with Automatic Model Cascade)   │  │
 │  └───────────────────────┘      └───────────────────────────────────┘  │
 │                                                                        │
 │  ┌───────────────────────┐      ┌───────────────────────────────────┐  │
 │  │   LearningLoopService │◄────►│ AnswerEvaluator + BKTEngine       │  │
 │  │ (Atomic Attempts Loop)│      │ LeitnerScheduler (Box 1 - 5)      │  │
 │  └───────────────────────┘      └───────────────────────────────────┘  │
 │                                                                        │
 │  ┌───────────────────────┐      ┌───────────────────────────────────┐  │
 │  │   QuestionSelector    │◄────►│ ConceptDAGValidator               │  │
 │  │ (Frontier & Remediation)     │ (Kahn's Topological Algorithm)    │  │
 │  └───────────────────────┘      └───────────────────────────────────┘  │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │ PyMongo Repository
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │                      MONGODB LOCAL / ATLAS CLUSTER                     │
 │                                                                        │
 │  • subjects           • topics           • concepts                    │
 │  • concept_prereqs    • misconceptions   • questions                   │
 │  • learners           • concept_mastery  • assessment_sessions         │
 │  • question_attempts                                                   │
 └────────────────────────────────────────────────────────────────────────┘
```

---

## Mathematical Foundations

### 1. Bayesian Knowledge Tracing (BKT)
Mastery is updated on every formal practice submission based strictly on binary observation ($o_t \in \{0, 1\}$):

$$P(L_t \mid \text{obs}) = \begin{cases} 
\dfrac{P(L_{t-1}) \cdot (1 - P(S))}{P(L_{t-1}) \cdot (1 - P(S)) + (1 - P(L_{t-1})) \cdot P(G)}, & \text{if } o_t = 1 \\
\dfrac{P(L_{t-1}) \cdot P(S)}{P(L_{t-1}) \cdot P(S) + (1 - P(L_{t-1})) \cdot (1 - P(G))}, & \text{if } o_t = 0 
\end{cases}$$

Mastery transition is then applied once:

$$P(L_t) = P(L_t \mid \text{obs}) + (1 - P(L_t \mid \text{obs})) \cdot P(T)$$

Where:
- $P(L_0)$: Prior knowledge probability (concept baseline).
- $P(T)$: Transition/learning probability ($0.12 - 0.15$).
- $P(G)$: Guess probability ($0.20$).
- $P(S)$: Slip probability ($0.10 - 0.12$).

### 2. Spaced Repetition (Modified Leitner Engine)
- Correct attempts advance the card to Box $B+1$ (capped at Box 5).
- Incorrect attempts immediately reset the card to Box 1.
- Inter-review intervals:
  - **Box 1**: 24 hours ($2^0$ days)
  - **Box 2**: 72 hours ($3$ days)
  - **Box 3**: 168 hours ($7$ days)
  - **Box 4**: 336 hours ($14$ days)
  - **Box 5**: 720 hours ($30$ days)

---

## Directory Structure

```
ConceptIQ/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── analytics.py       # Class-wide misconception analytics
│   │   │   │   ├── concepts.py        # Curriculum syllabus & DAG edges
│   │   │   │   ├── learners.py        # Profiles, masteries & review schedules
│   │   │   │   ├── questions.py       # Diagnostic question bank
│   │   │   │   ├── sessions.py        # Adaptive sessions & attempt submit
│   │   │   │   └── tutor.py           # SSE Streaming & doubt query endpoints
│   │   │   └── router.py              # Unified API v1 route registry
│   │   ├── core/
│   │   │   ├── config.py              # Environment settings (Pydantic)
│   │   │   ├── database.py            # Database dependency injector
│   │   │   ├── mongo.py               # PyMongo client & unique index setup
│   │   │   └── mongo_repo.py          # Unified MongoDB Data Repository
│   │   ├── domain/
│   │   │   ├── bkt.py                 # Pure mathematical BKT engine
│   │   │   ├── dag.py                 # Kahn's topological sort & validation
│   │   │   ├── evaluator.py           # Deterministic MCQ & NAT evaluator
│   │   │   ├── scheduler.py           # 5-box Leitner Spaced Repetition engine
│   │   │   └── schemas/               # Typed Pydantic request/response schemas
│   │   ├── models/                    # Domain entities & validation definitions
│   │   ├── seed/
│   │   │   ├── c_curriculum_data.py   # Multi-subject academic dataset
│   │   │   └── seed_mongo.py          # Idempotent MongoDB seed runner
│   │   ├── services/
│   │   │   ├── learning_loop.py       # Single-turn atomic assessment workflow
│   │   │   ├── llm_diagnostician.py   # Diagnostic reasoning & speech analyzer
│   │   │   ├── question_selector.py   # Adaptive frontier & remediation engine
│   │   │   └── tutor_engine.py        # Universal Tutor with SSE stream generator
│   │   └── main.py                    # FastAPI application entrypoint
│   └── tests/                         # 61 Automated Pytest suites
├── src/
│   ├── components/
│   │   ├── CleanHomeScreen.tsx        # Minimal JARVIS centerpiece & quick actions
│   │   ├── CleanProgressView.tsx      # Real evidence-based mastery view
│   │   ├── CleanTutorWorkspace.tsx    # Split-panel workspace with KaTeX & code
│   │   ├── EducationalRenderer.tsx    # Streaming KaTeX math & copyable code blocks
│   │   ├── JarvisNeuralCore.tsx       # Reactive 5-state JARVIS intelligence HUD
│   │   ├── JarvisRadialHud.tsx        # Circular reticle & orbital degree ticks
│   │   └── MinimalNav.tsx             # 5-tab persistent navigation header
│   ├── services/
│   │   └── api.ts                     # Centralized typed HTTP & SSE client
│   ├── types/                         # TypeScript interfaces and telemetry contracts
│   ├── App.tsx                        # Main application container & view manager
│   ├── index.css                      # Tailwind v4 styles & chamfer card tokens
│   └── main.tsx                       # React DOM root
├── .env.example                       # Documented environment variables
├── package.json                       # Frontend dependencies & scripts
├── vite.config.ts                     # Vite bundler configuration
└── README.md                          # Comprehensive project documentation
```

---

## Getting Started

### Prerequisites
- **Python**: 3.11 or higher
- **Node.js**: v18 or higher (v20+ recommended) & npm
- **MongoDB**: Local Community Server (running on `localhost:27017`) or a MongoDB Atlas URI

---

### Step 1: Environment Setup

Create your `.env` file in the project root:

```ini
# LLM Provider: 'gemini', 'openai', or 'fallback' (deterministic offline)
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_google_gemini_api_key_here

# MongoDB Connection
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=conceptiq
```

---

### Step 2: Backend Installation & Database Seeding

1. **Create and activate a Python virtual environment**:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

2. **Install backend dependencies**:
   ```bash
   pip install fastapi uvicorn pymongo pydantic pydantic-settings httpx sse-starlette pytest pytest-cov
   ```

3. **Seed MongoDB with the multi-subject curriculum**:
   ```bash
   python -m backend.app.seed.seed_mongo
   ```
   *Expected output: Seeded 3 subjects (CS, Math, Physics), 3 topics, 13 concepts, 14 prerequisites, 10 misconceptions, and 24 questions.*

4. **Launch the FastAPI backend server**:
   ```bash
   uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   Interactive Swagger documentation will be available at **`http://127.0.0.1:8000/docs`**.

---

### Step 3: Frontend Installation & Launch

1. **Install npm packages**:
   ```bash
   npm install --legacy-peer-deps
   ```

2. **Run the Vite development server**:
   ```bash
   npm run dev
   ```

3. **Open the application**:
   Open **`http://localhost:3000`** in your browser.

---

## Testing & Verification

ConceptIQ includes 61 automated unit, integration, and audit tests covering mathematical invariants, schema resilience, and end-to-end workflows:

```bash
python -m pytest backend/tests -v
```

### Verified Test Areas:
- **`test_bkt.py`**: Numerical stability, boundary guarantees ($0.0 \le P(L) \le 1.0$), and monotonicity across correct/incorrect observations.
- **`test_dag.py`**: Cycle detection, self-loop prevention, Kahn's topological sort, and cross-subject prerequisite boundary enforcement.
- **`test_audit_suite.py`**: Correctness authority invariants (ensuring LLM output never overrides the deterministic evaluator).
- **`test_learning_loop_e2e.py`**: Full single-turn attempt processing, BKT updates, Leitner transitions, and next question selection.
- **`test_universal_hierarchy.py`**: Multi-subject coexistence, lazy mastery initialization, and candidate misconception registration.

---

## License

This project is licensed under the Apache-2.0 License. See `LICENSE` for details.
