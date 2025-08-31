// src/components/ProfileDetailModal.tsx
import React from 'react';
import { X, Mail, Phone, Linkedin, Github } from 'lucide-react';
import { Profile } from '../types';

interface ProfileDetailModalProps {
  profile: Profile;
  onClose: () => void;
}

const ProfileDetailModal: React.FC<ProfileDetailModalProps> = ({ profile, onClose }) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-2xl p-8 max-w-4xl w-full relative max-h-[90vh] flex flex-col">
        <button onClick={onClose} className="absolute top-4 right-4 text-gray-500 hover:text-gray-800">
          <X />
        </button>
        <div className="flex items-center space-x-6 mb-6 flex-shrink-0">
          <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center">
            <span className="text-white font-bold text-3xl">{profile.name.charAt(0)}{profile.surname.charAt(0)}</span>
          </div>
          <div>
            <h2 className="text-3xl font-bold text-gray-900">{profile.name} {profile.surname}</h2>
            <div className="flex flex-wrap gap-x-4 gap-y-2 text-gray-500 mt-2">
              {profile.email && <div className="flex items-center"><Mail className="w-4 h-4 mr-2"/> {profile.email}</div>}
              {profile.phone && <div className="flex items-center"><Phone className="w-4 h-4 mr-2"/> {profile.phone}</div>}
              {profile.linkedin_url && <a href={profile.linkedin_url} target="_blank" rel="noopener noreferrer" className="flex items-center hover:text-blue-600"><Linkedin className="w-4 h-4 mr-2"/> LinkedIn</a>}
              {profile.github_url && <a href={profile.github_url} target="_blank" rel="noopener noreferrer" className="flex items-center hover:text-blue-600"><Github className="w-4 h-4 mr-2"/> GitHub</a>}
            </div>
          </div>
        </div>
        <div className="overflow-y-auto pr-4">
          <h3 className="text-xl font-semibold mb-2 text-gray-800">Podsumowanie</h3>
          <p className="text-gray-700 mb-6 leading-relaxed">{profile.description}</p>
          
          <h3 className="text-xl font-semibold mb-2 text-gray-800">Doświadczenie zawodowe</h3>
          {profile.work_experiences.map((exp, index) => (
            <div key={index} className="mb-4 pl-4 border-l-2 border-blue-200">
              <p className="font-semibold text-gray-900">{exp.position} w {exp.company}</p>
              <p className="text-sm text-gray-500">{exp.start_date} - {exp.end_date}</p>
              <p className="text-sm text-gray-700 mt-1">{exp.description}</p>
            </div>
          ))}

          <h3 className="text-xl font-semibold mt-6 mb-2 text-gray-800">Projekty</h3>
          {profile.projects.map((proj, index) => (
            <div key={index} className="mb-4 pl-4 border-l-2 border-gray-200">
              <p className="font-semibold text-gray-900">{proj.name}</p>
              <p className="text-sm text-gray-700 mt-1">{proj.description}</p>
            </div>
          ))}

          <h3 className="text-xl font-semibold mt-6 mb-2 text-gray-800">Umiejętności</h3>
          <div className="flex flex-wrap gap-2">
            {profile.skills.map((skill, index) => (
              <span key={index} className="px-3 py-1 bg-blue-50 text-blue-700 text-sm rounded-full border border-blue-200">{skill.name}</span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfileDetailModal;
