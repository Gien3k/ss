// src/components/DatabaseView.tsx
import React, { useState, useEffect } from 'react';
import { Profile } from '../types.ts';
import apiClient from '../apiClient.ts';
import { Mail, Phone, Linkedin, Github, Sparkles, Briefcase, GraduationCap, Code, BookOpen, Award, Languages, List, Loader2 } from 'lucide-react';

// --- Komponenty pomocnicze (bez zmian) ---
const Section = ({ title, icon, children, className = "" }: { title: string, icon: React.ReactNode, children: React.ReactNode, className?: string }) => (
    <div className={`mt-6 ${className}`}>
        <h3 className="text-lg font-semibold mb-3 text-gray-800 border-b pb-2 flex items-center">
            {icon} <span className="ml-2">{title}</span>
        </h3>
        {children}
    </div>
);

const DetailPanel = ({ user }: { user: Profile }) => (
    <div className="p-6">
      <h2 className="text-2xl font-bold text-gray-900">{user.name} {user.surname}</h2>
      <div className="flex flex-wrap gap-x-4 gap-y-2 text-sm text-gray-600 mt-2">
          {user.email && <div className="flex items-center"><Mail className="w-4 h-4 mr-2"/> {user.email}</div>}
          {user.phone && <div className="flex items-center"><Phone className="w-4 h-4 mr-2"/> {user.phone}</div>}
          {user.linkedin_url && <a href={user.linkedin_url} target="_blank" rel="noopener noreferrer" className="flex items-center hover:text-blue-600"><Linkedin className="w-4 h-4 mr-2"/> LinkedIn</a>}
          {user.github_url && <a href={user.github_url} target="_blank" rel="noopener noreferrer" className="flex items-center hover:text-blue-600"><Github className="w-4 h-4 mr-2"/> GitHub</a>}
      </div>

      {user.ai_summary && (
        <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h3 className="text-lg font-semibold mb-2 text-blue-800 flex items-center">
                <Sparkles className="w-5 h-5 mr-2 text-blue-600"/> Podsumowanie AI
            </h3>
            <p className="text-gray-800 leading-relaxed text-sm">{user.ai_summary}</p>
        </div>
      )}
      
      {user.work_experiences?.length > 0 && (
        <Section title="Doświadczenie zawodowe" icon={<Briefcase size={20} />}>
            {user.work_experiences.map((exp, i) => (
                <div key={i} className="mb-4 pl-2 border-l-2 border-gray-200 ml-2">
                    <p className="font-semibold text-gray-800">{exp.position} w {exp.company}</p>
                    <p className="text-sm text-gray-500">{exp.start_date} - {exp.end_date}</p>
                    <p className="text-sm text-gray-700 mt-1 whitespace-pre-wrap">{exp.description}</p>
                </div>
            ))}
        </Section>
      )}

      {user.education_history?.length > 0 && ( <Section title="Edukacja" icon={<GraduationCap size={20} />}>{ user.education_history.map((edu, i) => <div key={i} className="mb-3 pl-2 border-l-2 border-gray-200 ml-2"><p className="font-semibold">{edu.institution}</p><p className="text-sm">{edu.degree}</p></div>) }</Section> )}
      {user.projects?.length > 0 && ( <Section title="Projekty i Osiągnięcia" icon={<Code size={20} />}>{ user.projects.map((proj, i) => <div key={i} className="mb-3 pl-2 border-l-2 border-gray-200 ml-2"><p className="font-semibold">{proj.name}</p><p className="text-sm">{proj.description}</p></div>) }</Section> )}
      {user.skills?.length > 0 && ( <Section title="Umiejętności" icon={<Sparkles size={20} />}><div className="flex flex-wrap gap-2 pt-2">{user.skills.map((skill, i) => <span key={i} className="px-3 py-1 bg-blue-50 text-blue-700 text-sm rounded-full border border-blue-200">{skill.name}</span>)}</div></Section> )}
      {user.languages?.length > 0 && ( <Section title="Języki" icon={<Languages size={20} />}><ul className="list-disc pl-5">{user.languages.map((lang, i) => <li key={i} className="mb-1 text-sm">{lang.name} - {lang.level}</li>)}</ul></Section> )}
      {user.publications?.length > 0 && ( <Section title="Publikacje" icon={<BookOpen size={20} />}>{ user.publications.map((pub, i) => <div key={i} className="mb-3 pl-2 border-l-2 border-gray-200 ml-2"><p className="font-semibold">{pub.title}</p><p className="text-sm">{pub.outlet} ({pub.date})</p></div>) }</Section> )}
    </div>
);

const DatabaseView = () => {
    const [users, setUsers] = useState<Profile[]>([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedUser, setSelectedUser] = useState<Profile | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    
    // --- NOWE ZMIENNE STANU DLA PDF ---
    const [pdfUrl, setPdfUrl] = useState<string | null>(null);
    const [isPdfLoading, setIsPdfLoading] = useState<boolean>(false);

    const fetchUsers = async (query: string = '') => {
        setIsLoading(true);
        setError(null);
        try {
            const response = await apiClient.get('/users', { 
                params: { search: query, skip: 0, limit: 100 } 
            });
            setUsers(response.data.items);
        } catch (err) {
            setError("Nie udało się załadować listy kandydatów.");
        } finally {
            setIsLoading(false);
        }
    };
    
    useEffect(() => {
        fetchUsers();
    }, []);

    // --- NOWY EFEKT DO POBIERANIA PDF ---
    useEffect(() => {
        // Funkcja czyszcząca poprzedni URL, aby uniknąć wycieków pamięci
        if (pdfUrl) {
            URL.revokeObjectURL(pdfUrl);
            setPdfUrl(null);
        }

        if (selectedUser?.cv_filepath) {
            const fetchPdf = async () => {
                setIsPdfLoading(true);
                try {
                    // Używamy apiClient, który doda token autoryzacyjny
                    const response = await apiClient.get(`/cv/${selectedUser.id}`, {
                        responseType: 'blob', // Prosimy o surowe dane (plik)
                    });
                    // Tworzymy bezpieczny, tymczasowy URL z pobranych danych
                    const url = URL.createObjectURL(response.data);
                    setPdfUrl(url);
                } catch (error) {
                    console.error("Nie udało się załadować pliku PDF", error);
                    setPdfUrl(null);
                } finally {
                    setIsPdfLoading(false);
                }
            };
            fetchPdf();
        }
        
        // Funkcja czyszcząca przy odmontowaniu komponentu
        return () => {
            if (pdfUrl) {
                URL.revokeObjectURL(pdfUrl);
            }
        };
    }, [selectedUser]); // Ten efekt uruchomi się za każdym razem, gdy zmieni się wybrany użytkownik
    
    const handleSearch = (event: React.ChangeEvent<HTMLInputElement>) => {
        const query = event.target.value;
        setSearchTerm(query);
        const timer = setTimeout(() => { fetchUsers(query); }, 300);
        return () => clearTimeout(timer);
    };

    return (
        <div className="flex h-full bg-white">
            <div className="w-1/3 border-r border-gray-200 flex flex-col">
                {/* Panel listy użytkowników (bez zmian) */}
                <div className="p-4 border-b"><input type="text" placeholder="Szukaj..." value={searchTerm} onChange={handleSearch} className="w-full border rounded-lg px-3 py-2" /></div>
                <div className="flex-1 overflow-y-auto">
                    {isLoading && <div className="p-4 text-center">Ładowanie...</div>}
                    {error && <div className="p-4 text-center text-red-500">{error}</div>}
                    {!isLoading && !error && (
                        <ul>{users.map(user => (<li key={user.id} onClick={() => setSelectedUser(user)} className={`p-4 border-b cursor-pointer hover:bg-gray-50 ${selectedUser?.id === user.id ? 'bg-blue-50' : ''}`}><p className="font-semibold">{user.name} {user.surname}</p><p className="text-sm truncate">{user.ai_summary || 'Brak opisu'}</p></li>))}</ul>
                    )}
                </div>
            </div>
            <div className="w-2/3 flex-1 flex flex-col overflow-y-hidden">
                {selectedUser ? (
                    <div className="flex-1 flex h-full overflow-y-hidden">
                        {/* --- ZAKTUALIZOWANY PANEL PDF --- */}
                        <div className="w-1/2 h-full border-r overflow-hidden flex items-center justify-center">
                            {isPdfLoading && <Loader2 className="w-8 h-8 animate-spin text-blue-500" />}
                            {!isPdfLoading && pdfUrl && (
                                <iframe src={pdfUrl} className="w-full h-full border-none" title={`CV ${selectedUser.name}`} />
                            )}
                            {!isPdfLoading && !pdfUrl && selectedUser.cv_filepath && (
                                <div className="text-center p-4 text-gray-500">Nie udało się załadować podglądu PDF.</div>
                            )}
                             {!selectedUser.cv_filepath && (
                                <div className="text-center p-4 text-gray-500">Kandydat nie posiada pliku CV.</div>
                            )}
                        </div>
                        <div className="w-1/2 overflow-y-auto">
                             <DetailPanel user={selectedUser} />
                        </div>
                    </div>
                ) : (
                    <div className="flex items-center justify-center h-full w-full text-gray-500"><p>Wybierz kandydata z listy.</p></div>
                )}
            </div>
        </div>
    );
};

export default DatabaseView;
