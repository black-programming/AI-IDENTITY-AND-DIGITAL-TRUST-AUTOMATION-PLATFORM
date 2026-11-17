import React, { useState } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import CommandCenterView from './views/CommandCenterView';
import VerificationHubView from './views/VerificationHubView';
import RiskEngineView from './views/RiskEngineView';
import CasesQueueView from './views/CasesQueueView';
import AuditLedgerView from './views/AuditLedgerView';
import SecuritySessionsView from './views/SecuritySessionsView';
import ApiExplorerView from './views/ApiExplorerView';
import CommandPaletteModal from './components/CommandPaletteModal';
import './App.css';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [isCommandOpen, setIsCommandOpen] = useState(false);

  const handleInspectCase = (caseItem) => {
    setActiveTab('verify');
  };

  return (
    <div className="app-shell" id="app-root">
      {/* Top Header */}
      <Header 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        onOpenCommand={() => setIsCommandOpen(true)}
      />

      {/* Main Layout Area */}
      <div className="app-body">
        {/* Dynamic Navigation Sidebar */}
        <Sidebar 
          activeTab={activeTab} 
          setActiveTab={setActiveTab} 
        />

        {/* Content View Area */}
        <main className="app-main-viewport" id="main-content">
          {activeTab === 'overview' && (
            <CommandCenterView 
              onSelectTab={setActiveTab} 
              onInspectCase={handleInspectCase}
            />
          )}
          {activeTab === 'verify' && <VerificationHubView />}
          {activeTab === 'risk' && <RiskEngineView />}
          {activeTab === 'cases' && <CasesQueueView />}
          {activeTab === 'audit' && <AuditLedgerView />}
          {activeTab === 'security' && <SecuritySessionsView />}
          {activeTab === 'api' && <ApiExplorerView />}
        </main>
      </div>

      {/* Command Palette Modal (⌘K) */}
      <CommandPaletteModal 
        isOpen={isCommandOpen} 
        onClose={() => setIsCommandOpen(false)} 
        onSelectTab={setActiveTab}
      />
    </div>
  );
}
