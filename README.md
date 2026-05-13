# R26-IT-109-Research

## Behaviour‑Aware Multilingual Voice‑Based Local Service Discovery System Using a Multi‑Agent AI Framework

### Overview
This research proposes the design, implementation, and evaluation of a **behaviour‑aware, urgency‑sensitive, multilingual voice‑based local service discovery system** using a learning‑driven multi‑agent artificial intelligence framework. The system is specifically designed for real‑world service requests in Sri Lanka, where users frequently speak using mixed languages (Sinhala‑English/Tamil‑English) and incomplete phrases during urgent situations.

The platform introduces behavioural intelligence, acoustic urgency modelling, trust‑aware provider selection, and adaptive workforce coordination to significantly improve service reliability, transparency, and employment sustainability within local service ecosystems.

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Backend** | Python | Voice intent processing, urgency detection, multi-agent coordination, workforce intelligence, acoustic & multimodal analysis |
| **Frontend** | React Native + Node.js | Cross‑platform mobile app, REST APIs, WebSocket real‑time services, OTP/SMS integration, voice registration flow orchestration |
| **Database** | PostgreSQL + Redis | Structured provider/user data, session caching, real‑time state management |
| **ML/AI Libraries** | PyTorch/TensorFlow, scikit-learn, Librosa, Transformers | Speech processing, MFCC extraction, CNN embeddings, multi-agent decision models |

---

## 🏗️ System Architecture

### 🐍 Python Backend (`service_discovery_backend/`)
Handles all AI/ML computation, multi-agent logic, and workforce intelligence:
- **Voice Intent & Urgency Engine** — Code-switch aware NLP, fragmented speech handling, acoustic feature extraction (pitch, speech rate, energy, MFCC), urgency classification (Normal / Moderate / High)
- **Multi‑Agent Coordination Framework** — Context, Search, Distance, Availability, and Ranking agents collaborating for optimal provider selection
- **Workforce Intelligence Module** — Fairness-aware task allocation, dynamic reputation evolution, demand hotspot prediction, income stability forecasting
- **Multimodal Context Fusion** — Optional image upload processing using pretrained CNNs (ResNet / EfficientNet) to refine service classification

### 📱 React Native + Node.js Frontend (`service_discovery_frontend/`)
React Native delivers the mobile experience for both users and providers, with Node.js powering the API layer and real‑time services behind it:
- **Voice Registration & Login Flow** — Conversational audio prompt sequencing in Sinhala / Tamil / English, partial registration save/resume, SMS OTP verification
- **Voice Biometric Authentication** — Password-free login with OTP fallback for new devices or poor acoustic conditions
- **Selfie‑Based Auto‑Profile Generation** — Liveness check + automatic provider dashboard population from a single photo
- **Emergency Mode** — Fragmented speech support, quick-access widgets, acoustic urgency detection
- **Provider Dashboard** — Job listings, availability toggle, trust score display, earnings tracking, map‑based navigation
- **Duplicate Identity Detection** — Phone number conflict resolution with voice biometric fallback for shared-device scenarios
- **Real‑Time Tracking & Notifications** — WebSocket integration for live provider tracking, job alerts, and status updates
- **Location & Mapping** — Real-time GPS, distance calculation, provider tracking on map

---

## 🎓 Research Objectives

### 🔹 Objective 1 — Adaptive Multilingual & Urgency‑Aware Voice Intent Model
- **Code‑Switch Aware Understanding** — Trained on Singlish & Tamil‑English mixes (e.g., *"Hospital ekak near me urgent"*)
- **Fragmented Speech Handling** — Intent detection from incomplete emergency phrases (e.g., *"Accident… plumber… ikmanata…"*)
- **Acoustic Urgency Detection** — Real‑time classification using pitch, speech rate, energy levels, and MFCC features
- **Visual Context Refinement** — Optional CNN‑based image embedding fusion for complex service classification

### 🔹 Objective 2 — Adaptive Multi‑Agent Coordination Framework

| Agent | Responsibility |
|-------|---------------|
| **Context Agent** | Analyzes environmental constraints — user location, request time, and urgency level |
| **Search Agent** | Retrieves candidate providers from the database by service category and location |
| **Distance Agent** | Calculates real-time travel distance and estimated arrival time |
| **Availability Agent** | Verifies whether a provider is online, free, and capable of accepting urgent jobs |
| **Ranking Agent** | Scores providers on ratings, reliability, response speed, and urgent-task history |

### 🔹 Objective 3 — AI‑Driven Employment Empowerment & Workforce Intelligence
- **Fairness‑Aware Task Allocation** — Balances suitability, trust, distance, and opportunity distribution to prevent job concentration
- **Dynamic Reputation Evolution** — Time‑weighted trust scoring that allows providers to recover from past negative ratings
- **Workforce Demand Prediction** — Historical pattern analysis for identifying demand hotspots and skill gaps
- **Income Stability Prediction** — Financial sustainability recommendations for gig workers

### 🔹 Objective 4 — Voice‑Driven Zero‑Barrier Onboarding & Authentication
- **Dual‑Mode Registration** — Manual (typed form) + AI Voice Registration (fully conversational, no typing required)
- **Password‑Free Authentication** — Voice biometric matching with SMS OTP as fallback
- **Partial Registration Support** — Save progress mid-session and resume later
- **Duplicate Identity Resolution** — Shared‑device conflict detection using voice biometric verification
- **Selfie‑to‑Dashboard Automation** — Single‑photo liveness check triggers auto‑generated professional provider profile

---

## 👥 Contributors

| Objective | Contributor |
|-----------|------------|
| **Objective 1** — Adaptive Multilingual & Urgency‑Aware Voice Intent Model | [Thilinaihale](https://github.com/Thilinaihale/Thilinaihale) |
| **Objective 2** — Adaptive Multi‑Agent Coordination Framework | [Sasindu Nimsara](https://github.com/sasindunimsara2002) |
| **Objective 3** — AI‑Driven Employment Empowerment & Workforce Intelligence | [Pamoda-Gamage](https://github.com/Pamoda-Gamage) |
| **Objective 4** — Voice‑Driven Zero‑Barrier Onboarding & Authentication | [Imeshaudayangani](https://github.com/Imeshaudayangani) |

---

## 📄 License

This repository is part of an academic research project. Please contact the contributors before reuse or redistribution.
