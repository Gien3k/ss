import React, { useState, useRef, useEffect } from 'react';
import { 
  Home, 
  Users, 
  UserCheck, 
  Briefcase, 
  Wrench, 
  Send, 
  User,
  LogOut,
  Loader2,
  X,
  UploadCloud,
  FileText,
  Database,
  Mail,
  Phone,
  Linkedin,
  Github
} from 'lucide-react';

// --- ZAKTUALIZOWANE INTERFEJSY ---
interface Skill {
  name: string;
}

interface WorkExperience {
  position: string;
  company: string;
  start_date: string;
  end_date: string;
  description: string;
}

interface Education {
  institution: string;
  degree: string;
  start_date: string;
  end_date: string;
}

interface Project {
    name: string;
    description: string;
}

interface Profile {
  id: number;
  name: string;
  surname: string;
  email: string | null;
  phone: string | null;
  linkedin_url: string | null;
  github_url: string | null;
  description: string;
  experience_score: number;
  skills: Skill[];
  work_experiences: WorkExperience[];
  education_history: Education[];
  projects: Project[];
  cv_filepath: string | null;
}

interface Message {
  id: string;
  type: 'user' | 'assistant' | 'results';
  content: string;
  timestamp: Date;
  results?: Profile[];
}

// --- NOWY, ROZBUDOWANY KOMPONENT WIDOKU BAZY DANYCH ---
const DatabaseView = () => {
  const [users, setUsers] = useState<Profile[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedUser, setSelectedUser] = useState<Profile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async (query: string = '') => {
    setIsLoading(true);
    try {
      const response = await fetch(`http://34.70.6.174:8000/users?search=${encodeURIComponent(query)}`);
      if (!response.ok) throw new Error('Błąd pobierania danych');
      const data = await response.json();
      setUsers(data);
    } catch (error) {
      console.error("Błąd:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
    fetchUsers(event.target.value);
  };

  return (
    <div className="flex h-full bg-white">
      {/* Lewy panel: lista i wyszukiwarka */}
      <div className="w-1/3 border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b">
          <input
            type="text"
            placeholder="Szukaj po imieniu lub nazwisku..."
            value={searchTerm}
            onChange={handleSearch}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div className="flex-1 overflow-y-auto">
          {isLoading ? (
            <div className="p-4 text-center text-gray-500">Ładowanie użytkowników...</div>
          ) : (
            <ul>
              {users.map(user => (
                <li key={user.id} onClick={() => setSelectedUser(user)} className={`p-4 border-b cursor-pointer hover:bg-gray-50 ${selectedUser?.id === user.id ? 'bg-blue-50' : ''}`}>
                  <p className="font-semibold text-gray-800">{user.name} {user.surname}</p>
                  <p className="text-sm text-gray-600 truncate">{user.description}</p>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* Prawy panel: szczegóły i PDF */}
      <div className="w-2/3 flex-1 flex flex-col">
        {selectedUser ? (
          <div className="flex-1 flex h-full">
            {selectedUser.cv_filepath && (
              <div className="w-1/2 h-full border-r border-gray-200">
                <iframe 
                  src={`http://34.70.6.174:8000/cv/${selectedUser.id}`} 
                  className="w-full h-full border-none"
                  title={`CV of ${selectedUser.name}`}
                />
              </div>
            )}
            <div className={`p-6 overflow-y-auto ${selectedUser.cv_filepath ? 'w-1/2' : 'w-full'}`}>
              <h2 className="text-2xl font-bold text-gray-900">{selectedUser.name} {selectedUser.surname}</h2>
              <div className="text-sm text-gray-500 mt-1">
                <p>{selectedUser.email}</p>
                <p>{selectedUser.phone}</p>
              </div>

              <h3 className="text-lg font-semibold mt-6 mb-2 text-gray-800">Podsumowanie</h3>
              <p className="text-gray-700 leading-relaxed">{selectedUser.description}</p>
              
              <h3 className="text-lg font-semibold mt-6 mb-2 text-gray-800">Doświadczenie zawodowe</h3>
              {selectedUser.work_experiences.map((exp, index) => (
                <div key={index} className="mb-4">
                  <p className="font-semibold">{exp.position} w {exp.company}</p>
                  <p className="text-sm text-gray-500">{exp.start_date} - {exp.end_date}</p>
                  <p className="text-sm text-gray-700 mt-1">{exp.description}</p>
                </div>
              ))}

              <h3 className="text-lg font-semibold mt-6 mb-2 text-gray-800">Umiejętności</h3>
              <div className="flex flex-wrap gap-2">
                {selectedUser.skills.map((skill, index) => (
                  <span key={index} className="px-3 py-1 bg-blue-50 text-blue-700 text-sm rounded-full border border-blue-200 font-medium">{skill.name}</span>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            <p>Wybierz użytkownika z listy, aby zobaczyć szczegóły.</p>
          </div>
        )}
      </div>
    </div>
  );
};


// ... (reszta kodu bez zmian) ...
const UploadProfileView = () => {
  const [uploadType, setUploadType] = useState<'file' | 'text'>('file');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [description, setDescription] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [message, setMessage] = useState('');

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      setSelectedFile(event.target.files[0]);
      setMessage('');
    }
  };

  const handleSubmit = async () => {
    setIsUploading(true);
    setMessage('Przetwarzanie danych...');

    let endpoint = '';
    let body: FormData | string;

    if (uploadType === 'file') {
      if (!selectedFile) {
        setMessage('Proszę najpierw wybrać plik.');
        setIsUploading(false);
        return;
      }
      endpoint = 'http://34.70.6.174:8000/upload-cv';
      const formData = new FormData();
      formData.append('file', selectedFile);
      body = formData;
    } else {
      if (!description.trim()) {
        setMessage('Proszę wprowadzić opis.');
        setIsUploading(false);
        return;
      }
      endpoint = 'http://34.70.6.174:8000/process-text';
      body = JSON.stringify({ description });
    }

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: uploadType === 'text' ? { 'Content-Type': 'application/json' } : {},
        body: body,
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || 'Wystąpił błąd podczas przesyłania.');
      }
      
      setMessage(`Sukces! Przetworzono profil dla: ${result.data.personal_info.name}.`);

    } catch (error: any) {
      setMessage(`Błąd: ${error.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">Dodaj swój profil</h1>
      <p className="text-gray-600 mb-6">Nasz system automatycznie przeanalizuje dane i utworzy profil w naszej bazie talentów.</p>
      
      <div className="flex justify-center mb-6">
        <div className="bg-gray-200 rounded-lg p-1 flex space-x-1">
          <button onClick={() => setUploadType('file')} className={`px-4 py-2 text-sm font-medium rounded-md ${uploadType === 'file' ? 'bg-white text-blue-600 shadow' : 'text-gray-600'}`}>
            Prześlij plik CV
          </button>
          <button onClick={() => setUploadType('text')} className={`px-4 py-2 text-sm font-medium rounded-md ${uploadType === 'text' ? 'bg-white text-blue-600 shadow' : 'text-gray-600'}`}>
            Wpisz opis ręcznie
          </button>
        </div>
      </div>

      {uploadType === 'file' && (
        <div className="bg-white border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
          <UploadCloud className="mx-auto h-12 w-12 text-gray-400" />
          <p className="mt-4 text-sm text-gray-600">
            <label htmlFor="file-upload" className="font-medium text-blue-600 hover:text-blue-500 cursor-pointer">
              Wybierz plik
            </label>
            lub przeciągnij go tutaj (.pdf, .docx).
          </p>
          <input id="file-upload" type="file" className="sr-only" onChange={handleFileChange} accept=".pdf,.docx"/>
          {selectedFile && <p className="mt-2 text-sm text-gray-500">{selectedFile.name}</p>}
        </div>
      )}

      {uploadType === 'text' && (
        <div>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={10}
            className="w-full border border-gray-300 rounded-lg p-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Wklej tutaj treść swojego CV lub opisz swoje umiejętności, doświadczenie i projekty..."
          />
        </div>
      )}

      <div className="mt-6">
        <button
          onClick={handleSubmit}
          disabled={isUploading}
          className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center space-x-2"
        >
          {isUploading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
          <span>{isUploading ? 'Przetwarzanie...' : 'Wyślij i przeanalizuj'}</span>
        </button>
      </div>

      {message && <p className="mt-4 text-center text-sm text-gray-600">{message}</p>}
    </div>
  );
};


function App() {
  const [activeView, setActiveView] = useState('dashboard');
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [selectedProfile, setSelectedProfile] = useState<Profile | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  useEffect(() => {
    setMessages([{ id: '1', type: 'assistant', content: 'Dzień dobry! Jestem asystentem SkillSense...', timestamp: new Date() }]);
  }, []);

  const handleSendMessage = async () => {
    // ... Logika wysyłania wiadomości bez zmian ...
    if (!inputValue.trim() || isTyping) return;
    const userMessage: Message = { id: Date.now().toString(), type: 'user', content: inputValue, timestamp: new Date() };
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    try {
      const response = await fetch(`http://34.70.6.174:8000/search?query=${encodeURIComponent(userMessage.content)}`);
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

  const navigationItems = [
    { id: 'dashboard', icon: Home, label: 'Dashboard' },
    { id: 'upload-cv', icon: FileText, label: 'Dodaj Profil' },
    { id: 'database', icon: Database, label: 'Baza Kandydatów' },
  ];

  const renderActiveView = () => {
    switch (activeView) {
      case 'dashboard':
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
                              <span className="text-gray-600">Wskaźnik Doświadczenia:</span>
                              <span className="font-semibold text-blue-600">{profile.experience_score}</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                              <div className="bg-gradient-to-r from-blue-400 to-blue-500 h-2 rounded-full" style={{ width: `${Math.min(profile.experience_score * 10, 100)}%` }}></div>
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
      <div className="flex-1 flex flex-col h-screen overflow-y-hidden">
        {renderActiveView()}
      </div>
      {selectedProfile && (
        <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-2xl p-8 max-w-4xl w-full relative max-h-[90vh] flex flex-col">
            <button onClick={() => setSelectedProfile(null)} className="absolute top-4 right-4 text-gray-500 hover:text-gray-800">
              <X />
            </button>
            <div className="flex items-center space-x-6 mb-6 flex-shrink-0">
              <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center">
                <span className="text-white font-bold text-3xl">{selectedProfile.name.charAt(0)}{selectedProfile.surname.charAt(0)}</span>
              </div>
              <div>
                <h2 className="text-3xl font-bold text-gray-900">{selectedProfile.name} {selectedProfile.surname}</h2>
                <div className="flex space-x-4 text-gray-500 mt-2">
                  {selectedProfile.email && <div className="flex items-center"><Mail className="w-4 h-4 mr-2"/> {selectedProfile.email}</div>}
                  {selectedProfile.phone && <div className="flex items-center"><Phone className="w-4 h-4 mr-2"/> {selectedProfile.phone}</div>}
                  {selectedProfile.linkedin_url && <a href={selectedProfile.linkedin_url} target="_blank" className="flex items-center hover:text-blue-600"><Linkedin className="w-4 h-4 mr-2"/> LinkedIn</a>}
                  {selectedProfile.github_url && <a href={selectedProfile.github_url} target="_blank" className="flex items-center hover:text-blue-600"><Github className="w-4 h-4 mr-2"/> GitHub</a>}
                </div>
              </div>
            </div>
            <div className="overflow-y-auto pr-4">
              <h3 className="text-xl font-semibold mb-2 text-gray-800">Podsumowanie</h3>
              <p className="text-gray-700 mb-6 leading-relaxed">{selectedProfile.description}</p>
              
              <h3 className="text-xl font-semibold mb-2 text-gray-800">Doświadczenie zawodowe</h3>
              {selectedProfile.work_experiences.map((exp, index) => (
                <div key={index} className="mb-4 pl-4 border-l-2 border-blue-200">
                  <p className="font-semibold text-gray-900">{exp.position} w {exp.company}</p>
                  <p className="text-sm text-gray-500">{exp.start_date} - {exp.end_date}</p>
                  <p className="text-sm text-gray-700 mt-1">{exp.description}</p>
                </div>
              ))}

              <h3 className="text-xl font-semibold mt-6 mb-2 text-gray-800">Projekty</h3>
              {selectedProfile.projects.map((proj, index) => (
                <div key={index} className="mb-4 pl-4 border-l-2 border-gray-200">
                  <p className="font-semibold text-gray-900">{proj.name}</p>
                  <p className="text-sm text-gray-700 mt-1">{proj.description}</p>
                </div>
              ))}

              <h3 className="text-xl font-semibold mt-6 mb-2 text-gray-800">Umiejętności</h3>
              <div className="flex flex-wrap gap-2">
                {selectedProfile.skills.map((skill, index) => (
                  <span key={index} className="px-3 py-1 bg-blue-50 text-blue-700 text-sm rounded-full border border-blue-200">{skill.name}</span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
