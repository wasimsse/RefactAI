'use client';

import React, { useState, useEffect } from 'react';
import { 
  FolderOpen, 
  Trash2, 
  Play, 
  Calendar, 
  FileText, 
  GitBranch,
  Plus,
  Search,
  Filter,
  MoreVertical,
  Download,
  Upload,
  AlertCircle,
  CheckCircle,
  Clock
} from 'lucide-react';

interface Project {
  id: string;
  name: string;
  description?: string;
  sourceFiles: number;
  testFiles: number;
  createdAt: number;
  lastAnalyzed?: number;
  repositoryUrl?: string;
  status: 'active' | 'archived' | 'analyzing';
  vulnerabilities?: number;
  securityGrade?: string;
}

interface ProjectHubProps {
  onProjectSelect?: (project: Project) => void;
  onProjectDelete?: (projectId: string) => void;
  onProjectAnalyze?: (project: Project) => void;
}

export default function ProjectHub({ 
  onProjectSelect, 
  onProjectDelete, 
  onProjectAnalyze 
}: ProjectHubProps) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);

  // Load projects from localStorage
  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = () => {
    try {
      const storedProjects = localStorage.getItem('refactai-projects');
      if (storedProjects) {
        const parsedProjects = JSON.parse(storedProjects);
        setProjects(parsedProjects);
      }
    } catch (error) {
      console.error('Error loading projects:', error);
    } finally {
      setLoading(false);
    }
  };

  const saveProjects = (updatedProjects: Project[]) => {
    try {
      localStorage.setItem('refactai-projects', JSON.stringify(updatedProjects));
      setProjects(updatedProjects);
    } catch (error) {
      console.error('Error saving projects:', error);
    }
  };

  const addProject = (project: Project) => {
    const updatedProjects = [...projects, project];
    saveProjects(updatedProjects);
  };

  const deleteProject = (projectId: string) => {
    const updatedProjects = projects.filter(p => p.id !== projectId);
    saveProjects(updatedProjects);
    setShowDeleteConfirm(null);
    if (onProjectDelete) {
      onProjectDelete(projectId);
    }
  };

  const updateProject = (projectId: string, updates: Partial<Project>) => {
    const updatedProjects = projects.map(p => 
      p.id === projectId ? { ...p, ...updates } : p
    );
    saveProjects(updatedProjects);
  };

  const formatDate = (timestamp: number) => {
    return new Date(timestamp).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-600 bg-green-100';
      case 'analyzing': return 'text-blue-600 bg-blue-100';
      case 'archived': return 'text-gray-600 bg-gray-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getSecurityGradeColor = (grade: string) => {
    switch (grade?.toUpperCase()) {
      case 'A': return 'text-green-600 bg-green-100';
      case 'B': return 'text-blue-600 bg-blue-100';
      case 'C': return 'text-yellow-600 bg-yellow-100';
      case 'D': return 'text-orange-600 bg-orange-100';
      case 'F': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const filteredProjects = projects.filter(project => {
    const matchesSearch = !searchTerm || 
      project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (project.description && project.description.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const matchesFilter = filterStatus === 'all' || project.status === filterStatus;
    
    return matchesSearch && matchesFilter;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Clock className="w-8 h-8 text-gray-400 mx-auto mb-4 animate-spin" />
          <p className="text-gray-600">Loading projects...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 flex items-center">
            <FolderOpen className="w-8 h-8 text-blue-600 mr-3" />
            Project Hub
          </h2>
          <p className="text-gray-600 mt-1">
            Manage and analyze your projects
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <span className="text-sm text-gray-500">
            {projects.length} project{projects.length !== 1 ? 's' : ''}
          </span>
        </div>
      </div>

      {/* Search and Filter */}
      <div className="flex items-center space-x-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Search projects..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        <div className="flex items-center space-x-2">
          <Filter className="w-4 h-4 text-gray-400" />
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">All Projects</option>
            <option value="active">Active</option>
            <option value="analyzing">Analyzing</option>
            <option value="archived">Archived</option>
          </select>
        </div>
      </div>

      {/* Projects Grid */}
      {filteredProjects.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
          <FolderOpen className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {projects.length === 0 ? 'No Projects Yet' : 'No Projects Found'}
          </h3>
          <p className="text-gray-600 mb-4">
            {projects.length === 0 
              ? 'Clone a repository or upload a project to get started'
              : 'Try adjusting your search or filter criteria'
            }
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredProjects.map((project) => (
            <div
              key={project.id}
              className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => {
                setSelectedProject(project);
                if (onProjectSelect) {
                  onProjectSelect(project);
                }
              }}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 mb-1">
                    {project.name}
                  </h3>
                  {project.description && (
                    <p className="text-sm text-gray-600 mb-2">
                      {project.description}
                    </p>
                  )}
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(project.status)}`}>
                      {project.status}
                    </span>
                    {project.securityGrade && (
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getSecurityGradeColor(project.securityGrade)}`}>
                        Grade: {project.securityGrade}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex items-center space-x-1">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (onProjectAnalyze) {
                        onProjectAnalyze(project);
                      }
                    }}
                    className="p-2 text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-md transition-colors"
                    title="Analyze Project"
                  >
                    <Play className="w-4 h-4" />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setShowDeleteConfirm(project.id);
                    }}
                    className="p-2 text-red-600 hover:text-red-800 hover:bg-red-50 rounded-md transition-colors"
                    title="Delete Project"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              <div className="space-y-2 text-sm text-gray-600">
                <div className="flex items-center justify-between">
                  <span className="flex items-center">
                    <FileText className="w-4 h-4 mr-1" />
                    Source Files
                  </span>
                  <span className="font-medium">{project.sourceFiles}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="flex items-center">
                    <GitBranch className="w-4 h-4 mr-1" />
                    Test Files
                  </span>
                  <span className="font-medium">{project.testFiles}</span>
                </div>
                {project.vulnerabilities !== undefined && (
                  <div className="flex items-center justify-between">
                    <span className="flex items-center">
                      <AlertCircle className="w-4 h-4 mr-1" />
                      Vulnerabilities
                    </span>
                    <span className={`font-medium ${project.vulnerabilities > 0 ? 'text-red-600' : 'text-green-600'}`}>
                      {project.vulnerabilities}
                    </span>
                  </div>
                )}
                <div className="flex items-center justify-between">
                  <span className="flex items-center">
                    <Calendar className="w-4 h-4 mr-1" />
                    Created
                  </span>
                  <span className="font-medium">{formatDate(project.createdAt)}</span>
                </div>
                {project.lastAnalyzed && (
                  <div className="flex items-center justify-between">
                    <span className="flex items-center">
                      <CheckCircle className="w-4 h-4 mr-1" />
                      Last Analyzed
                    </span>
                    <span className="font-medium">{formatDate(project.lastAnalyzed)}</span>
                  </div>
                )}
              </div>

              {project.repositoryUrl && (
                <div className="mt-3 pt-3 border-t border-gray-100">
                  <p className="text-xs text-gray-500 truncate">
                    {project.repositoryUrl}
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="p-6">
              <div className="flex items-center mb-4">
                <AlertCircle className="w-6 h-6 text-red-600 mr-3" />
                <h3 className="text-lg font-semibold text-gray-900">
                  Delete Project
                </h3>
              </div>
              <p className="text-gray-600 mb-6">
                Are you sure you want to delete this project? This action cannot be undone.
              </p>
              <div className="flex items-center justify-end space-x-3">
                <button
                  onClick={() => setShowDeleteConfirm(null)}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-md transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={() => deleteProject(showDeleteConfirm)}
                  className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Export functions for external use
export const projectHubUtils = {
  addProject: (project: Project) => {
    const storedProjects = localStorage.getItem('refactai-projects');
    const projects = storedProjects ? JSON.parse(storedProjects) : [];
    projects.push(project);
    localStorage.setItem('refactai-projects', JSON.stringify(projects));
  },
  
  getProjects: (): Project[] => {
    const storedProjects = localStorage.getItem('refactai-projects');
    return storedProjects ? JSON.parse(storedProjects) : [];
  },
  
  updateProject: (projectId: string, updates: Partial<Project>) => {
    const storedProjects = localStorage.getItem('refactai-projects');
    const projects = storedProjects ? JSON.parse(storedProjects) : [];
    const updatedProjects = projects.map((p: Project) => 
      p.id === projectId ? { ...p, ...updates } : p
    );
    localStorage.setItem('refactai-projects', JSON.stringify(updatedProjects));
  },
  
  deleteProject: (projectId: string) => {
    const storedProjects = localStorage.getItem('refactai-projects');
    const projects = storedProjects ? JSON.parse(storedProjects) : [];
    const updatedProjects = projects.filter((p: Project) => p.id !== projectId);
    localStorage.setItem('refactai-projects', JSON.stringify(updatedProjects));
  }
};
