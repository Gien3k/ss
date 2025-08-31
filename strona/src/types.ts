// strona/src/types.ts

export interface Skill {
  name: string;
}

export interface WorkExperience {
  position: string;
  company: string;
  start_date: string | null;
  end_date: string | null;
  description: string | null;
}

export interface Education {
  institution: string;
  degree: string | null;
  start_date: string | null;
  end_date: string | null;
}

export interface Project {
  name: string;
  description: string | null;
}

export interface Language {
    name: string;
    level: string;
}

// NOWE TYPY
export interface Publication {
    title: string;
    outlet: string | null;
    date: string | null;
}

export interface Certification {
    name: string;
    issuing_organization: string | null;
    date_issued: string | null;
}

export interface OtherData {
    title: string;
    content: string;
}

export interface Profile {
  id: number;
  name: string;
  surname: string;
  email: string | null;
  phone: string | null;
  linkedin_url: string | null;
  github_url: string | null;
  description: string | null;
  ai_summary: string | null;
  match_score?: number;
  cv_filepath: string | null;
  
  // Zaktualizowane relacje
  skills: Skill[];
  work_experiences: WorkExperience[];
  education_history: Education[];
  projects: Project[];
  languages: Language[];
  publications: Publication[];
  certifications: Certification[];
  other_data: OtherData[] | null;
}

export interface Message {
  id: string;
  type: 'user' | 'assistant' | 'results';
  content: string;
  timestamp: Date;
  results?: Profile[];
}
