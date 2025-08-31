// src/components/DashboardView.tsx
import React, { useState, useRef, useEffect } from 'react';
import { Loader2, Send } from 'lucide-react';
import { Message, Profile } from '../types';

interface DashboardViewProps {
  setSelectedProfile: (profile: Profile) => void;
}

const DashboardView: React.FC<DashboardViewProps> = ({ setSelectedProfile }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  useEffect(() => {
    setMessages([{ id: '1', type: 'assistant', content: 'Dzień dobry! Jestem asystentem SkillSense. Opisz kogo szukasz, a ja postaram się znaleźć odpowiednich kandydatów.', timestamp: new Date() }]);
  }, []);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isTyping) return;
    const userMessage: Message = { id: Date.now().toString(), type: 'user', content: inputValue, timestamp: new Date() };
    setMessages(prev => [...prev, userMessage]);
    const currentQuery = inputValue;
    setInputValue('');
    setIsTyping(true);

    try {
      const response = await fetch(`http://34.70.6.174:8000/search?query=${encodeURIComponent(currentQuery)}`);
      if (!response.ok) throw new Error(`Błąd serwera: ${response.statusText}`);
      const data = await response.json();
      const assistantResponse: Message = { id: (Date.now() + 1).toString(), type: 'assistant', content: data.summary, timestamp: new Date() };
      const resultsMessage: Message = { id: (Date.now() + 2).toString(), type: 'results', content: '', timestamp: new Date(), results: data.profiles };
      setMessages(prev => [...prev, assistantResponse, resultsMessage]);
    } catch (error: any) {
      console.error("Błąd połączenia z API:", error);
      const errorMessage: Message = { id: (Date.now() + 1).toString(), type: 'assistant', content: 'Wystąpił błąd podczas połączenia z serwerem.', timestamp: new Date() };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full">
      <div className="bg-white border-b border-gray-200 p-6">
        <h1 className="text-2xl font-bold text-gray-900">Witaj w SkillSense</h1>
        <p className="text-gray-600">Opisz, kogo lub czego szukasz, a ja znajdę najlepsze dopasowania.</p>
      </div>
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.map((message) => (
          <div key={message.id} className="space-y-4">
            {message.type !== 'results' && (
              <div className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-3xl rounded-lg px-4 py-3 ${message.type === 'user' ? 'bg-blue-600 text-white' : 'bg-white border border-gray-200 text-gray-900'}`}>
                  <p>{message.content}</p>
                </div>
              </div>
            )}
            {message.results && (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 max-w-6xl">
                {message.results.map((profile, index) => (
                  <div key={index} className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-lg transition-shadow flex flex-col">
                    <div className="flex items-center space-x-4 mb-4">
                      <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center flex-shrink-0">
                        <span className="text-white font-semibold">{profile.name.charAt(0)}{profile.surname.charAt(0)}</span>
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900">{profile.name} {profile.surname}</h3>
                      </div>
                    </div>
                    
                    <div className="mb-4">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">Dopasowanie:</span>
                        <span className="font-semibold text-blue-600">{profile.match_score}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                        <div className="bg-gradient-to-r from-blue-400 to-blue-500 h-2 rounded-full" style={{ width: `${profile.match_score || 0}%` }}></div>
                      </div>
                    </div>

                    <div className="flex-1"></div>
                    <button onClick={() => setSelectedProfile(profile)} className="w-full mt-4 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 font-medium transition-colors">
                      Zobacz Pełny Profil
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 rounded-lg px-4 py-3">
              <div className="flex items-center space-x-2">
                <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                <span className="text-gray-600">Przetwarzam zapytanie...</span>
              </div>
            </div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>
      <div className="border-t border-gray-200 bg-white p-6">
        <div className="flex space-x-4">
          <input type="text" value={inputValue} onChange={(e) => setInputValue(e.target.value)} onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()} placeholder="Np. 'student informatyki z C++...'" className="flex-1 border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500" disabled={isTyping} />
          <button onClick={handleSendMessage} disabled={isTyping || !inputValue.trim()} className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center space-x-2">
            <Send className="w-4 h-4" /> <span>Wyślij</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default DashboardView;
