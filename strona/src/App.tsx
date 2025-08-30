// strona/src/App.tsx
import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  Home, Users, Send, User, LogOut, Loader2, X, UploadCloud, FileText, Database,
  Mail, Phone, Linkedin, Github, ThumbsUp, ThumbsDown, Folder, Plus, ChevronRight,
  ClipboardList, ArrowLeft, Building, GraduationCap, Users2, Languages, BookOpen, Star
} from 'lucide-react';

const API_BASE_URL = "http://34.70.6.174:8000";
const CANDIDATE_STATUS_OPTIONS = ["Nowy", "Screening", "Rozmowa", "Oferta", "Zatrudniony", "Odrzucony"];

// --- ZAKTUALIZOWANE INTERFEJSY ---
interface Skill { name: string; }
interface WorkExperience { position: string; company: string; start_date: string; end_date: string; description: string; technologies_used: string[]; }
interface Education { institution: string; degree: string; start_date: string; end_date: string; }
interface Project { name: string; description: string; technologies_used: string[]; }
interface Language { name: string; level: string; }
interface Publication { title: string; outlet: string | null; date: string | null; }
interface Activity { name: string; role: string | null; start_date: string | null; end_date: string | null; description: string | null; }
interface Profile {
  id: number; name: string; surname: string; email: string | null; phone: string | null; linkedin_url: string | null; github_url: string | null; description: string;
  match_score?: number; cv_filepath: string | null;
  skills: Skill[]; work_experiences: WorkExperience[]; education_history: Education[]; projects: Project[];
  languages: Language[]; publications: Publication[]; activities: Activity[];
}
interface Message { id: string; type: 'user' | 'assistant' | 'results'; content: string; timestamp: Date; results?: Profile[]; query?: string; }
interface RecruitmentProject { id: number; name: string; description: string | null; }
interface CandidateInProject extends Profile { status: string; notes: string | null; }
interface RecruitmentProjectDetail extends RecruitmentProject { candidates_with_status: CandidateInProject[]; }

// --- KOMPONENTY POMOCNICZE ---
const CareerTimeline = ({ workExperiences }: { workExperiences: WorkExperience[] }) => (
    <div className="mt-6">
        <h4 className="text-lg font-semibold text-gray-800 mb-3">Oś Czasu Kariery</h4>
        <div className="border-l-2 border-blue-200 ml-1">
            {workExperiences.map((exp, index) => (
                <div key={index} className="relative pl-6 pb-6 last:pb-0">
                    <div className="absolute -left-[5px] top-1.5 w-2 h-2 bg-blue-500 rounded-full ring-4 ring-white"></div>
                    <p className="font-semibold text-gray-900">{exp.position} w {exp.company}</p>
                    <p className="text-sm text-gray-500">{exp.start_date} - {exp.end_date}</p>
                </div>
            ))}
        </div>
    </div>
);

const CandidateComparisonModal = ({ profiles, onClose }: { profiles: Profile[], onClose: () => void }) => (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg shadow-2xl p-8 max-w-7xl w-full relative max-h-[90vh] flex flex-col">
            <button onClick={onClose} className="absolute top-4 right-4 text-gray-500 hover:text-gray-800"><X /></button>
            <h2 className="text-2xl font-bold mb-6">Porównanie Kandydatów</h2>
            <div className="flex-1 overflow-y-auto grid grid-cols-1 md:grid-cols-3 gap-6">
                {profiles.map(profile => (
                    <div key={profile.id} className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                        <h3 className="font-bold text-lg">{profile.name} {profile.surname}</h3>
                        {profile.match_score && <p className="text-blue-600 font-semibold">{profile.match_score}% dopasowania</p>}
                        <hr className="my-3"/>
                        <h4 className="font-semibold text-sm">Podsumowanie</h4>
                        <p className="text-xs text-gray-600 line-clamp-4">{profile.description}</p>
                         <hr className="my-3"/>
                        <h4 className="font-semibold text-sm">Top 5 Umiejętności</h4>
                        <div className="flex flex-wrap gap-1 mt-1">
                            {profile.skills.slice(0, 5).map(skill => <span key={skill.name} className="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full font-medium">{skill.name}</span>)}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    </div>
);

// --- WIDOKI APLIKACJI (WYDZIELONE JAKO OSOBNE KOMPONENTY) ---
const DashboardView = ({ messages, isTyping, inputValue, setInputValue, handleSendMessage, setSelectedProfile, handleFeedback, toggleComparison, comparisonList, setIsComparing, openAddToProjectModal }) => {
    const chatEndRef = useRef<HTMLDivElement>(null);
    useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, isTyping]);

    return (
        <div className="flex-1 flex flex-col h-full bg-gray-100">
            <div className="bg-white border-b border-gray-200 p-6">
                <h1 className="text-2xl font-bold text-gray-900">Witaj w SkillSense</h1>
                <p className="text-gray-600">Opisz, kogo lub czego szukasz, a ja znajdę najlepsze dopasowania.</p>
            </div>
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {messages.map((message) => (
                    <div key={message.id} className="space-y-4">
                        {message.type !== 'results' && (<div className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}><div className={`max-w-3xl rounded-lg px-4 py-3 shadow-sm ${message.type === 'user' ? 'bg-blue-600 text-white' : 'bg-white border border-gray-200 text-gray-900'}`}><p>{message.content}</p></div></div>)}
                        {message.results && message.query && (
                            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 max-w-6xl">
                                {message.results.map((profile) => (
                                    <div key={profile.id} className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-lg transition-shadow flex flex-col">
                                        <div className="flex items-center space-x-4 mb-4"><div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center flex-shrink-0"><span className="text-white font-semibold text-lg">{profile.name.charAt(0)}{profile.surname.charAt(0)}</span></div><div><h3 className="font-semibold text-gray-900">{profile.name} {profile.surname}</h3></div></div>
                                        <div className="mb-4"><div className="flex items-center justify-between text-sm"><span className="text-gray-600">Dopasowanie:</span><span className="font-semibold text-blue-600">{profile.match_score}%</span></div><div className="w-full bg-gray-200 rounded-full h-2 mt-1"><div className="bg-gradient-to-r from-green-400 to-blue-500 h-2 rounded-full" style={{ width: `${profile.match_score}%` }}></div></div></div>
                                        <div className="flex-1"></div>
                                        <div className="flex items-center justify-between mt-4">
                                            <button onClick={() => setSelectedProfile(profile)} className="bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 font-medium transition-colors text-sm">Pełny Profil</button>
                                            <div className="flex space-x-2"><button onClick={() => handleFeedback(message.query!, profile.id, 'good')} className="p-2 text-gray-400 hover:text-green-500 rounded-full hover:bg-green-50 transition-colors"><ThumbsUp className="w-5 h-5"/></button><button onClick={() => handleFeedback(message.query!, profile.id, 'bad')} className="p-2 text-gray-400 hover:text-red-500 rounded-full hover:bg-red-50 transition-colors"><ThumbsDown className="w-5 h-5"/></button></div>
                                        </div>
                                         <div className="flex items-center space-x-2 mt-4"><button onClick={() => toggleComparison(profile)} className={`w-full text-sm py-2 px-3 rounded-lg border transition-colors ${comparisonList.find(p => p.id === profile.id) ? 'bg-blue-100 border-blue-300 text-blue-800' : 'bg-white border-gray-300 hover:bg-gray-50'}`}>{comparisonList.find(p => p.id === profile.id) ? 'Usuń z porównania' : 'Do porównania'}</button><button onClick={() => openAddToProjectModal(profile)} className="w-full text-sm bg-gray-800 text-white hover:bg-black py-2 px-3 rounded-lg">Zapisz</button></div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                ))}
                {isTyping && <div className="flex justify-start"><div className="bg-white border border-gray-200 rounded-lg px-4 py-3"><div className="flex items-center space-x-2"><Loader2 className="w-4 h-4 animate-spin text-blue-600" /><span className="text-gray-600">Przetwarzam...</span></div></div></div>}
                <div ref={chatEndRef} />
            </div>
            {comparisonList.length > 1 && <div className="fixed bottom-10 right-10 z-20"><button onClick={() => setIsComparing(true)} className="bg-green-600 text-white px-6 py-3 rounded-lg shadow-lg hover:bg-green-700 transition-transform hover:scale-105 flex items-center"><Users2 className="w-5 h-5 mr-2" /> Porównaj ({comparisonList.length})</button></div>}
            <div className="border-t border-gray-200 bg-white p-6"><div className="flex space-x-4"><input type="text" value={inputValue} onChange={(e) => setInputValue(e.target.value)} onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()} placeholder="Np. 'student informatyki z C++...'" className="flex-1 border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500" disabled={isTyping} /><button onClick={handleSendMessage} disabled={isTyping || !inputValue.trim()} className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center space-x-2"><Send className="w-4 h-4" /> <span>Wyślij</span></button></div></div>
        </div>
    );
};

const UploadProfileView = () => {
  const [uploadType, setUploadType] = useState<'file' | 'text'>('file');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [description, setDescription] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [message, setMessage] = useState('');

  const handleSubmit = async () => {
    setIsUploading(true); setMessage('Przetwarzanie danych...');
    let endpoint = ''; let body: FormData | string;
    if (uploadType === 'file') {
      if (!selectedFile) { setMessage('Proszę najpierw wybrać plik.'); setIsUploading(false); return; }
      endpoint = `${API_BASE_URL}/upload-cv`;
      const formData = new FormData(); formData.append('file', selectedFile); body = formData;
    } else {
      if (!description.trim()) { setMessage('Proszę wprowadzić opis.'); setIsUploading(false); return; }
      endpoint = `${API_BASE_URL}/process-text`; body = JSON.stringify({ description });
    }
    try {
      const response = await fetch(endpoint, { method: 'POST', headers: uploadType === 'text' ? { 'Content-Type': 'application/json' } : {}, body: body });
      const result = await response.json();
      if (!response.ok) { throw new Error(result.detail || 'Wystąpił błąd podczas przesyłania.'); }
      setMessage(`Sukces! Przetworzono profil dla: ${result.data?.personal_info?.name || 'nowego kandydata'}.`);
    } catch (error: any) { setMessage(`Błąd: ${error.message}`);
    } finally { setIsUploading(false); }
  };

  return (
    <div className="p-6 bg-gray-100 h-full overflow-y-auto">
      <div className="max-w-3xl mx-auto bg-white p-8 rounded-lg shadow-md">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Dodaj Profil Kandydata</h1><p className="text-gray-600 mb-6">Nasz system automatycznie przeanalizuje dane i utworzy profil w bazie talentów.</p>
          <div className="flex justify-center mb-6"><div className="bg-gray-200 rounded-lg p-1 flex space-x-1"><button onClick={() => setUploadType('file')} className={`px-4 py-2 text-sm font-medium rounded-md ${uploadType === 'file' ? 'bg-white text-blue-600 shadow' : 'text-gray-600'}`}>Prześlij plik CV</button><button onClick={() => setUploadType('text')} className={`px-4 py-2 text-sm font-medium rounded-md ${uploadType === 'text' ? 'bg-white text-blue-600 shadow' : 'text-gray-600'}`}>Wpisz opis ręcznie</button></div></div>
          {uploadType === 'file' && (<div className="bg-white border-2 border-dashed border-gray-300 rounded-lg p-8 text-center"><UploadCloud className="mx-auto h-12 w-12 text-gray-400" /><p className="mt-4 text-sm text-gray-600"><label htmlFor="file-upload" className="font-medium text-blue-600 hover:text-blue-500 cursor-pointer">Wybierz plik</label> lub przeciągnij go tutaj (.pdf).</p><input id="file-upload" type="file" className="sr-only" onChange={(e: React.ChangeEvent<HTMLInputElement>) => {if(e.target.files)setSelectedFile(e.target.files[0])}} accept=".pdf"/><p className="mt-2 text-sm text-gray-500">{selectedFile?.name}</p></div>)}
          {uploadType === 'text' && (<div><textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={10} className="w-full border border-gray-300 rounded-lg p-4 focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Wklej tutaj treść swojego CV lub opisz swoje umiejętności, doświadczenie i projekty..."/></div>)}
          <div className="mt-6"><button onClick={handleSubmit} disabled={isUploading} className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center space-x-2">{isUploading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}<span>{isUploading ? 'Przetwarzanie...' : 'Wyślij i przeanalizuj'}</span></button></div>
          {message && <p className="mt-4 text-center text-sm text-gray-600">{message}</p>}
      </div>
    </div>
  );
};

const DatabaseView = ({ fetchApi, setSelectedProfile }) => {
    const [users, setUsers] = useState<Profile[]>([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedUserInDb, setSelectedUserInDb] = useState<Profile | null>(null);
    const [isLoading, setIsLoading] = useState(true);
  
    const fetchUsers = useCallback(async (query: string = '') => {
      setIsLoading(true);
      try {
        const data = await fetchApi(`/users?search_query=${encodeURIComponent(query)}`);
        if(data) setUsers(data);
      } catch (error) { console.error("Błąd:", error); } 
      finally { setIsLoading(false); }
    }, [fetchApi]);
  
    useEffect(() => { fetchUsers(); }, [fetchUsers]);
  
    return (
      <div className="flex h-full bg-white">
        <div className="w-1/3 border-r border-gray-200 flex flex-col"><div className="p-4 border-b"><input type="text" placeholder="Szukaj po imieniu lub nazwisku..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && fetchUsers(searchTerm)} className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"/></div>
          <div className="flex-1 overflow-y-auto">{isLoading ? <div className="p-4 text-center text-gray-500">Ładowanie...</div> : (<ul>{users.map(user => (<li key={user.id} onClick={() => setSelectedUserInDb(user)} className={`p-4 border-b cursor-pointer hover:bg-gray-50 ${selectedUserInDb?.id === user.id ? 'bg-blue-50 border-r-2 border-blue-500' : ''}`}><p className="font-semibold text-gray-800">{user.name} {user.surname}</p><p className="text-sm text-gray-600 truncate">{user.skills.map(s => s.name).join(', ')}</p></li>))}</ul>)}</div>
        </div>
        <div className="w-2/3 flex-1 flex flex-col">
          {selectedUserInDb ? (
            <div className="flex-1 flex h-full">
              {selectedUserInDb.cv_filepath && <div className="w-1/2 h-full border-r border-gray-200"><iframe src={`${API_BASE_URL}/cv/${selectedUserInDb.id}`} className="w-full h-full border-none" title={`CV of ${selectedUserInDb.name}`}/></div>}
              <div className={`p-6 overflow-y-auto ${selectedUserInDb.cv_filepath ? 'w-1/2' : 'w-full'}`}>
                <button onClick={() => setSelectedProfile(selectedUserInDb)} className="text-blue-600 hover:underline cursor-pointer text-sm">Zobacz pełny, interaktywny profil &rarr;</button>
                <h2 className="text-2xl font-bold text-gray-900 mt-4">{selectedUserInDb.name} {selectedUserInDb.surname}</h2>
                <div className="text-sm text-gray-500 mt-1"><p>{selectedUserInDb.email}</p><p>{selectedUserInDb.phone}</p></div>
                <h3 className="text-lg font-semibold mt-6 mb-2 text-gray-800">Podsumowanie</h3><p className="text-gray-700 leading-relaxed">{selectedUserInDb.description}</p>
                <h3 className="text-lg font-semibold mt-6 mb-2 text-gray-800">Doświadczenie</h3>{selectedUserInDb.work_experiences.map((exp, index) => (<div key={index} className="mb-4"><div className="flex items-center"><Building className="w-4 h-4 mr-2 text-gray-400"/><p className="font-semibold">{exp.position} w {exp.company}</p></div><p className="text-sm text-gray-500 ml-6">{exp.start_date} - {exp.end_date}</p></div>))}
                <h3 className="text-lg font-semibold mt-6 mb-2 text-gray-800">Umiejętności</h3><div className="flex flex-wrap gap-2">{selectedUserInDb.skills.map((skill, index) => (<span key={index} className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full font-medium">{skill.name}</span>))}</div>
              </div>
            </div>
          ) : (<div className="flex items-center justify-center h-full text-gray-500"><p>Wybierz kandydata z listy, aby zobaczyć szczegóły.</p></div>)}
        </div>
      </div>
    );
};


// --- GŁÓWNY KOMPONENT ---
function App() {
  const [activeView, setActiveView] = useState('dashboard');
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [selectedProfile, setSelectedProfile] = useState<Profile | null>(null);
  const [comparisonList, setComparisonList] = useState<Profile[]>([]);
  const [isComparing, setIsComparing] = useState(false);
  const [interviewQuestions, setInterviewQuestions] = useState<string[]>([]);
  const [isGeneratingQuestions, setIsGeneratingQuestions] = useState(false);
  const [projects, setProjects] = useState<RecruitmentProject[]>([]);
  const [isAddToProjectModalOpen, setIsAddToProjectModalOpen] = useState(false);
  const [candidateToAdd, setCandidateToAdd] = useState<Profile | null>(null);
  const [isNewProjectModalOpen, setIsNewProjectModalOpen] = useState(false);
  const [currentProject, setCurrentProject] = useState<RecruitmentProjectDetail | null>(null);

  const fetchApi = useCallback(async (url: string, options: RequestInit = {}) => {
      try {
          const response = await fetch(`${API_BASE_URL}${url}`, options);
          if (!response.ok) throw new Error(`Błąd serwera: ${response.statusText}`);
          if (response.status === 204 || response.headers.get("content-length") === "0") return null;
          return response.json();
      } catch (error) { console.error(`Błąd API dla ${url}:`, error); throw error; }
  }, []);

  const fetchProjects = useCallback(async () => {
    const data = await fetchApi('/projects');
    if (data) setProjects(data);
  }, [fetchApi]);

  const fetchProjectDetails = useCallback(async (projectId: number) => {
    const data = await fetchApi(`/projects/${projectId}`);
    if (data) setCurrentProject(data);
  }, [fetchApi]);

  useEffect(() => { setMessages([{ id: '1', type: 'assistant', content: 'Dzień dobry! Jestem asystentem SkillSense, gotowym do działania.', timestamp: new Date() }]); }, []);
  useEffect(() => { if (activeView === 'projects' && !currentProject) { fetchProjects(); } }, [activeView, currentProject, fetchProjects]);

  const handleSendMessage = useCallback(async () => {
    if (!inputValue.trim() || isTyping) return;
    const userMessage: Message = { id: Date.now().toString(), type: 'user', content: inputValue, timestamp: new Date() };
    setMessages(prev => [...prev, userMessage]);
    const currentInputValue = inputValue;
    setInputValue('');
    setIsTyping(true);
    try {
      const data = await fetchApi(`/search?query=${encodeURIComponent(currentInputValue)}`);
      const assistantResponse: Message = { id: (Date.now() + 1).toString(), type: 'assistant', content: data.summary, timestamp: new Date() };
      const resultsMessage: Message = { id: (Date.now() + 2).toString(), type: 'results', content: '', timestamp: new Date(), results: data.profiles, query: currentInputValue };
      setMessages(prev => [...prev, assistantResponse, resultsMessage]);
    } catch (error) {
      const errorMessage: Message = { id: (Date.now() + 1).toString(), type: 'assistant', content: 'Wystąpił błąd podczas połączenia z serwerem.', timestamp: new Date() };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  }, [inputValue, isTyping, fetchApi]);

  const handleFeedback = useCallback(async (query: string, rated_user_id: number, rating: 'good' | 'bad') => {
      await fetchApi('/feedback', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query, rated_user_id, rating }), });
  }, [fetchApi]);

  const toggleComparison = (profile: Profile) => { setComparisonList(prev => prev.find(p => p.id === profile.id) ? prev.filter(p => p.id !== profile.id) : [...prev, profile]); };
  
  const handleGenerateQuestions = useCallback(async (user_id: number, query: string) => {
    setIsGeneratingQuestions(true); setInterviewQuestions([]);
    try {
      const data = await fetchApi('/generate-interview-questions', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ user_id, query }) });
      if (data) setInterviewQuestions(data);
    } catch (error) {
      setInterviewQuestions(["Nie udało się wygenerować pytań."]);
    } finally {
      setIsGeneratingQuestions(false);
    }
  }, [fetchApi]);

  const openAddToProjectModal = (profile: Profile) => { setCandidateToAdd(profile); setIsAddToProjectModalOpen(true); fetchProjects(); };
  
  const handleAddCandidateToProject = async (projectId: number) => {
      if (!candidateToAdd) return;
      await fetchApi(`/projects/${projectId}/candidates`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ user_id: candidateToAdd.id }) });
      setIsAddToProjectModalOpen(false); setCandidateToAdd(null);
  };
  
  const handleCreateProject = async (event: React.FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      const formData = new FormData(event.currentTarget);
      await fetchApi('/projects', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: formData.get('name'), description: formData.get('description') }) });
      setIsNewProjectModalOpen(false); fetchProjects();
  };

  const navigationItems = [
    { id: 'dashboard', icon: Home, label: 'Dashboard' },
    { id: 'projects', icon: Folder, label: 'Projekty' },
    { id: 'upload-cv', icon: FileText, label: 'Dodaj Profil' },
    { id: 'database', icon: Database, label: 'Baza Kandydatów' },
  ];
  
  const renderActiveView = () => {
    if (currentProject) {
        return (
            <div className="p-6 h-full flex flex-col bg-gray-50">
                <button onClick={() => setCurrentProject(null)} className="text-blue-600 mb-4 flex items-center hover:underline"><ArrowLeft className="w-4 h-4 mr-1"/> Wróć do listy projektów</button>
                <h1 className="text-3xl font-bold">{currentProject.name}</h1><p className="text-gray-500 mb-6">{currentProject.description}</p>
                <div className="flex-1 overflow-y-auto space-y-4">
                    {currentProject.candidates_with_status.length > 0 ? currentProject.candidates_with_status.map(candidate => (
                        <div key={candidate.id} className="bg-white p-4 rounded-lg border flex justify-between items-start">
                           <div><h3 className="font-bold">{candidate.name} {candidate.surname}</h3><p className="text-sm text-gray-600">{candidate.email}</p></div>
                           <div className="text-right"><select defaultValue={candidate.status} className="p-1 border rounded-md text-sm">{CANDIDATE_STATUS_OPTIONS.map(opt => <option key={opt} value={opt}>{opt}</option>)}</select></div>
                        </div>
                    )) : <p className="text-gray-500 text-center mt-10">Brak kandydatów w tym projekcie.</p>}
                </div>
            </div>
        )
    }

    switch (activeView) {
      case 'dashboard': return <DashboardView messages={messages} isTyping={isTyping} inputValue={inputValue} setInputValue={setInputValue} handleSendMessage={handleSendMessage} setSelectedProfile={setSelectedProfile} handleFeedback={handleFeedback} toggleComparison={toggleComparison} comparisonList={comparisonList} setIsComparing={setIsComparing} openAddToProjectModal={openAddToProjectModal} />;
      case 'projects': return (
          <div className="p-6 h-full flex flex-col bg-gray-50">
              <div className="flex justify-between items-center mb-6"><h1 className="text-3xl font-bold">Projekty Rekrutacyjne</h1><button onClick={() => setIsNewProjectModalOpen(true)} className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center hover:bg-blue-700"><Plus className="w-4 h-4 mr-2"/>Nowy Projekt</button></div>
              <div className="flex-1 overflow-y-auto space-y-4">{projects.map(project => (<div key={project.id} onClick={() => fetchProjectDetails(project.id)} className="bg-white p-4 rounded-lg border hover:shadow-lg hover:border-blue-500 cursor-pointer transition-all"><div className="flex justify-between items-center"><div><h2 className="font-bold text-lg text-gray-800">{project.name}</h2><p className="text-sm text-gray-500">{project.description}</p></div><ChevronRight className="text-gray-400"/></div></div>))}</div>
          </div>
      );
      case 'upload-cv': return <UploadProfileView />;
      case 'database': return <DatabaseView fetchApi={fetchApi} setSelectedProfile={setSelectedProfile} />;
      default: return <div className="p-6">Wybierz opcję z menu</div>;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
        <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
            <div className="p-6 border-b border-gray-200"><h1 className="text-xl font-bold text-blue-700 flex items-center"><ClipboardList className="mr-2"/>SkillSense</h1><p className="text-xs text-gray-500 mt-1">Politechnika Rzeszowska</p></div>
            <nav className="flex-1 p-4"><ul className="space-y-2">{navigationItems.map((item) => (<li key={item.id}><a href="#" onClick={(e) => { e.preventDefault(); setActiveView(item.id); setCurrentProject(null); }} className={`flex items-center px-4 py-3 rounded-lg transition-colors ${activeView === item.id ? 'bg-blue-50 text-blue-700 border border-blue-200' : 'text-gray-600 hover:bg-gray-50'}`}><item.icon className="w-5 h-5 mr-3" /><span className="text-sm font-medium">{item.label}</span></a></li>))}</ul></nav>
            <div className="p-4 border-t border-gray-200"><div className="flex items-center space-x-3 mb-3"><div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center"><User className="w-4 h-4 text-white" /></div><div><p className="text-sm font-medium text-gray-900">Jan Kowalski</p><p className="text-xs text-gray-500">Administrator</p></div></div><button className="flex items-center text-sm text-gray-500 hover:text-gray-700"><LogOut className="w-4 h-4 mr-2" /> Wyloguj</button></div>
        </div>
        <div className="flex-1 flex flex-col h-screen overflow-y-hidden">{renderActiveView()}</div>
        {isComparing && <CandidateComparisonModal profiles={comparisonList} onClose={() => { setIsComparing(false); setComparisonList([]); }} />}
        {isAddToProjectModalOpen && candidateToAdd && (
          <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
              <div className="bg-white rounded-lg p-6 w-full max-w-md">
                  <h2 className="text-xl font-bold mb-4">Dodaj {candidateToAdd.name} do projektu</h2>
                  <div className="space-y-2 max-h-60 overflow-y-auto">{projects.map(p => <button key={p.id} onClick={() => handleAddCandidateToProject(p.id)} className="w-full text-left p-3 bg-gray-100 hover:bg-gray-200 rounded-lg">{p.name}</button>)}</div>
                   <button onClick={() => setIsAddToProjectModalOpen(false)} className="mt-4 w-full text-center p-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300">Anuluj</button>
              </div>
          </div>
        )}
        {isNewProjectModalOpen && (
          <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
              <form onSubmit={handleCreateProject} className="bg-white rounded-lg p-6 w-full max-w-md">
                  <h2 className="text-xl font-bold mb-4">Stwórz nowy projekt</h2>
                  <input name="name" required placeholder="Nazwa projektu" className="w-full p-2 border rounded-lg mb-4"/>
                  <textarea name="description" placeholder="Opis (opcjonalnie)" className="w-full p-2 border rounded-lg mb-4"></textarea>
                  <div className="flex justify-end space-x-2"><button type="button" onClick={() => setIsNewProjectModalOpen(false)} className="p-2 bg-gray-200 rounded-lg">Anuluj</button><button type="submit" className="p-2 bg-blue-600 text-white rounded-lg">Stwórz</button></div>
              </form>
          </div>
        )}
        {selectedProfile && (
            <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
                <div className="bg-white rounded-lg shadow-2xl p-8 max-w-4xl w-full relative max-h-[90vh] flex flex-col">
                    <button onClick={() => setSelectedProfile(null)} className="absolute top-4 right-4 text-gray-500 hover:text-gray-800"><X /></button>
                    <div className="flex items-center space-x-6 mb-6 flex-shrink-0">
                        <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center"><span className="text-white font-bold text-3xl">{selectedProfile.name.charAt(0)}{selectedProfile.surname.charAt(0)}</span></div>
                        <div>
                            <h2 className="text-3xl font-bold text-gray-900">{selectedProfile.name} {selectedProfile.surname}</h2>
                            <div className="flex flex-wrap gap-x-4 gap-y-1 text-gray-500 mt-2">
                                {selectedProfile.email && <div className="flex items-center"><Mail className="w-4 h-4 mr-2"/>{selectedProfile.email}</div>}
                                {selectedProfile.phone && <div className="flex items-center"><Phone className="w-4 h-4 mr-2"/>{selectedProfile.phone}</div>}
                                {selectedProfile.linkedin_url && <a href={selectedProfile.linkedin_url} target="_blank" rel="noopener noreferrer" className="flex items-center hover:text-blue-600"><Linkedin className="w-4 h-4 mr-2"/> LinkedIn</a>}
                                {selectedProfile.github_url && <a href={selectedProfile.github_url} target="_blank" rel="noopener noreferrer" className="flex items-center hover:text-blue-600"><Github className="w-4 h-4 mr-2"/> GitHub</a>}
                            </div>
                        </div>
                    </div>
                    <div className="overflow-y-auto pr-4 -mr-4 space-y-6">
                        <div><h3 className="text-xl font-semibold mb-2 text-gray-800 flex items-center"><User className="w-5 h-5 mr-2 text-blue-500"/> Podsumowanie</h3><p className="text-gray-700 leading-relaxed pl-7">{selectedProfile.description}</p></div>
                        <div><h3 className="text-xl font-semibold mb-3 text-gray-800 flex items-center"><GraduationCap className="w-5 h-5 mr-2 text-blue-500"/> Edukacja</h3><div className="border-l-2 border-gray-200 ml-2 space-y-4">{selectedProfile.education_history.map((edu, i) => (<div key={i} className="pl-6 relative"><div className="absolute -left-[5px] top-1.5 w-2 h-2 bg-gray-500 rounded-full ring-4 ring-white"></div><p className="font-semibold text-gray-900">{edu.institution}</p><p className="text-sm text-gray-700">{edu.degree}</p><p className="text-sm text-gray-500">{edu.start_date} - {edu.end_date}</p></div>))}</div></div>
                        <div><h3 className="text-xl font-semibold mb-3 text-gray-800 flex items-center"><Building className="w-5 h-5 mr-2 text-blue-500"/> Doświadczenie</h3><div className="border-l-2 border-blue-200 ml-2 space-y-4">{selectedProfile.work_experiences.map((exp, i) => (<div key={i} className="pl-6 relative"><div className="absolute -left-[5px] top-1.5 w-2 h-2 bg-blue-500 rounded-full ring-4 ring-white"></div><p className="font-semibold text-gray-900">{exp.position} w {exp.company}</p><p className="text-sm text-gray-500">{exp.start_date} - {exp.end_date}</p></div>))}</div></div>
                        <div><h3 className="text-xl font-semibold mb-3 text-gray-800 flex items-center"><Star className="w-5 h-5 mr-2 text-blue-500"/> Działalność Dodatkowa</h3><div className="border-l-2 border-gray-200 ml-2 space-y-4">{selectedProfile.activities.map((act, i) => (<div key={i} className="pl-6 relative"><div className="absolute -left-[5px] top-1.5 w-2 h-2 bg-gray-500 rounded-full ring-4 ring-white"></div><p className="font-semibold text-gray-900">{act.name} ({act.role})</p><p className="text-sm text-gray-500">{act.start_date} - {act.end_date}</p></div>))}</div></div>
                        <div><h3 className="text-xl font-semibold mb-3 text-gray-800 flex items-center"><Languages className="w-5 h-5 mr-2 text-blue-500"/> Języki</h3><div className="flex flex-wrap gap-2 pl-7">{selectedProfile.languages.map((lang, i) => (<span key={i} className="px-3 py-1 bg-gray-100 text-gray-800 text-sm rounded-full font-medium">{lang.name} - {lang.level}</span>))}</div></div>
                        <div><h3 className="text-xl font-semibold mb-3 text-gray-800 flex items-center"><BookOpen className="w-5 h-5 mr-2 text-blue-500"/> Publikacje</h3><ul className="list-disc pl-12 space-y-1">{selectedProfile.publications.map((pub, i) => (<li key={i} className="text-sm text-gray-700">{pub.title} <span className="text-gray-500">({pub.outlet}, {pub.date})</span></li>))}</ul></div>
                        <div className="mt-6"><h3 className="text-xl font-semibold mb-2 text-gray-800">Sugerowane Pytania Rekrutacyjne</h3><button onClick={() => handleGenerateQuestions(selectedProfile.id, "IT expert")} disabled={isGeneratingQuestions} className="bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50">{isGeneratingQuestions ? <Loader2 className="w-5 h-5 animate-spin" /> : "Generuj Pytania"}</button>{interviewQuestions.length > 0 && <ul className="list-disc pl-5 mt-4 space-y-2 text-gray-700">{interviewQuestions.map((q, i) => <li key={i}>{q}</li>)}</ul>}</div>
                    </div>
                </div>
            </div>
        )}
    </div>
  );
}

export default App;
