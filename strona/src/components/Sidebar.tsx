// src/components/Sidebar.tsx
import React from 'react';
import { User, LogOut, LucideIcon } from 'lucide-react';

interface NavItem {
  id: string;
  icon: LucideIcon;
  label: string;
}

interface SidebarProps {
  navigationItems: NavItem[];
  activeView: string;
  setActiveView: (view: string) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ navigationItems, activeView, setActiveView }) => {
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
        <div className="flex items-center space-x-3 mb-3">
          <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
            <User className="w-4 h-4 text-white" />
          </div>
          <div>
            <p className="text-sm font-medium text-gray-900">Jan Kowalski</p>
            <p className="text-xs text-gray-500">Administrator</p>
          </div>
        </div>
        <button className="flex items-center text-sm text-gray-500 hover:text-gray-700">
          <LogOut className="w-4 h-4 mr-2" /> Wyloguj
        </button>
      </div>
    </div>
  );
};

export default Sidebar;
