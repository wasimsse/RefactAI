'use client';

import { useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Upload, GitBranch, Folder, File, Search, Filter, Eye, Download, BarChart3, Code, TestTube, Settings, Database, FileText, AlertTriangle, CheckCircle, Clock, Users, Zap, Shield, TrendingUp, Play, RefreshCw, Plus } from 'lucide-react';
import { apiClient, type Workspace, type Assessment, type Plan, type FileInfo } from '../api/client';
import { cachedApiClient } from '../api/cachedClient';
import FileViewer from '../components/FileViewer';
import ImprovedDashboard from '../components/ImprovedDashboard';
import { DashboardSkeleton } from '../components/SkeletonLoader';
import RefactoringOperations from '../components/RefactoringOperations';
import SecurityAnalysisDashboard from '../components/SecurityAnalysisDashboard';
import GitHubCloneInterface from '../components/GitHubCloneInterface';
import ProjectHub, { projectHubUtils } from '../components/ProjectHub';

interface Finding {
  id: string;
  title: string;
  description: string;
  severity: 'critical' | 'major' | 'minor';
  file: string;
  line: number;
  category: string;
}

type TabType = 'overview' | 'findings' | 'transforms' | 'files' | 'analysis' | 'security' | 'refactoring' | 'projects';

export default function DashboardPage() {
  const router = useRouter();
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [currentWorkspace, setCurrentWorkspace] = useState<Workspace | null>(null);
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [files, setFiles] = useState<FileInfo[]>([]);
  const [activeTab, setActiveTab] = useState<TabType>('analysis'); // Set default to analysis
  const [isUploading, setIsUploading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [selectedFile, setSelectedFile] = useState<FileInfo | null>(null);
  const [fileSearchTerm, setFileSearchTerm] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [loadingStep, setLoadingStep] = useState<string>('Initializing...');
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [showFileViewer, setShowFileViewer] = useState(false);
  const [fileContent, setFileContent] = useState<string>('');
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const [showCloneDialog, setShowCloneDialog] = useState(false);
  const [cloneUrl, setCloneUrl] = useState('');
  const [cloneBranch, setCloneBranch] = useState('main');

  // Helper function to create ZIP from files
  const createZipFromFiles = async (files: File[]): Promise<File> => {
    const JSZip = (await import('jszip')).default;
    const zip = new JSZip();
    
    // Add all files to the ZIP
    for (const file of files) {
      const content = await file.arrayBuffer();
      zip.file(file.name, content);
    }
    
    // Generate the ZIP file
    const zipBlob = await zip.generateAsync({ type: 'blob' });
    // Create a File-like object
    const file = Object.assign(zipBlob, {
      name: 'project.zip',
      lastModified: Date.now()
    });
    return file as File;
  };

  // Load workspaces on component mount
  useEffect(() => {
    const initializeDashboard = async () => {
      try {
        console.log('Initializing dashboard...');
        // Load existing workspaces without clearing them
        await loadWorkspaces();
      } catch (error) {
        console.error('Failed to initialize dashboard:', error);
        // On error, ensure we start with clean state
        setCurrentWorkspace(null);
        setWorkspaces([]);
        setFiles([]);
        setAssessment(null);
        setPlan(null);
      }
    };
    
    // Add timeout to prevent infinite loading
    const timeout = setTimeout(() => {
      console.log('Dashboard initialization timeout - forcing completion');
      setIsLoading(false);
      setLoadingStep('Ready');
      setLoadingProgress(100);
    }, 5000); // Reduced to 5 second timeout
    
    initializeDashboard().finally(() => {
      clearTimeout(timeout);
      setIsLoading(false);
      setLoadingStep('Ready');
      setLoadingProgress(100);
    });
  }, []);

  const loadWorkspaces = async () => {
    try {
      setLoadingStep('Loading workspaces...');
      setLoadingProgress(20);
      
      console.log('Loading workspaces...');
      const workspaceList = await cachedApiClient.getWorkspaces();
      console.log('Loaded workspaces:', workspaceList);
      setWorkspaces(workspaceList);
      setLoadingProgress(40);
      
      if (workspaceList.length === 0) {
        console.log('No workspaces found - starting with clean state');
        setCurrentWorkspace(null);
        setFiles([]);
        setAssessment(null);
        setPlan(null);
        setLoadingStep('No projects found - ready to upload');
        setLoadingProgress(100);
      } else {
        // Use the first workspace if available
        const workspace = workspaceList[0];
        setCurrentWorkspace(workspace);
        setLoadingStep('Loading project data...');
        setLoadingProgress(60);
        await loadWorkspaceData(workspace);
        setLoadingStep('Dashboard ready');
        setLoadingProgress(100);
      }
    } catch (error) {
      console.error('Failed to load workspaces:', error);
      console.error('Error details:', error);
      setWorkspaces([]);
      setCurrentWorkspace(null);
      setLoadingStep('Error loading dashboard');
      setLoadingProgress(0);
    } finally {
      // Remove artificial delay for faster loading
      console.log('Setting isLoading to false');
      setIsLoading(false);
    }
  };

  const loadWorkspaceData = async (workspace: Workspace) => {
    try {
      console.log('Loading workspace data for:', workspace.id);
      
      setLoadingStep('Loading project data...');
      setLoadingProgress(70);

      // Load all data in parallel for faster loading
      const [fileList, assessmentData, planData] = await Promise.allSettled([
        apiClient.getWorkspaceFiles(workspace.id),
        apiClient.getAssessment(workspace.id).catch(() => null),
        apiClient.getPlan(workspace.id).catch(() => null)
      ]);

      // Process results
      if (fileList.status === 'fulfilled') {
        console.log('Loaded files:', fileList.value.length);
        setFiles(fileList.value);
      }

      if (assessmentData.status === 'fulfilled' && assessmentData.value) {
        console.log('Assessment data loaded:', assessmentData.value);
        console.log('Assessment evidences count:', assessmentData.value.evidences?.length || 0);
        if (assessmentData.value.evidences && assessmentData.value.evidences.length > 0) {
          console.log('First evidence sample:', assessmentData.value.evidences[0]);
        }
        setAssessment(assessmentData.value);
      } else {
        console.log('No assessment found for workspace');
        setAssessment(null);
      }

      if (planData.status === 'fulfilled' && planData.value) {
        setPlan(planData.value);
      } else {
        console.log('No plan found for workspace');
        setPlan(null);
      }

      setLoadingProgress(100);

    } catch (error) {
      console.error('Failed to load workspace data:', error);
      setLoadingStep('Error loading project data');
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    setIsUploading(true);
    setLoadingStep('Preparing files...');
    setLoadingProgress(10);
    
    try {
      // Create a ZIP file from the selected files
      setLoadingStep('Creating project archive...');
      setLoadingProgress(20);
      const zipFile = await createZipFromFiles(Array.from(files));
      
      setLoadingStep('Uploading project...');
      setLoadingProgress(30);
      const workspace = await apiClient.uploadProject(zipFile);
      console.log('Starting analysis for workspace:', workspace.id);
      
      // Run full analysis workflow: assessment + plan generation
      setLoadingStep('Analyzing code structure...');
      setLoadingProgress(50);
      console.log('Starting assessment for workspace:', workspace.id);
      await apiClient.assessProject(workspace.id);
      console.log('Assessment completed for workspace:', workspace.id);
      
      setLoadingStep('Generating refactoring plan...');
      setLoadingProgress(80);
      console.log('Starting plan generation for workspace:', workspace.id);
      await apiClient.generatePlan(workspace.id);
      console.log('Plan generation completed for workspace:', workspace.id);
      
      setLoadingStep('Finalizing dashboard...');
      setLoadingProgress(95);
      setCurrentWorkspace(workspace);
      await loadWorkspaceData(workspace);
      setLoadingStep('Upload complete!');
      setLoadingProgress(100);
    } catch (error) {
      console.error('Failed to upload project:', error);
      setLoadingStep('Upload failed');
      setLoadingProgress(0);
      alert('Failed to upload project. Please try again.');
    } finally {
      setIsUploading(false);
      // Reset loading states immediately
      setLoadingStep('Ready');
      setLoadingProgress(0);
    }
  };

  const handleGitClone = () => {
    setShowCloneDialog(true);
  };

  const confirmGitClone = async () => {
    if (!cloneUrl.trim()) {
      alert('Please enter a repository URL');
      return;
    }

    setShowCloneDialog(false);
    setIsUploading(true);
    setLoadingStep('Cloning repository...');
    setLoadingProgress(20);
    
    try {
      setLoadingStep('Downloading repository...');
      setLoadingProgress(40);
      const workspace = await apiClient.cloneGitRepository(cloneUrl, cloneBranch);
      
      setLoadingStep('Analyzing repository...');
      setLoadingProgress(70);
      setCurrentWorkspace(workspace);
      await loadWorkspaceData(workspace);
      
      setLoadingStep('Repository ready!');
      setLoadingProgress(100);
    } catch (error) {
      console.error('Failed to clone repository:', error);
      setLoadingStep('Clone failed');
      setLoadingProgress(0);
      alert('Failed to clone repository. Please check the URL and try again.');
    } finally {
      setIsUploading(false);
      // Reset loading states immediately
      setLoadingStep('Ready');
      setLoadingProgress(0);
    }
  };

  const cancelGitClone = () => {
    setShowCloneDialog(false);
    setCloneUrl('');
    setCloneBranch('main');
  };

  const startAnalysis = async () => {
    if (!currentWorkspace) return;
    await startAnalysisWithWorkspace(currentWorkspace);
  };

  const startAnalysisWithWorkspace = async (workspace: any) => {
    setIsAnalyzing(true);
    setAnalysisProgress(0);
    setLoadingStep('Starting analysis...');

    try {
      // Step 1: Assessment
      setLoadingStep('Analyzing code quality...');
      setAnalysisProgress(20);
      await apiClient.assessProject(workspace.id);
      
      // Step 2: Plan Generation
      setLoadingStep('Generating refactoring plan...');
      setAnalysisProgress(60);
      await apiClient.generatePlan(workspace.id);
      
      // Step 3: Reload data
      setLoadingStep('Loading analysis results...');
      setAnalysisProgress(80);
      await loadWorkspaceData(workspace);
      
      setLoadingStep('Analysis complete!');
      setAnalysisProgress(100);
      
      // Show success message briefly
      setTimeout(() => {
        setLoadingStep('Ready');
        setAnalysisProgress(0);
      }, 1000);
      
    } catch (error) {
      console.error('Analysis failed:', error);
      setLoadingStep('Analysis failed');
      setAnalysisProgress(0);
      alert('Analysis failed. Please try again.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const clearCurrentProject = () => {
    setShowClearConfirm(true);
  };

  const confirmClearProject = () => {
    // Clear all current project data
    setCurrentWorkspace(null);
    setAssessment(null);
    setPlan(null);
    setFiles([]);
    setSelectedFile(null);
    setFileContent('');
    setShowFileViewer(false);
    setActiveTab('overview');
    setFileSearchTerm('');
    setAnalysisProgress(0);
    setLoadingStep('Ready');
    setLoadingProgress(0);
    
    // Clear any cached data
    if (typeof window !== 'undefined') {
      localStorage.removeItem('refactai-cache');
    }
    
    // Reset to initial state
    setIsLoading(false);
    setIsUploading(false);
    setIsAnalyzing(false);
    
    // Close confirmation dialog
    setShowClearConfirm(false);
  };

  const cancelClearProject = () => {
    setShowClearConfirm(false);
  };

  const handleFileClick = (file: FileInfo) => {
      setSelectedFile(file);
      setShowFileViewer(true);
  };

  const closeFileViewer = () => {
    setShowFileViewer(false);
    setSelectedFile(null);
    setFileContent('');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto">
          <div className="relative mb-8">
            <div className="w-24 h-24 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto shadow-2xl">
              <RefreshCw className="w-12 h-12 text-white animate-spin" />
            </div>
            <div className="absolute -inset-2 bg-gradient-to-br from-blue-500/20 to-purple-600/20 rounded-full blur-xl"></div>
          </div>
          
          <h2 className="text-2xl font-bold text-white mb-4">RefactAI Dashboard</h2>
          <p className="text-slate-300 text-lg mb-6">{loadingStep}</p>
          
          {/* Progress Bar */}
          <div className="w-full bg-slate-700 rounded-full h-3 mb-4 overflow-hidden">
            <div 
              className="bg-gradient-to-r from-blue-500 to-purple-600 h-3 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${loadingProgress}%` }}
            />
          </div>
          
          <div className="flex justify-between text-sm text-slate-400">
            <span>Progress</span>
            <span>{Math.round(loadingProgress)}%</span>
          </div>
          
          {/* Loading Steps */}
          <div className="mt-8 space-y-2">
            <div className={`flex items-center space-x-3 text-sm ${loadingProgress >= 20 ? 'text-blue-400' : 'text-slate-500'}`}>
              <div className={`w-2 h-2 rounded-full ${loadingProgress >= 20 ? 'bg-blue-400' : 'bg-slate-600'}`}></div>
              <span>Loading workspaces</span>
            </div>
            <div className={`flex items-center space-x-3 text-sm ${loadingProgress >= 60 ? 'text-blue-400' : 'text-slate-500'}`}>
              <div className={`w-2 h-2 rounded-full ${loadingProgress >= 60 ? 'bg-blue-400' : 'bg-slate-600'}`}></div>
              <span>Loading project data</span>
            </div>
            <div className={`flex items-center space-x-3 text-sm ${loadingProgress >= 90 ? 'text-blue-400' : 'text-slate-500'}`}>
              <div className={`w-2 h-2 rounded-full ${loadingProgress >= 90 ? 'bg-blue-400' : 'bg-slate-600'}`}></div>
              <span>Preparing dashboard</span>
            </div>
          </div>
          
          {/* Skip Loading Button */}
          <div className="mt-6">
            <button
              onClick={() => {
                setIsLoading(false);
                setLoadingStep('Ready');
                setLoadingProgress(100);
              }}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
            >
              Skip Loading & Continue
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Header */}
      <header className="bg-slate-900/80 backdrop-blur-sm border-b border-slate-700/50 shadow-xl">
        <div className="max-w-7xl mx-auto px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-8">
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                  <Code className="w-7 h-7 text-white" />
                </div>
                <div>
                  <h1 className="text-4xl font-black text-white tracking-tight mb-1">RefactAI</h1>
                  <p className="text-blue-400 font-semibold">Professional Java Refactoring Suite</p>
                </div>
              </div>
              <div className="flex items-center space-x-4 text-base text-slate-300">
                <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                <span className="font-semibold text-white">Dashboard</span>
                {currentWorkspace && (
                  <>
                    <span className="text-slate-500">•</span>
                    <span className="text-white font-semibold bg-slate-700 px-3 py-1 rounded-full text-sm">{currentWorkspace.name}</span>
                  </>
                )}
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <a 
                href="/" 
                className="text-slate-300 hover:text-white transition-all duration-200 px-6 py-3 rounded-xl hover:bg-slate-700/50 font-medium flex items-center group border border-slate-600 hover:border-slate-500"
              >
                <ArrowLeft className="w-4 h-4 mr-2 group-hover:-translate-x-1 transition-transform duration-200" />
                Back to Home
              </a>
              {currentWorkspace && (
                <button 
                  onClick={clearCurrentProject}
                  className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-6 py-3 rounded-xl transition-all duration-200 font-semibold shadow-lg hover:shadow-xl flex items-center border border-blue-500/50 transform hover:scale-105"
                >
                  <Plus className="w-5 h-5 mr-3" />
                  Analyze New Project
                </button>
              )}
              <button className="bg-gradient-to-r from-slate-700 to-slate-600 hover:from-slate-600 hover:to-slate-500 text-white px-6 py-3 rounded-xl transition-all duration-200 font-semibold shadow-lg hover:shadow-xl flex items-center border border-slate-600">
                <Settings className="w-5 h-5 mr-3" />
                Settings
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-8 py-12">
        {/* Project Upload Section */}
        {!currentWorkspace && (
          <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-3xl border border-slate-700/50 p-12 mb-12 shadow-2xl">
            <div className="text-center mb-12">
              <div className="flex items-center justify-center mb-8">
                <div className="w-24 h-24 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mr-6">
                  <Code className="w-12 h-12 text-white" />
                </div>
                <div className="text-left">
                  <h2 className="text-5xl font-black text-white mb-4 tracking-tight">Welcome to RefactAI</h2>
                  <p className="text-2xl text-blue-400 font-bold tracking-wide">Professional Java Refactoring Suite</p>
                </div>
              </div>
              <p className="text-xl text-slate-300 max-w-4xl mx-auto font-light leading-relaxed">
                Transform your Java codebase with AI-powered analysis. Identify code smells, plan refactoring strategies, and safely apply transformations with our assessment-first workflow.
              </p>
            </div>
            
            {/* Upload Progress */}
            {isUploading && (
              <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl border border-slate-700/50 p-8 mb-8 max-w-2xl mx-auto">
                <div className="text-center">
                  <div className="w-16 h-16 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
                    <RefreshCw className="w-8 h-8 text-blue-400 animate-spin" />
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-4">Processing Project</h3>
                  <p className="text-slate-300 mb-6">{loadingStep}</p>
                  
                  {/* Progress Bar */}
                  <div className="w-full bg-slate-700 rounded-full h-4 mb-4 overflow-hidden">
                    <div 
                      className="bg-gradient-to-r from-blue-500 to-purple-600 h-4 rounded-full transition-all duration-500 ease-out"
                      style={{ width: `${loadingProgress}%` }}
                    />
                  </div>
                  
                  <div className="flex justify-between text-sm text-slate-400">
                    <span>Progress</span>
                    <span>{Math.round(loadingProgress)}%</span>
                  </div>
                </div>
              </div>
            )}

            {/* Upload Options */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
              {/* File Upload */}
              <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl border border-slate-700/50 p-8 hover:border-blue-500/50 transition-all duration-300 group">
                <div className="text-center">
                  <div className="w-16 h-16 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-6 group-hover:bg-blue-500/30 transition-colors">
                    <Upload className="w-8 h-8 text-blue-400" />
                </div>
                  <h3 className="text-2xl font-bold text-white mb-4">Upload Project</h3>
                  <p className="text-slate-400 mb-6 leading-relaxed">
                    Select Java files, JAR archives, or entire project folders. We support Maven, Gradle, and plain Java projects.
                  </p>
                  <label className="inline-block">
                <input
                  type="file"
                      accept=".zip,.jar,.java"
                      multiple
                  className="hidden"
                      onChange={handleFileUpload}
                      disabled={isUploading}
                    />
                    <span className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white px-8 py-4 rounded-xl font-semibold transition-all duration-200 cursor-pointer shadow-lg hover:shadow-xl transform hover:scale-105 inline-flex items-center">
                      <Upload size={20} className="mr-3" />
                      {isUploading ? loadingStep : 'Select Project File'}
                    </span>
                </label>
                </div>
              </div>

              {/* Git Clone */}
              <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl border border-slate-700/50 p-8 hover:border-emerald-500/50 transition-all duration-300 group">
                <div className="text-center">
                  <div className="w-16 h-16 bg-emerald-500/20 rounded-full flex items-center justify-center mx-auto mb-6 group-hover:bg-emerald-500/30 transition-colors">
                    <GitBranch className="w-8 h-8 text-emerald-400" />
                </div>
                  <h3 className="text-2xl font-bold text-white mb-4">Clone Repository</h3>
                  <p className="text-slate-400 mb-6 leading-relaxed">
                    Import directly from GitHub, GitLab, or any Git repository. We'll clone and analyze your project automatically.
                  </p>
                  <button
                    onClick={handleGitClone}
                    disabled={isUploading}
                    className="bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white px-8 py-4 rounded-xl font-semibold transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-105 inline-flex items-center"
                  >
                    <GitBranch size={24} className="mr-3" />
                    {isUploading ? loadingStep : 'Clone & Analyze'}
                  </button>
                </div>
              </div>
            </div>
            
            {/* Features Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
              <div className="bg-slate-800/50 p-6 rounded-xl border border-slate-700/50 text-center">
                <div className="w-12 h-12 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Search className="w-6 h-6 text-blue-400" />
                </div>
                <h4 className="text-lg font-semibold text-white mb-2">Smart Detection</h4>
                <p className="text-slate-400 text-sm">AI-powered code smell detection with 95% accuracy</p>
              </div>
              
              <div className="bg-slate-800/50 p-6 rounded-xl border border-slate-700/50 text-center">
                <div className="w-12 h-12 bg-emerald-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Zap className="w-6 h-6 text-emerald-400" />
                </div>
                <h4 className="text-lg font-semibold text-white mb-2">Fast Analysis</h4>
                <p className="text-slate-400 text-sm">Analyze large codebases in seconds, not hours</p>
              </div>
              
              <div className="bg-slate-800/50 p-6 rounded-xl border border-slate-700/50 text-center">
                <div className="w-12 h-12 bg-purple-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Shield className="w-6 h-6 text-purple-400" />
                </div>
                <h4 className="text-lg font-semibold text-white mb-2">Safe Refactoring</h4>
                <p className="text-slate-400 text-sm">Risk-free transformations with rollback protection</p>
              </div>
            </div>
            
            <div className="text-center">
              <p className="text-slate-400 text-lg">
                Need help? Check out our <a href="#" className="text-blue-400 hover:text-blue-300 underline font-medium">documentation</a> or <a href="#" className="text-blue-400 hover:text-blue-300 underline font-medium">contact support</a>.
              </p>
            </div>
          </div>
        )}

        {/* Analysis Progress */}
        {isAnalyzing && (
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl border border-slate-700/50 p-8 mb-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
                <RefreshCw className="w-8 h-8 text-blue-400 animate-spin" />
              </div>
              <h3 className="text-2xl font-bold text-white mb-4">Analyzing Project</h3>
              <p className="text-slate-300 mb-6">
                {analysisProgress < 50 && 'Detecting code smells and analyzing structure...'}
                {analysisProgress >= 50 && analysisProgress < 90 && 'Generating refactoring recommendations...'}
                {analysisProgress >= 90 && 'Finalizing analysis and preparing results...'}
              </p>
              
              {/* Progress Bar */}
              <div className="w-full bg-slate-700 rounded-full h-4 mb-4 overflow-hidden">
                <div
                  className="bg-gradient-to-r from-blue-500 to-purple-600 h-4 rounded-full transition-all duration-500 ease-out"
                  style={{ width: `${analysisProgress}%` }}
                />
              </div>
              
              <div className="flex justify-between text-sm text-slate-400">
                <span>Analysis Progress</span>
                <span>{Math.round(analysisProgress)}%</span>
              </div>
            </div>
          </div>
        )}

        {/* Analysis Button */}
        {currentWorkspace && !assessment && !isAnalyzing && (
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl border border-slate-700/50 p-8 mb-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-emerald-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
                <Search className="w-8 h-8 text-emerald-400" />
              </div>
              <h3 className="text-2xl font-bold text-white mb-4">Ready to Analyze</h3>
              <p className="text-slate-300 mb-6">
                Project "{currentWorkspace.name}" has {currentWorkspace.sourceFiles} source files and {currentWorkspace.testFiles} test files.
              </p>
              <button 
                onClick={startAnalysis} 
                className="bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white px-8 py-4 rounded-xl font-semibold transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-105 inline-flex items-center"
              >
                <Search className="w-5 h-5 mr-3" />
                Start Analysis
              </button>
            </div>
          </div>
        )}

        {/* Use ImprovedDashboard component when workspace exists */}
        {currentWorkspace && (
          <ImprovedDashboard 
            workspaceId={currentWorkspace.id}
            assessment={assessment}
            plan={plan}
            files={files}
            setCurrentWorkspace={setCurrentWorkspace}
          />
        )}
      </div>

      {/* File Viewer Modal */}
      {showFileViewer && selectedFile && (
        <FileViewer
          workspaceId={currentWorkspace!.id}
          filePath={selectedFile.relativePath}
          fileName={selectedFile.name}
          onClose={closeFileViewer}
        />
      )}

      {/* Clear Project Confirmation Dialog */}
      {showClearConfirm && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-slate-800 border border-slate-700 rounded-2xl p-8 max-w-md mx-4 shadow-2xl">
            <div className="flex items-center mb-6">
              <div className="w-12 h-12 bg-amber-500/10 rounded-xl flex items-center justify-center mr-4">
                <AlertTriangle className="w-6 h-6 text-amber-400" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-white">Clear Current Project?</h3>
                <p className="text-slate-400 text-sm">This will remove all analysis data and start fresh.</p>
              </div>
            </div>
            
            <p className="text-slate-300 mb-8 leading-relaxed">
              Are you sure you want to clear the current project analysis? This action cannot be undone and you'll need to upload or clone a new project to continue.
            </p>
            
            <div className="flex space-x-4">
              <button
                onClick={cancelClearProject}
                className="flex-1 bg-slate-700 hover:bg-slate-600 text-white px-6 py-3 rounded-xl font-semibold transition-all duration-200 border border-slate-600"
              >
                Cancel
              </button>
              <button
                onClick={confirmClearProject}
                className="flex-1 bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 text-white px-6 py-3 rounded-xl font-semibold transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-105"
              >
                Clear Project
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Enhanced GitHub Clone Interface */}
      {showCloneDialog && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 border border-slate-700 rounded-2xl p-8 max-w-4xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center">
                <div className="w-12 h-12 bg-emerald-500/10 rounded-xl flex items-center justify-center mr-4">
                  <GitBranch className="w-6 h-6 text-emerald-400" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-white">Clone Repository</h3>
                  <p className="text-slate-400 text-sm">Import directly from GitHub with real-time progress tracking</p>
                </div>
              </div>
              <button
                onClick={cancelGitClone}
                className="text-slate-400 hover:text-white transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <GitHubCloneInterface 
              workspaceId={currentWorkspace?.id || 'default'}
              onCloneComplete={(workspace) => {
                console.log('Repository cloned, workspace created:', workspace);
                setShowCloneDialog(false);
                
                // Save to Project Hub
                const project = {
                  id: workspace.id,
                  name: workspace.name,
                  description: `Cloned from GitHub`,
                  sourceFiles: workspace.sourceFiles,
                  testFiles: workspace.testFiles,
                  createdAt: workspace.createdAt,
                  repositoryUrl: `https://github.com/${workspace.name}`,
                  status: 'active' as const
                };
                
                projectHubUtils.addProject(project);
                
                console.log('Setting current workspace:', workspace);
                setCurrentWorkspace(workspace);
                setShowCloneDialog(false);
                
                // Show success message
                setLoadingStep('Repository cloned successfully! Starting analysis...');
                setLoadingProgress(10);
                
                // Auto-start analysis after a short delay, using the new workspace
                setTimeout(() => {
                  console.log('Auto-starting analysis for cloned repository with workspace:', workspace.id);
                  // Call startAnalysis with the new workspace
                  startAnalysisWithWorkspace(workspace);
                }, 2000);
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
