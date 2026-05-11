import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { Mic, Search, ShieldCheck, UserPlus, Activity, MapPin, Phone, Star, Clock, Users } from "lucide-react";
import { health, matchService, registerProvider, voiceLogin, listProviders, listRequests } from "./api";
import "./styles.css";

const defaultPayload = {
  transcript: "Hospital ekak near me urgent",
  latitude: 6.9271,
  longitude: 79.8612,
  visual_hint: "",
};

function useSpeechRecognition(setTranscript) {
  const [listening, setListening] = useState(false);
  const supported = useMemo(() => Boolean(window.SpeechRecognition || window.webkitSpeechRecognition), []);

  const start = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return;
    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.onstart = () => setListening(true);
    recognition.onend = () => setListening(false);
    recognition.onerror = () => setListening(false);
    recognition.onresult = (event) => {
      const result = event.results?.[0]?.[0]?.transcript;
      if (result) setTranscript(result);
    };
    recognition.start();
  };
  return { supported, listening, start };
}

function Metric({ label, value }) {
  return (
    <div className="metric-card">
      <div className="metric-label">{label}</div>
      <div className="metric-value">{value}</div>
    </div>
  );
}

function ProviderCard({ provider }) {
  return (
    <div className="provider-card">
      <div className="provider-head">
        <div className="avatar">{provider.first_name?.[0]}{provider.last_name?.[0]}</div>
        <div>
          <h3>{provider.first_name} {provider.last_name}</h3>
          <p>{provider.service_category} • {provider.city}</p>
        </div>
        <span className="score">{provider.ranking_score}</span>
      </div>
      <div className="provider-grid">
        <span><Star size={15}/> Rating {provider.rating}</span>
        <span><ShieldCheck size={15}/> Trust {Math.round(provider.trust_score * 100)}%</span>
        <span><MapPin size={15}/> {provider.distance_km} km</span>
        <span><Clock size={15}/> ETA {provider.eta_minutes} min</span>
        <span><Phone size={15}/> {provider.phone_number}</span>
        <span><Activity size={15}/> {provider.current_status}</span>
      </div>
      <p className="explain">{provider.ranking_explanation}</p>
    </div>
  );
}

function App() {
  const [payload, setPayload] = useState(defaultPayload);
  const [match, setMatch] = useState(null);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState("");
  const [providers, setProviders] = useState([]);
  const [requests, setRequests] = useState([]);
  const [registration, setRegistration] = useState({ phone_number: "+94710001111", preferred_language: "English" });
  const [registrationResult, setRegistrationResult] = useState(null);
  const [login, setLogin] = useState({ phone_number: "+94710000001", spoken_name: "Nimal Perera" });
  const [loginResult, setLoginResult] = useState(null);
  const { supported, listening, start } = useSpeechRecognition((text) => setPayload((p) => ({ ...p, transcript: text })));

  useEffect(() => {
    health().then(setStatus).catch((e) => setError(e.message));
    listProviders().then(setProviders).catch(() => {});
    listRequests().then(setRequests).catch(() => {});
  }, []);

  const runMatch = async () => {
    setError("");
    try {
      const result = await matchService({
        ...payload,
        latitude: Number(payload.latitude),
        longitude: Number(payload.longitude),
        visual_hint: payload.visual_hint || undefined,
      });
      setMatch(result);
      listRequests().then(setRequests).catch(() => {});
    } catch (e) {
      setError(e.message);
    }
  };

  const runRegistration = async () => {
    setError("");
    try {
      const result = await registerProvider(registration);
      setRegistrationResult(result);
      listProviders().then(setProviders).catch(() => {});
    } catch (e) {
      setError(e.message);
    }
  };

  const runLogin = async () => {
    setError("");
    try {
      const result = await voiceLogin(login);
      setLoginResult(result);
    } catch (e) {
      setError(e.message);
    }
  };

  return (
    <div className="app-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">Multi-Agent AI Research Prototype</p>
          <h1>Behaviour-Aware Multilingual Voice-Based Local Service Discovery System</h1>
          <p className="hero-copy">
            A runnable front-end interface for Sinhala-English/Tamil-English style service requests, urgency-aware intent prediction, provider ranking, and zero-barrier provider onboarding.
          </p>
        </div>
        <div className="status-card">
          <ShieldCheck size={32}/>
          <h3>Backend Status</h3>
          <p>{status ? "Connected" : "Checking connection"}</p>
          {status?.training_report && <small>Intent Accuracy: {Math.round(status.training_report.intent_accuracy * 100)}% • Training Rows: {status.training_report.records}</small>}
        </div>
      </header>

      {error && <div className="error-box">{error}</div>}

      <main className="grid-layout">
        <section className="panel large">
          <div className="section-title"><Search/> <h2>Service Request Matching</h2></div>
          <label>Voice / Text Request</label>
          <textarea value={payload.transcript} onChange={(e) => setPayload({ ...payload, transcript: e.target.value })}/>
          <div className="button-row">
            <button className="secondary" onClick={start} disabled={!supported || listening}><Mic size={17}/>{listening ? "Listening..." : "Use Browser Voice"}</button>
            <button onClick={runMatch}><Search size={17}/> Analyze and Match</button>
          </div>
          {!supported && <p className="help-text">Voice capture requires Chrome or Edge with Web Speech API support. Text input works in every browser.</p>}

          <div className="form-grid">
            <div><label>Latitude</label><input type="number" step="0.0001" value={payload.latitude} onChange={(e) => setPayload({ ...payload, latitude: e.target.value })}/></div>
            <div><label>Longitude</label><input type="number" step="0.0001" value={payload.longitude} onChange={(e) => setPayload({ ...payload, longitude: e.target.value })}/></div>
          </div>
          <label>Optional Visual Context Hint</label>
          <input placeholder="Example: pipe leak under sink / sparking wire / tyre puncture" value={payload.visual_hint} onChange={(e) => setPayload({ ...payload, visual_hint: e.target.value })}/>

          {match && (
            <div className="result-box">
              <div className="metrics-row">
                <Metric label="Predicted Intent" value={match.analysis.intent}/>
                <Metric label="Urgency Level" value={match.analysis.urgency}/>
                <Metric label="Success Probability" value={`${Math.round(match.analysis.success_probability * 100)}%`}/>
                <Metric label="Search Radius" value={`${match.context.search_radius_km} km`}/>
              </div>
              <h3>Top Ranked Providers</h3>
              {match.ranked_providers.length === 0 && <p>No available providers found for this service category.</p>}
              {match.ranked_providers.map((p) => <ProviderCard key={p.id} provider={p}/>) }
              <h3>Multi-Agent Trace</h3>
              <div className="trace-list">
                {match.agent_trace.map((item, index) => <div key={index}><strong>{item.agent}</strong><span>{typeof item.output === "string" ? item.output : JSON.stringify(item.output)}</span></div>)}
              </div>
            </div>
          )}
        </section>

        <section className="panel">
          <div className="section-title"><UserPlus/> <h2>Voice-Driven Provider Registration</h2></div>
          {["first_name", "last_name", "service_category", "city", "phone_number", "preferred_language", "voice_phrase"].map((field) => (
            <div key={field}>
              <label>{field.replaceAll("_", " ")}</label>
              <input value={registration[field] || ""} onChange={(e) => setRegistration({ ...registration, [field]: e.target.value })}/>
            </div>
          ))}
          <button onClick={runRegistration}><UserPlus size={17}/> Save Registration</button>
          {registrationResult && <pre className="small-pre">{JSON.stringify(registrationResult, null, 2)}</pre>}
        </section>

        <section className="panel">
          <div className="section-title"><ShieldCheck/> <h2>Password-Free Voice Login</h2></div>
          <label>Phone Number</label>
          <input value={login.phone_number} onChange={(e) => setLogin({ ...login, phone_number: e.target.value })}/>
          <label>Spoken Name</label>
          <input value={login.spoken_name} onChange={(e) => setLogin({ ...login, spoken_name: e.target.value })}/>
          <button onClick={runLogin}><ShieldCheck size={17}/> Authenticate</button>
          {loginResult && <pre className="small-pre">{JSON.stringify(loginResult, null, 2)}</pre>}
        </section>

        <section className="panel wide">
          <div className="section-title"><Users/> <h2>Provider Bank and Request Monitoring</h2></div>
          <div className="dashboard-grid">
            <Metric label="Registered Providers" value={providers.length}/>
            <Metric label="Logged Requests" value={requests.length}/>
            <Metric label="Online Providers" value={providers.filter(p => p.current_status === "online").length}/>
            <Metric label="Service Categories" value={new Set(providers.map(p => p.service_category)).size}/>
          </div>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Name</th><th>Category</th><th>City</th><th>Status</th><th>Trust</th><th>Jobs</th></tr></thead>
              <tbody>{providers.slice(0, 12).map(p => <tr key={p.id}><td>{p.first_name} {p.last_name}</td><td>{p.service_category}</td><td>{p.city}</td><td>{p.current_status}</td><td>{Math.round(p.trust_score * 100)}%</td><td>{p.completed_jobs}</td></tr>)}</tbody>
            </table>
          </div>
        </section>
      </main>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
