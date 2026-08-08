import React, { useEffect, useMemo, useState } from 'react';
import './App.css';
import ChatInterface from './components/ChatInterface';
import SourcePanel from './components/SourcePanel';
import { useWebSocket } from './hooks/useWebSocket';
import { useTripState } from './hooks/useTripState';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: string[];
  timestamp: number;
}

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedSources, setSelectedSources] = useState<string[]>([]);
  const { tripState, updateTripState } = useTripState();
  const { ws, isConnected } = useWebSocket('ws://localhost:8000/ws');
  const messageCountLabel = `${messages.length} msg`;

  const itineraryDays = tripState?.itinerary?.length ?? 0;
  const itineraryActivities = useMemo(
    () =>
      tripState?.itinerary?.reduce(
        (total, day) => total + day.activities.length,
        0
      ) ?? 0,
    [tripState]
  );
  const tripHighlights = [
    tripState?.destination ? `📍 ${tripState.destination}` : null,
    tripState?.budget ? `💶 ${tripState.budget}` : null,
    tripState?.interests?.length
      ? `✨ ${tripState.interests.join(', ')}`
      : null,
  ].filter(Boolean) as string[];

  const handleSendMessage = (userMessage: string) => {
    if (!ws || loading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: userMessage,
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    // Send message to backend
    ws.send(JSON.stringify({ message: userMessage }));
  };

  useEffect(() => {
    if (!ws) return;

    const handleMessage = (event: MessageEvent) => {
      const data = JSON.parse(event.data);

      if (data.type === 'response') {
        const assistantMsg: Message = {
          id: Date.now().toString(),
          role: 'assistant',
          content: data.content,
          sources: data.sources,
          timestamp: Date.now(),
        };
        setMessages((prev) => [...prev, assistantMsg]);
        setSelectedSources(data.sources || []);
      } else if (data.type === 'state_update') {
        updateTripState(data.state);
      }

      setLoading(false);
    };

    ws.addEventListener('message', handleMessage);
    return () => ws.removeEventListener('message', handleMessage);
  }, [ws, updateTripState]);

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-content">
          <div className="brand-block">
            <div className="brand-badge">✦ AI travel workspace</div>
            <div>
              <h1>Horyzonty Trip Planner</h1>
              <p>
                Bardziej uporządkowany panel do planowania podróży, źródeł i
                kolejnych kroków.
              </p>
            </div>
          </div>

          <div className="header-meta">
            <div className="header-pill">Desktop mode</div>
            <div className="connection-status">
              <span
                className={`status-indicator ${
                  isConnected ? 'connected' : 'disconnected'
                }`}
              ></span>
              {isConnected ? 'Backend online' : 'Łączenie z backendem'}
            </div>
          </div>
        </div>
      </header>

      <main className="app-main">
        <div className="chat-section">
          <ChatInterface
            messages={messages}
            onSendMessage={handleSendMessage}
            isLoading={loading}
            isConnected={isConnected}
          />
        </div>

        <aside className="source-section">
          <section className="insight-panel overview-panel">
            <div className="panel-heading">
              <div>
                <span className="panel-kicker">Trip workspace</span>
                <h3>Aktualna sesja</h3>
              </div>
              <span className="panel-badge">
                {messageCountLabel}
              </span>
            </div>

            <div className="overview-grid">
              <div className="overview-card">
                <span className="overview-label">Plan dni</span>
                <strong>{itineraryDays || '—'}</strong>
              </div>
              <div className="overview-card">
                <span className="overview-label">Aktywności</span>
                <strong>{itineraryActivities || '—'}</strong>
              </div>
              <div className="overview-card">
                <span className="overview-label">Źródła</span>
                <strong>{selectedSources.length || '—'}</strong>
              </div>
              <div className="overview-card">
                <span className="overview-label">Loty</span>
                <strong>{tripState?.flights?.length ?? '—'}</strong>
              </div>
            </div>

            <div className="trip-summary">
              {tripHighlights.length > 0 ? (
                tripHighlights.map((highlight) => (
                  <span key={highlight} className="summary-chip">
                    {highlight}
                  </span>
                ))
              ) : (
                <p className="summary-empty">
                  Po rozpoczęciu rozmowy tutaj pojawi się skrót destination,
                  budżetu i preferencji.
                </p>
              )}
            </div>
          </section>

          <SourcePanel sources={selectedSources} />

          {tripState && (
            <details className="trip-state-panel">
              <summary>
                <div>
                  <span className="panel-kicker">Debug</span>
                  <h3>Raw TripState</h3>
                </div>
                <span className="panel-badge subtle">JSON</span>
              </summary>
              <pre>{JSON.stringify(tripState, null, 2)}</pre>
            </details>
          )}
        </aside>
      </main>
    </div>
  );
}

export default App;

