// src/components/DashboardView.tsx
import React, { useState, useRef, useEffect } from 'react';
import { Loader2, Send, Sparkles, Star, Award } from 'lucide-react';
import { Message, Profile } from '../types';
import apiClient from '../apiClient'; // Używamy naszego apiClient

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
      // Używamy apiClient, który automatycznie dołączy token
      const response = await apiClient.get('/search', {
        params: { query: currentQuery, skip: 0, limit: 3 } // Pobieramy 3 najlepszych kandydatów
      });

      const data = response.data;
      
      const assistantResponse: Message = { 
        id: (Date.now() + 1).toString(), 
        type: 'assistant', 
        content: data.summary, 
        timestamp: new Date() 
      };
      
      const resultsMessage: Message = { 
        id: (Date.now() + 2).toString(), 
        type: 'results', 
        content: '', 
        timestamp: new Date(), 
        results: data.profiles.items // Wyniki są teraz w data.profiles.items
      };

      setMessages(prev => [...prev, assistantResponse, resultsMessage]);

    } catch (error: any) {
      console.error("Błąd połączenia z API:", error);
      const errorMessage: Message = { 
        id: (Date.now() + 1).toString(), 
        type: 'assistant', 
        content: 'Wystąpił błąd podczas połączenia z serwerem. Proszę spróbować ponownie.', 
        timestamp: new Date() 
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-gray-50">
      <div className="bg-white border-b border-gray-200 p-6">
        <h1 className="text-2xl font-bold text-gray-900">Witaj w SkillSense</h1>
        <p className="text-gray-600">Opisz, kogo lub czego szukasz, a ja znajdę najlepsze dopasowania.</p>
      </div>
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.map((message) => (
          <div key={message.id}>
            {message.type !== 'results' && (
              <div className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-3xl rounded-lg px-4 py-3 shadow-sm ${message.type === 'user' ? 'bg-blue-600 text-white' : 'bg-white border border-gray-200 text-gray-900'}`}>
                  <p className="whitespace-pre-wrap">{message.content}</p>
                </div>
              </div>
            )}
            
            {/* NOWY, PRZEBUDOWANY BLOK WYNIKÓW */}
            {message.results && message.results.length > 0 && (
              <div className="space-y-4 mt-4">
                {message.results.map((profile) => (
                  <div key={profile.id} className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-lg transition-shadow flex flex-col sm:flex-row gap-6">
                    {/* LEWA KOLUMNA: Info i wynik */}
                    <div className="flex-shrink-0 sm:w-1/3 sm:border-r sm:pr-6">
                      <div className="flex items-center space-x-4 mb-4">
                        <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center flex-shrink-0">
                          <span className="text-white font-semibold text-lg">{profile.name.charAt(0)}{profile.surname.charAt(0)}</span>
                        </div>
                        <div>
                          <h3 className="font-bold text-lg text-gray-900">{profile.name} {profile.surname}</h3>
                        </div>
                      </div>
                      <div className="space-y-2">
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-gray-600 font-medium flex items-center"><Star className="w-4 h-4 mr-2 text-yellow-500"/> Dopasowanie:</span>
                            <span className="font-bold text-xl text-blue-600">{Math.round(profile.match_score || 0)}%</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2.5">
                            <div className="bg-gradient-to-r from-blue-400 to-blue-500 h-2.5 rounded-full" style={{ width: `${profile.match_score || 0}%` }}></div>
                          </div>
                      </div>
                    </div>
                    
                    {/* PRAWA KOLUMNA: Uzasadnienie i umiejętności */}
                    <div className="flex-1">
                      {profile.reasoning && (
                        <div>
                          <h4 className="text-sm font-semibold text-gray-800 flex items-center mb-2">
                            <Sparkles className="w-4 h-4 mr-2 text-blue-500" />
                            Dlaczego pasuje?
                          </h4>
                          <p className="text-sm text-gray-700 leading-relaxed italic border-l-2 border-blue-200 pl-3">
                            {profile.reasoning}
                          </p>
                        </div>
                      )}
                      <div className="mt-4">
                         <h4 className="text-sm font-semibold text-gray-800 flex items-center mb-2">
                            <Award className="w-4 h-4 mr-2 text-gray-500" />
                            Kluczowe umiejętności
                          </h4>
                        <div className="flex flex-wrap gap-2">
                          {profile.skills.slice(0, 5).map((skill) => (
                            <span key={skill.name} className="px-2.5 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded-full border border-gray-200">
                              {skill.name}
                            </span>
                          ))}
                        </div>
                      </div>
                       <button onClick={() => setSelectedProfile(profile)} className="w-full sm:w-auto mt-6 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 font-medium transition-colors text-sm">
                          Zobacz Pełny Profil
                        </button>
                    </div>
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
                <span className="text-gray-600">Analizuję kandydatów...</span>
              </div>
            </div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>
      <div className="border-t border-gray-200 bg-white p-6">
        <div className="flex space-x-4">
          <input type="text" value={inputValue} onChange={(e) => setInputValue(e.target.value)} onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()} placeholder="Np. 'doświadczony analityk danych z Pythonem i SQL'" className="flex-1 border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500" disabled={isTyping} />
          <button onClick={handleSendMessage} disabled={isTyping || !inputValue.trim()} className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center space-x-2 font-semibold">
            <Send className="w-4 h-4" /> <span>Szukaj</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default DashboardView;
