import React, { useState, useRef, useEffect } from 'react';
import './ChatInterface.css';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: string[];
  timestamp: number;
}

interface ChatInterfaceProps {
  messages: Message[];
  onSendMessage: (message: string) => void;
  isLoading: boolean;
  isConnected: boolean;
}

export default function ChatInterface({
  messages,
  onSendMessage,
  isLoading,
  isConnected,
}: ChatInterfaceProps) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const quickPrompts = [
    {
      icon: '🗺️',
      label: 'City break',
      text: 'Plan me 3 days in Lisbon for food and history lovers, budget around €100/day',
    },
    {
      icon: '✈️',
      label: 'Flights',
      text: 'Find flights from Warsaw to Barcelona in June',
    },
    {
      icon: '🏛️',
      label: 'Recommendations',
      text: 'What museums in Rome are best for a first-time visitor?',
    },
  ];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading && isConnected) {
      onSendMessage(input);
      setInput('');
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-topbar">
        <div>
          <span className="chat-kicker">Conversation</span>
          <h2>Planowanie podróży</h2>
        </div>

        <div className="chat-topbar-meta">
          <span className="chat-stat">{messages.length} turns</span>
          <span className={`chat-status ${isConnected ? 'live' : 'offline'}`}>
            {isConnected ? 'Live session' : 'Offline'}
          </span>
        </div>
      </div>

      <div className="messages-area">
        {messages.length === 0 ? (
          <div className="empty-state">
            <div className="empty-hero">
              <div className="empty-icon">🌍</div>
              <div className="empty-copy">
                <h2>Zaprojektuj podróż od jednego promptu</h2>
                <p>
                  Opisz kierunek, budżet i styl wyjazdu. Interfejs po prawej
                  pokaże źródła, a rozmowa tutaj zostanie zorganizowana jak
                  desktopowy workspace.
                </p>
              </div>
            </div>

            <div className="empty-benefits">
              <div className="benefit-card">
                <strong>RAG + źródła</strong>
                <span>Łatwiej zobaczyć, skąd biorą się rekomendacje.</span>
              </div>
              <div className="benefit-card">
                <strong>Refinement flow</strong>
                <span>Zmiany planu w kolejnych wiadomościach bez restartu.</span>
              </div>
              <div className="benefit-card">
                <strong>Desktop layout</strong>
                <span>Więcej informacji na ekranie i lepsza hierarchia.</span>
              </div>
            </div>

            <div className="example-prompts">
              {quickPrompts.map((prompt) => (
                <button
                  key={prompt.label}
                  onClick={() => isConnected && onSendMessage(prompt.text)}
                  disabled={!isConnected || isLoading}
                >
                  <span className="prompt-icon">{prompt.icon}</span>
                  <span>
                    <strong>{prompt.label}</strong>
                    <small>{prompt.text}</small>
                  </span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <div
                key={message.id}
                className={`message ${message.role === 'user' ? 'user-message' : 'assistant-message'}`}
              >
                <div className="message-avatar">
                  {message.role === 'user' ? '👤' : '🤖'}
                </div>
                <div className="message-content">
                  <div className="message-meta">
                    <span>{message.role === 'user' ? 'Ty' : 'Trip Planner'}</span>
                    <span>
                      {new Date(message.timestamp).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </span>
                  </div>
                  <p>{message.content}</p>
                  {message.sources && message.sources.length > 0 && (
                    <div className="message-sources">
                      <span className="sources-label">📚 Sources:</span>
                      <ul>
                        {message.sources.map((source, idx) => (
                          <li key={idx}>{source}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="message assistant-message">
                <div className="message-avatar">🤖</div>
                <div className="message-content">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      <form className="input-area" onSubmit={handleSubmit}>
        <div className="input-wrapper">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              isConnected
                ? 'Np. 4 dni w Porto, budżet 120€/dzień, sztuka i dobre jedzenie...'
                : 'Łączenie z serwerem...'
            }
            disabled={!isConnected || isLoading}
            className="chat-input"
          />
          <button
            type="submit"
            disabled={!isConnected || isLoading || !input.trim()}
            className="send-button"
          >
            {isLoading ? '⏳' : '📤'}
          </button>
        </div>
        <p className="input-hint">
          💡 Spróbuj: "Plan 4 days in Porto", "Find flights to Barcelona" albo
          "What museums are open on Sundays?"
        </p>
      </form>
    </div>
  );
}

