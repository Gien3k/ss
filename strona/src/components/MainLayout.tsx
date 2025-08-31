// src/components/MainLayout.tsx
import React, { useState } from 'react';
import { Home, FileText, Database, User, LogOut } from 'lucide-react';
import DashboardView from './DashboardView.tsx'; 
import UploadProfileView from './UploadProfileView.tsx';
import DatabaseView from './DatabaseView.tsx';
import { Profile } from '../types.ts';
import ProfileDetailModal from './ProfileDetailModal.tsx';

interface MainLayoutProps {
  onLogout: () => void;
}

const Sidebar: React.FC<{ activeView: string; setActiveView: (view: string) => void; onLogout: () => void; }> = ({ activeView, setActiveView, onLogout }) => {
    const navigationItems = [
        { id: 'dashboard', icon: Home, label: 'Dashboard' },
        { id: 'upload-cv', icon: FileText, label: 'Dodaj Profil' },
        { id: 'database', icon: Database, label: 'Baza Kandydatów' },
    ];

    return (
        <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
            <div className="p-6 border-b border-gray-200">
                <h1 className="text-xl font-bold text-blue-700">SkillSense</h1>
                <p className="text-xs text-gray-500 mt-1">Politechnika Rzeszowska</p>
            </div>
            <nav className="flex-1 p-4">
                <ul className="space-y-2">
                    {navigationItems.map((item) => (
                        <li key={item.id}>
                            <a href="#" onClick={(e) => { e.preventDefault(); setActiveView(item.id); }}
                                className={`flex items-center px-4 py-3 rounded-lg transition-colors ${activeView === item.id ? 'bg-blue-50 text-blue-700 border border-blue-200' : 'text-gray-600 hover:bg-gray-50'}`}>
                                <item.icon className="w-5 h-5 mr-3" />
                                <span className="text-sm font-medium">{item.label}</span>
                            </a>
                        </li>
                    ))}
                </ul>
            </nav>
            <div className="p-4 border-t border-gray-200">
                <button onClick={onLogout} className="flex items-center w-full px-4 py-3 text-sm text-gray-500 rounded-lg hover:bg-gray-50 hover:text-gray-700">
                    <LogOut className="w-4 h-4 mr-2" /> Wyloguj
                </button>
            </div>
        </div>
    );
};


const MainLayout: React.FC<MainLayoutProps> = ({ onLogout }) => {
  const [activeView, setActiveView] = useState('dashboard');
  const [selectedProfile, setSelectedProfile] = useState<Profile | null>(null);

  const renderActiveView = () => {
    switch (activeView) {
      case 'dashboard':
        return <DashboardView setSelectedProfile={setSelectedProfile} />;
      case 'upload-cv':
        return <UploadProfileView />;
      case 'database':
        return <DatabaseView />;
      default:
        return <div className="p-6">Wybierz opcję z menu</div>;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
        <Sidebar activeView={activeView} setActiveView={setActiveView} onLogout={onLogout} />
        <div className="flex-1 flex flex-col h-screen overflow-y-hidden">
            {renderActiveView()}
        </div>
        {selectedProfile && (
            <ProfileDetailModal
                profile={selectedProfile}
                onClose={() => setSelectedProfile(null)}
            />
        )}
    </div>
  );
};

export default MainLayout;
