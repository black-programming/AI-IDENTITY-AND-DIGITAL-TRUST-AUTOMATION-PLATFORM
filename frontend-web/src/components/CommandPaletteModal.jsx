import React, { useState, useEffect } from 'react';
import { 
  Search, 
  X, 
  LayoutDashboard, 
  FileCheck2, 
  Cpu, 
  Layers, 
  FileText, 
  ShieldAlert, 
  Network,
  ArrowRight
} from 'lucide-react';

export default function CommandPaletteModal({ isOpen, onClose, onSelectTab }) {
  const [query, setQuery] = useState('');

  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        if (isOpen) onClose();
        else onClose(false); // toggle
      }
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const commands = [
    { id: 'overview', title: 'Go to Command Center', category: 'Navigation', icon: LayoutDashboard },
    { id: 'verify', title: 'Open Live Verification Hub (Aadhaar, PAN, DL)', category: 'Inference', icon: FileCheck2 },
    { id: 'risk', title: 'Explainable AI Risk Engine & Platt Calibration', category: 'AI Models', icon: Cpu },
    { id: 'cases', title: 'Reviewer Queue Workbench (Human-in-the-Loop)', category: 'Review', icon: Layers },
    { id: 'audit', title: 'Immutable Merkle Audit Ledger & Signed Receipts', category: 'Compliance', icon: FileText },
    { id: 'security', title: 'Zero-Trust Security & Threat Defense', category: 'Security', icon: ShieldAlert },
    { id: 'api', title: 'FastAPI v1 Microservice Explorer & Docs', category: 'Developer', icon: Network }
  ];

  const filtered = commands.filter(c => 
    c.title.toLowerCase().includes(query.toLowerCase()) || 
    c.category.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div className="cmd-modal-backdrop" onClick={onClose}>
      <div className="cmd-modal-container cyber-card" onClick={(e) => e.stopPropagation()}>
        <div className="cmd-modal-header">
          <Search size={18} className="text-cyan" />
          <input 
            type="text" 
            autoFocus 
            placeholder="Type a command, screen, or document identifier..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="cmd-input font-mono"
          />
          <button className="btn-close-cmd" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <div className="cmd-results-list">
          {filtered.length === 0 ? (
            <div className="cmd-empty text-dim font-mono">No matching actions found.</div>
          ) : (
            filtered.map((item) => {
              const Icon = item.icon;
              return (
                <div 
                  key={item.id} 
                  className="cmd-result-item"
                  onClick={() => {
                    onSelectTab(item.id);
                    onClose();
                  }}
                >
                  <div className="cmd-item-icon">
                    <Icon size={16} className="text-cyan" />
                  </div>
                  <div className="cmd-item-text">
                    <span className="cmd-item-title">{item.title}</span>
                    <span className="cmd-item-category font-mono">{item.category}</span>
                  </div>
                  <ArrowRight size={14} className="cmd-arrow text-dim" />
                </div>
              );
            })
          )}
        </div>

        <div className="cmd-footer font-mono text-dim">
          <span>Navigation: <kbd>↑</kbd> <kbd>↓</kbd></span>
          <span>Select: <kbd>↵</kbd></span>
          <span>Close: <kbd>ESC</kbd></span>
        </div>
      </div>
    </div>
  );
}
