import React from 'react';
import './SourcePanel.css';

interface SourcePanelProps {
  sources: string[];
}

export default function SourcePanel({ sources }: SourcePanelProps) {
  return (
    <div className="source-panel">
      <div className="source-panel-header">
        <div>
          <span className="source-kicker">Research panel</span>
          <h3>Retrieved Sources</h3>
        </div>
        <span className="source-count">{sources.length}</span>
      </div>

      {sources && sources.length > 0 ? (
        <div className="sources-list">
          {sources.map((source, idx) => (
            <div key={idx} className="source-item">
              <div className="source-icon">📄</div>
              <div className="source-content">
                <div className="source-label">Source {idx + 1}</div>
                <div className="source-text">{source}</div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="empty-sources">
          <p>
            Brak źródeł. Rozpocznij rozmowę, a tutaj pokażą się dokumenty i
            fragmenty wykorzystane przez planera.
          </p>
        </div>
      )}
    </div>
  );
}

