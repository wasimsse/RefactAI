'use client';

import { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { 
  Code, Zap, FileText, AlertTriangle, CheckCircle, Info, XCircle,
  BarChart3, Target, Lightbulb, Search, Filter, Download, RefreshCw,
  Folder, PieChart, Eye, ChevronRight, ChevronDown, Clock, Shield,
  TrendingUp, GitBranch, Settings, Play, StopCircle, AlertCircle,
  CheckCircle2, MinusCircle, PlusCircle, ExternalLink, Copy, Edit3,
  Trash2, Star, Activity, Layers, Database, Cpu, HardDrive, Network,
  Lock, Unlock, Bug, Wrench, BookOpen, FileCode, GitCommit, Calendar,
  User, Users, Globe, Server, Monitor, Smartphone, Tablet, TestTube,
  ChevronLeft, ChevronFirst, ChevronLast, ChevronUp, X, Grid, List, Maximize2,
  Minimize2, MoreHorizontal, ArrowUpDown, Filter as FilterIcon, ArrowLeft, Brain,
  Wand2
} from 'lucide-react';
import { apiClient, FileInfo, Assessment, Plan, DependencyGraphData, FileDependencyAnalysis } from '../api/client';
import { BrandName } from './BrandLogo';
import { CodeSmellsPieChart, MetricsBarChart, QualityGauge } from './Charts';
import DependencyGraph from './DependencyGraph';
import DependencyMetrics from './DependencyMetrics';
import FilterSidebar from './FilterSidebar';
import { SkeletonCard, SkeletonChart, SkeletonFileList, SkeletonCodeSmell, FileAnalysisSkeleton, CodeSmellListSkeleton } from './SkeletonLoader';
import CodePreview from './CodePreview';
import CodeViewer from './CodeViewer';
import ErrorBoundary from './ErrorBoundary';
import RefactoringOperations from './RefactoringOperations';
import RefactoringMonitor from './RefactoringMonitor';
import LLMRefactoring from './LLMRefactoring';
import ControlledRefactoring from './ControlledRefactoring';
import SecurityAnalysisDashboard from './SecurityAnalysisDashboard';
import ProjectHub, { projectHubUtils } from './ProjectHub';
import CodeSmellsDashboard from './CodeSmellsDashboard';
import EnhancedRefactoringDashboard from './EnhancedRefactoringDashboard';

interface ImprovedDashboardProps {
  workspaceId: string;
  files: FileInfo[];
  assessment: Assessment | null;
  plan: Plan | null;
  onAnalysisComplete?: () => void;
  setCurrentWorkspace?: (workspace: any) => void;
}

export default function ImprovedDashboard({ 
  workspaceId, 
  files, 
  assessment, 
  plan, 
  onAnalysisComplete,
  setCurrentWorkspace
}: ImprovedDashboardProps) {
  const [activeView, setActiveView] = useState<'overview' | 'files' | 'analysis' | 'security' | 'enhanced' | 'enhanced-refactoring' | 'dependencies' | 'refactoring' | 'llm-refactoring' | 'controlled-refactoring' | 'monitor' | 'projects'>('overview');
  const [selectedFile, setSelectedFile] = useState<FileInfo | null>(null);
  const [fileAnalysis, setFileAnalysis] = useState<any>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const fileAnalysisRef = useRef<any>(null);
  const [fileViewMode, setFileViewMode] = useState<'grid' | 'list'>('list');
  const [searchTerm, setSearchTerm] = useState('');
  const [fileTypeFilter, setFileTypeFilter] = useState('');
  const [showOnlyCodeSmellsFiles, setShowOnlyCodeSmellsFiles] = useState(false);
  const [expandedFiles, setExpandedFiles] = useState<Set<string>>(new Set());
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set(['Method-Level Smells', 'Code Structure Smells']));
  const [currentPage, setCurrentPage] = useState(0);
  const [pageSize, setPageSize] = useState(20);
  const [sortBy, setSortBy] = useState<'name' | 'size' | 'type'>('size');
  const [isExporting, setIsExporting] = useState(false);
  const [currentView, setCurrentView] = useState<'files' | 'dashboard'>('files');
  
  // Code smell filter states
  const [smellSearchTerm, setSmellSearchTerm] = useState('');
  const [smellSeverityFilter, setSmellSeverityFilter] = useState('');
  const [smellCategoryFilter, setSmellCategoryFilter] = useState('');
  
  // Advanced filtering states
  const [showFilterSidebar, setShowFilterSidebar] = useState(false);
  const [activeFilters, setActiveFilters] = useState({
    severities: [] as string[],
    smellTypes: [] as string[],
    fileTypes: [] as string[],
    searchTerm: '',
    quickFilters: [] as string[]
  });
  
  // Dependency analysis states
  const [dependencyGraph, setDependencyGraph] = useState<DependencyGraphData | null>(null);
  const [fileDependencyAnalysis, setFileDependencyAnalysis] = useState<FileDependencyAnalysis | null>(null);
  const [loadingDependencies, setLoadingDependencies] = useState(false);
  
  // Code preview states
  const [showCodePreview, setShowCodePreview] = useState(false);
  const [showFileViewer, setShowFileViewer] = useState(false);
  const [fileContent, setFileContent] = useState<string>('');
  const [loadingFileContent, setLoadingFileContent] = useState(false);
  const [fileCodeSmells, setFileCodeSmells] = useState<any[]>([]);
  const [currentPreviewFile, setCurrentPreviewFile] = useState<FileInfo | null>(null);
  
  // Load file content for preview
  const loadFileContent = async (file: FileInfo) => {
    setLoadingFileContent(true);
    
    // Clear any existing analysis data to force fresh analysis
    setFileAnalysis(null);
    setFileCodeSmells([]);
    fileAnalysisRef.current = null;
    
    try {
      // Load file content
      const response = await apiClient.getFileContent(workspaceId, file.relativePath);
      setFileContent(response.content);
      setCurrentPreviewFile(file);
      
      // Load Enhanced Analysis data (used for metrics/details only)
      try {
        console.log('Loading Enhanced Analysis for file:', file.relativePath);
        
        // Try Enhanced Analysis first for accurate data
        // Add cache-busting timestamp to ensure fresh analysis
        const timestamp = Date.now();
        const analysisResponse = await apiClient.analyzeFileEnhanced(workspaceId, file.relativePath);
        console.log('✅ Enhanced analysis loaded:', analysisResponse);
        console.log('🔍 Analysis timestamp:', timestamp);
        
        // Set the analysis data for display (but do NOT use its count if assessment is available)
        setFileAnalysis(analysisResponse);

        // Prefer assessment evidences for consistent counts
        const evidences = (assessment?.evidences || []).filter((evidence: any) => {
          const filePath = evidence.pointer?.file;
          if (!filePath) return false;
          const norm = (p: string) => String(p).replace(/\\\\/g, '/').toLowerCase();
          const ev = norm(filePath);
          const rel = norm(file.relativePath);
          const fileName = file.name.toLowerCase();
          const exactMatch = ev === rel;
          const endsWithMatch = ev.endsWith('/' + fileName) && ev.includes('src/');
          const containsMatch = ev.includes('/' + fileName) && ev.includes('src/');
          return exactMatch || endsWithMatch || containsMatch;
        });

        if (evidences.length > 0) {
          const formatted = evidences.map((e: any) => ({
            startLine: e.pointer?.startLine || 1,
            endLine: e.pointer?.endLine || e.pointer?.startLine || 1,
            detectorId: e.detectorId || 'unknown',
            title: e.detectorId || 'Code Smell',
            severity: e.severity || 'MAJOR',
            summary: e.summary || 'Code quality issue detected',
            description: e.summary || 'Code quality issue detected'
          }));
          setFileCodeSmells(formatted);
        } else {
          setFileCodeSmells(analysisResponse.codeSmells || []);
        }
        
      } catch (analysisError) {
        console.warn('⚠️ Enhanced analysis failed, using assessment data:', analysisError);
        
        // Fallback to assessment data
        const fileSpecificSmells = (assessment?.evidences || []).filter((evidence: any) => {
          const filePath = evidence.pointer?.file;
          if (!filePath) return false;
          
          const norm = (p: string) => String(p).replace(/\\\\/g, '/').toLowerCase();
          const ev = norm(filePath);
          const rel = norm(file.relativePath);
          const fileName = file.name.toLowerCase();
          
          const matchesFile = ev === rel || 
                 ev.endsWith('/' + fileName) && ev.includes('src/') ||
                 ev.includes('/' + fileName) && ev.includes('src/');
          
          if (!matchesFile) return false;
          
          // Apply active filters
          const matchesSmellType = activeFilters.smellTypes.length === 0 || 
            activeFilters.smellTypes.includes(evidence.detectorId);
          const matchesSeverity = activeFilters.severities.length === 0 || 
            activeFilters.severities.includes(evidence.severity);
          
          return matchesSmellType && matchesSeverity;
        });

        const formattedCodeSmells = fileSpecificSmells.map((evidence: any) => ({
          startLine: evidence.pointer?.startLine || 1,
          endLine: evidence.pointer?.endLine || evidence.pointer?.startLine || 1,
          detectorId: evidence.detectorId || 'unknown',
          title: evidence.detectorId || 'Code Smell',
          severity: evidence.severity || 'MAJOR',
          summary: evidence.summary || 'Code quality issue detected',
          description: evidence.summary || 'Code quality issue detected'
        }));
        
        console.log('File-specific code smells:', formattedCodeSmells);
        setFileCodeSmells(formattedCodeSmells);
      }
      
      setShowCodePreview(true);
    } catch (error) {
      console.error('Failed to load file content:', error);
    } finally {
      setLoadingFileContent(false);
    }
  };

  // Start analysis with a specific workspace
  const startAnalysisWithWorkspace = async (workspace: any) => {
    try {
      console.log('Starting analysis for workspace:', workspace.id);
      
      // First, get the list of available workspaces from the backend
      const availableWorkspaces = await apiClient.listWorkspaces();
      console.log('Available workspaces:', availableWorkspaces);
      
      // Find a matching workspace in the backend
      let backendWorkspaceId = workspace.id;
      
      // If the workspace ID doesn't exist in backend, try to find a suitable one
      const existingWorkspace = availableWorkspaces.find((w: any) => w.id === workspace.id);
      if (!existingWorkspace && availableWorkspaces.length > 0) {
        // Use the most recent workspace if the exact match doesn't exist
        backendWorkspaceId = availableWorkspaces[availableWorkspaces.length - 1].id;
        console.log('Using backend workspace ID:', backendWorkspaceId);
      }
      
      // Step 1: Assessment
      const assessment = await apiClient.assessProject(backendWorkspaceId);
      console.log('Assessment completed:', assessment);
      
      // Step 2: Plan Generation
      const plan = await apiClient.generatePlan(backendWorkspaceId);
      console.log('Plan generated:', plan);
      
      // Reload workspace data to get updated files and analysis
      await loadWorkspaceData(workspace);
      
      console.log('Analysis completed successfully');
      
    } catch (error) {
      console.error('Analysis failed:', error);
      alert('Analysis failed. Please try again.');
    }
  };

  // Load workspace data
  const loadWorkspaceData = async (workspace: any) => {
    try {
      // This would typically load files, assessment, plan, etc.
      // For now, we'll just log that we're loading data
      console.log('Loading workspace data for:', workspace.id);
    } catch (error) {
      console.error('Failed to load workspace data:', error);
    }
  };

  // Load dependency analysis data
  const loadDependencyGraph = async () => {
    setLoadingDependencies(true);
    try {
      const data = await apiClient.getDependencyGraph(workspaceId);
      setDependencyGraph(data);
    } catch (error) {
      console.error('Failed to load dependency graph:', error);
    } finally {
      setLoadingDependencies(false);
    }
  };

  const loadFileDependencyAnalysis = async (filePath: string) => {
    try {
      const analysis = await apiClient.analyzeFileDependencies(workspaceId, filePath);
      setFileDependencyAnalysis(analysis);
    } catch (error) {
      console.error('Failed to load file dependency analysis:', error);
    }
  };

  // File analysis function
  const analyzeFile = async () => {
    if (!selectedFile) return;
    
    setIsAnalyzing(true);
    
    // Clear any existing analysis data to force fresh analysis
    setFileAnalysis(null);
    setFileCodeSmells([]);
    fileAnalysisRef.current = null;
    
    // Force clear browser cache for this analysis
    if (typeof window !== 'undefined') {
      // Clear any localStorage cache
      Object.keys(localStorage).forEach(key => {
        if (key.includes('analysis') || key.includes('codeSmells')) {
          localStorage.removeItem(key);
        }
      });
    }
    
    try {
      console.log('🔍 Starting FRESH file analysis for:', selectedFile.relativePath);
      
      // Always use enhanced analysis for comprehensive detection
      console.log('🔍 Using enhanced analysis for comprehensive code smell detection...');
      // Add cache-busting timestamp to ensure fresh analysis
      const timestamp = Date.now();
      const analysisResult = await apiClient.analyzeFileEnhanced(workspaceId, selectedFile.relativePath);
      console.log('✅ Enhanced analysis result:', analysisResult);
      console.log('🔍 Analysis timestamp:', timestamp);
      
      // Transform the backend data to match our UI structure
      console.log('🔍 Raw analysis result:', analysisResult);
      console.log('🔍 Code smells from result:', (analysisResult as any)?.codeSmells?.length || 0);
      console.log('🔍 Analysis result keys:', analysisResult ? Object.keys(analysisResult) : 'NO_RESULT');
      console.log('🔍 Code smells type:', typeof (analysisResult as any)?.codeSmells);
      console.log('🔍 Code smells array:', (analysisResult as any)?.codeSmells);
      
      // Debug the raw data structure
      const rawCodeSmells = (analysisResult as any)?.codeSmells;
      console.log('🔍 Raw codeSmells:', rawCodeSmells);
      console.log('🔍 Raw codeSmells length:', rawCodeSmells?.length);
      console.log('🔍 Raw codeSmells type:', typeof rawCodeSmells);
      console.log('🔍 Raw codeSmells is array:', Array.isArray(rawCodeSmells));
      
      const transformedAnalysis = {
        filePath: selectedFile.relativePath,
        // Preserve Enhanced Analysis data
        linesOfCode: (analysisResult as any)?.linesOfCode || 0,
        complexity: (analysisResult as any)?.complexity || 0,
        maintainability: (analysisResult as any)?.maintainability || 0,
        testability: (analysisResult as any)?.testability || 0,
        metrics: analysisResult.metrics || selectedFile.metrics,
        codeSmells: rawCodeSmells || [],
        qualityInsights: (analysisResult as any)?.qualityInsights || null,
        recommendations: (analysisResult as any)?.recommendations || null,
        categories: {
          'Class-Level Smells': ((analysisResult as any)?.codeSmells || []).filter((smell: any) =>
            smell.category === 'BLOATER' && (smell.type === 'LARGE_CLASS' || smell.type === 'DATA_CLASS' || smell.type === 'LAZY_CLASS')
          ).map((smell: any) => ({
            id: `${smell.type}-${smell.startLine}`,
            name: smell.title,
            description: smell.description,
            severity: smell.severity,
            suggestion: smell.recommendation,
            explanation: `This ${smell.type.toLowerCase().replace(/_/g, ' ')} affects class design and maintainability.`,
            impact: smell.severity === 'CRITICAL' ? 'High' : smell.severity === 'MAJOR' ? 'Medium' : 'Low'
          })),
          'Method-Level Smells': ((analysisResult as any)?.codeSmells || []).filter((smell: any) =>
            smell.category === 'BLOATER' && (smell.type === 'LONG_METHOD' || smell.type === 'LONG_PARAMETER_LIST') ||
            smell.category === 'CHANGE_PREVENTER' && smell.type === 'SHOTGUN_SURGERY' ||
            smell.category === 'DISPENSABLE' && smell.type === 'DUPLICATE_CODE'
          ).map((smell: any) => ({
            id: `${smell.type}-${smell.startLine}`,
            name: smell.title,
            description: smell.description,
            severity: smell.severity,
            suggestion: smell.recommendation,
            explanation: `This ${smell.type.toLowerCase().replace(/_/g, ' ')} impacts method design and code maintainability.`,
            impact: smell.severity === 'CRITICAL' ? 'High' : smell.severity === 'MAJOR' ? 'Medium' : 'Low'
          })),
          'Code Structure Smells': ((analysisResult as any)?.codeSmells || []).filter((smell: any) =>
            smell.category === 'DISPENSABLE' && (smell.type === 'COMMENTS' || smell.type === 'DEAD_CODE') ||
            smell.category === 'BLOATER' && smell.type === 'PRIMITIVE_OBSESSION'
          ).map((smell: any) => ({
            id: `${smell.type}-${smell.startLine}`,
            name: smell.title,
            description: smell.description,
            severity: smell.severity,
            suggestion: smell.recommendation,
            explanation: `This ${smell.type.toLowerCase().replace(/_/g, ' ')} affects code structure and readability.`,
            impact: smell.severity === 'CRITICAL' ? 'High' : smell.severity === 'MAJOR' ? 'Medium' : 'Low'
          })),
          'Design & Architecture Smells': ((analysisResult as any)?.codeSmells || []).filter((smell: any) =>
            smell.category === 'COUPLER' && smell.type === 'FEATURE_ENVY' ||
            smell.category === 'CHANGE_PREVENTER' && smell.type === 'DIVERGENT_CHANGE'
          ).map((smell: any) => ({
            id: `${smell.type}-${smell.startLine}`,
            name: smell.title,
            description: smell.description,
            severity: smell.severity,
            suggestion: smell.recommendation,
            explanation: `This ${smell.type.toLowerCase().replace(/_/g, ' ')} affects design and architecture patterns.`,
            impact: smell.severity === 'CRITICAL' ? 'High' : smell.severity === 'MAJOR' ? 'Medium' : 'Low'
          })),
          'Concurrency & Performance Smells': ((analysisResult as any)?.codeSmells || []).filter((smell: any) =>
            smell.category === 'COUPLER' && smell.type === 'THREAD_SAFETY' ||
            smell.category === 'BLOATER' && smell.type === 'EXCESSIVE_OBJECT_CREATION'
          ).map((smell: any) => ({
            id: `${smell.type}-${smell.startLine}`,
            name: smell.title,
            description: smell.description,
            severity: smell.severity,
            suggestion: smell.recommendation,
            explanation: `This ${smell.type.toLowerCase().replace(/_/g, ' ')} affects concurrency and performance.`,
            impact: smell.severity === 'CRITICAL' ? 'High' : smell.severity === 'MAJOR' ? 'Medium' : 'Low'
          })),
          'Testability Smells': ((analysisResult as any)?.codeSmells || []).filter((smell: any) =>
            smell.category === 'DISPENSABLE' && smell.type === 'HARD_TO_TEST' ||
            smell.category === 'BLOATER' && smell.type === 'MISSING_UNIT_TESTS'
          ).map((smell: any) => ({
            id: `${smell.type}-${smell.startLine}`,
            name: smell.title,
            description: smell.description,
            severity: smell.severity,
            suggestion: smell.recommendation,
            explanation: `This ${smell.type.toLowerCase().replace(/_/g, ' ')} affects code testability and quality assurance.`,
            impact: smell.severity === 'CRITICAL' ? 'High' : smell.severity === 'MAJOR' ? 'Medium' : 'Low'
          }))
        }
      };
      
      // Update both state and ref immediately
      setFileAnalysis(transformedAnalysis);
      fileAnalysisRef.current = transformedAnalysis;
      
      console.log('✅ File analysis completed successfully');
      console.log('📊 Transformed analysis:', transformedAnalysis);
      console.log('📊 Transformed analysis codeSmells length:', transformedAnalysis.codeSmells?.length || 0);
      console.log('📊 Transformed analysis keys:', Object.keys(transformedAnalysis));
      console.log('📊 Setting file analysis state to:', transformedAnalysis);
      console.log('📊 File analysis ref updated to:', fileAnalysisRef.current);
    } catch (error) {
      console.error('❌ Failed to analyze file:', error);
      
      // Create a fallback analysis with basic file info
      const fallbackAnalysis = {
        filePath: selectedFile.relativePath,
        metrics: selectedFile.metrics || {
          linesOfCode: 0,
          methodCount: 0,
          classCount: 0,
          complexity: 0
        },
        codeSmells: [],
        categories: {
          'No Analysis Available': [{
            id: 'no-analysis',
            name: 'Analysis Failed',
            description: 'Unable to analyze this file. This might be due to file format or backend issues.',
            severity: 'MINOR',
            suggestion: 'Try refreshing the page or check the console for errors.',
            explanation: 'The file analysis service is currently unavailable.',
            impact: 'Low'
          }]
        }
      };
      
      setFileAnalysis(fallbackAnalysis);
      
      // Show user-friendly error message
      console.warn('⚠️ Using fallback analysis due to error:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Auto-analyze when a file is selected
  useEffect(() => {
    if (selectedFile) {
      console.log('🔄 File selected, starting analysis for:', selectedFile.relativePath);
      console.log('🔄 Current activeView:', activeView);
      // Reset previous analysis and start new one
      setFileAnalysis(null);
      analyzeFile();
      loadFileDependencyAnalysis(selectedFile.relativePath);
    }
  }, [selectedFile]);

  // Also trigger analysis when switching to analysis view with a selected file
  useEffect(() => {
    if (activeView === 'analysis' && selectedFile && !fileAnalysis) {
      console.log('🔄 Switched to analysis view, starting analysis for:', selectedFile.relativePath);
      setFileAnalysis(null);
      analyzeFile();
    }
  }, [activeView, selectedFile]);

  // Debug file analysis state changes
  useEffect(() => {
    console.log('🔍 File analysis state changed:', fileAnalysis);
    if (fileAnalysis) {
      console.log('🎯 File analysis is now available with:', {
        codeSmells: fileAnalysis.codeSmells?.length || 0,
        metrics: fileAnalysis.metrics ? Object.keys(fileAnalysis.metrics).length : 0,
        qualityInsights: (fileAnalysis as any).qualityInsights ? 'Yes' : 'No'
      });
    }
  }, [fileAnalysis]);

  // Load dependency graph when dependencies view is selected
  useEffect(() => {
    if (activeView === 'dependencies' && !dependencyGraph) {
      loadDependencyGraph();
    }
  }, [activeView, dependencyGraph]);

  // Keyboard shortcut to close analysis (Escape key)
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && selectedFile) {
        setSelectedFile(null);
        setFileAnalysis(null);
        setActiveView('overview');
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [selectedFile]);

  // File type statistics
  const fileStats = useMemo(() => {
    const javaFiles = files.filter(f => f.name.endsWith('.java'));
    const resourceFiles = files.filter(f => f.relativePath.includes('/resources/'));
    const testFiles = files.filter(f => f.relativePath.includes('/test/'));
    const configFiles = files.filter(f => f.name.match(/\.(xml|yml|yaml|properties|json)$/));
    
    return {
      total: files.length,
      java: javaFiles.length,
      resources: resourceFiles.length,
      tests: testFiles.length,
      config: configFiles.length
    };
  }, [files]);

  // Filtered and sorted files
  const filteredFiles = useMemo(() => {
    
    const filtered = files.filter(file => {
      // Advanced search filter
      const matchesAdvancedSearch = !activeFilters.searchTerm || 
        file.name.toLowerCase().includes(activeFilters.searchTerm.toLowerCase()) ||
        file.relativePath.toLowerCase().includes(activeFilters.searchTerm.toLowerCase());
      
      // Legacy search filter (for backward compatibility)
      const matchesSearch = file.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           file.relativePath.toLowerCase().includes(searchTerm.toLowerCase());
      
      // Advanced file type filter
      const matchesAdvancedFileType = activeFilters.fileTypes.length === 0 || 
        activeFilters.fileTypes.some(type => file.name.endsWith(type));
      
      // Legacy file type filter
      const matchesType = !fileTypeFilter || 
        (fileTypeFilter === 'java' && file.name.endsWith('.java')) ||
        (fileTypeFilter === 'resources' && file.relativePath.includes('/resources/')) ||
        (fileTypeFilter === 'tests' && file.relativePath.includes('/test/')) ||
        (fileTypeFilter === 'config' && file.name.match(/\.(xml|yml|yaml|properties|json)$/));
      
      // REAL CODE SMELLS FILTER: Use actual assessment data with fallback
      const matchesCodeSmells = (() => {
        // If filter is disabled, show all files
        if (!showOnlyCodeSmellsFiles) {
          return true;
        }
        
        // If filter is enabled, only show files that have actual code smells in assessment data
        if (assessment?.evidences && assessment.evidences.length > 0) {
          // Check if this file has any code smells in the assessment data
          const hasRealCodeSmells = assessment.evidences.some((evidence: any) => {
            // The file path is in evidence.pointer.file (CodePointer structure)
            const filePath = evidence.pointer?.file;
            if (!filePath) return false;
            
            const norm = (p: string) => String(p).replace(/\\\\/g, '/').toLowerCase();
            const ev = norm(filePath);
            const rel = norm(file.relativePath);
            const fileName = file.name.toLowerCase();
            
            // More precise matching - require exact path match or very specific patterns
            const exactMatch = ev === rel;
            const endsWithMatch = ev.endsWith('/' + fileName) && ev.includes('src/');
            const containsMatch = ev.includes('/' + fileName) && ev.includes('src/');
            
            return exactMatch || endsWithMatch || containsMatch;
          });
          
          if (hasRealCodeSmells) {
            return true;
          }
        }
        
        // No fallback - only show files that actually have code smells
        return false;
      })();
      
      // Advanced code smell filtering by severity and type
      const matchesAdvancedCodeSmells = (() => {
        if (!assessment?.evidences || assessment.evidences.length === 0) {
          return true; // No assessment data, show all files
        }
        
        // If no smell type or severity filters are active, show all files
        if (activeFilters.smellTypes.length === 0 && activeFilters.severities.length === 0) {
          return true;
        }
        
        // Check if this file has code smells matching the filters
        const fileCodeSmells = assessment.evidences.filter((evidence: any) => {
          const filePath = evidence.pointer?.file;
          if (!filePath) return false;
          
          const norm = (p: string) => String(p).replace(/\\\\/g, '/').toLowerCase();
          const ev = norm(filePath);
          const rel = norm(file.relativePath);
          const fileName = file.name.toLowerCase();
          
          const exactMatch = ev === rel;
          const endsWithMatch = ev.endsWith('/' + fileName) && ev.includes('src/');
          const containsMatch = ev.includes('/' + fileName) && ev.includes('src/');
          
          return exactMatch || endsWithMatch || containsMatch;
        });
        
        // If file has no code smells, only show it if no filters are active
        if (fileCodeSmells.length === 0) {
          return activeFilters.smellTypes.length === 0 && activeFilters.severities.length === 0;
        }
        
        // Check if any of the file's code smells match the active filters
        return fileCodeSmells.some((evidence: any) => {
          const matchesSmellType = activeFilters.smellTypes.length === 0 || 
            activeFilters.smellTypes.includes(evidence.detectorId);
          const matchesSeverity = activeFilters.severities.length === 0 || 
            activeFilters.severities.includes(evidence.severity);
          
          return matchesSmellType && matchesSeverity;
        });
      })();
      
      return matchesSearch && matchesType && matchesCodeSmells && 
             matchesAdvancedSearch && matchesAdvancedFileType && matchesAdvancedCodeSmells;
    });


    // Sort files based on selected criteria
    return filtered.sort((a, b) => {
      switch (sortBy) {
        case 'size':
          return (b.metrics?.linesOfCode || 0) - (a.metrics?.linesOfCode || 0);
        case 'name':
          return a.name.localeCompare(b.name);
        case 'type':
          const aType = a.name.split('.').pop() || '';
          const bType = b.name.split('.').pop() || '';
          return aType.localeCompare(bType);
        default:
          return 0;
      }
    });
  }, [files, searchTerm, fileTypeFilter, showOnlyCodeSmellsFiles, sortBy, assessment, activeFilters]);

  // Paginated files
  const paginatedFiles = useMemo(() => {
    const start = currentPage * pageSize;
    return filteredFiles.slice(start, start + pageSize);
  }, [filteredFiles, currentPage, pageSize]);

  const totalPages = Math.ceil(filteredFiles.length / pageSize);

  const toggleFileExpansion = (filePath: string) => {
    const newExpanded = new Set(expandedFiles);
    if (newExpanded.has(filePath)) {
      newExpanded.delete(filePath);
    } else {
      newExpanded.add(filePath);
    }
    setExpandedFiles(newExpanded);
  };

  // CSV Export Functions
  const generateCSVContent = () => {
    const headers = [
      'File Path',
      'File Name', 
      'File Type',
      'Lines of Code',
      'Classes',
      'Methods',
      'Complexity',
      'Code Smells Count',
      'Code Smell Types',
      'Long Method Count',
      'God Class Count',
      'Duplicate Code Count',
      'Complex Method Count',
      'Long Parameter List Count',
      'Feature Envy Count',
      'Data Clumps Count',
      'Primitive Obsession Count',
      'Switch Statements Count',
      'Temporary Field Count',
      'Lazy Class Count',
      'Middle Man Count',
      'Speculative Generality Count',
      'Message Chains Count',
      'Inappropriate Intimacy Count',
      'Shotgun Surgery Count',
      'Divergent Change Count',
      'Parallel Inheritance Count',
      'Excessive Comments Count',
      'Dead Code Count',
      'Large Class Count',
      'Data Class Count',
      'Magic Numbers Count',
      'String Constants Count',
      'Inconsistent Naming Count',
      'Nested Conditionals Count',
      'Flag Arguments Count',
      'Try-Catch Hell Count',
      'Null Abuse Count',
      'Type Embedded Name Count',
      'Refused Bequest Count',
      'Empty Catch Block Count',
      'Resource Leak Count',
      'Raw Types Count',
      'Circular Dependencies Count',
      'Long Line Count',
      'String Concatenation Count',
      'Generic Exception Count',
      'Single Letter Vars Count',
      'Hardcoded Credentials Count',
      'Critical Issues',
      'Major Issues',
      'Minor Issues'
    ];

    const rows = filteredFiles.map(file => {
      // Get code smells for this file
      const evidencesForFile = (assessment?.evidences || []).filter((e: any) => {
        const filePath = e.pointer?.file;
        if (!filePath) return false;
        
        const norm = (p: string) => String(p).replace(/\\\\/g, '/').toLowerCase();
        const ev = norm(filePath);
        const rel = norm(file.relativePath);
        const fileName = file.name.toLowerCase();
        
        const exactMatch = ev === rel;
        const endsWithMatch = ev.endsWith('/' + fileName) && ev.includes('src/');
        const containsMatch = ev.includes('/' + fileName) && ev.includes('src/');
        
        return exactMatch || endsWithMatch || containsMatch;
      });

      // Count smells by type
      const smellTypeCounts = evidencesForFile.reduce((acc: any, e: any) => {
        const type = e.detectorId || e.summary || 'Unknown';
        acc[type] = (acc[type] || 0) + 1;
        return acc;
      }, {});

      // Count by severity
      const severityCounts = evidencesForFile.reduce((acc: any, e: any) => {
        const severity = e.severity || 'UNKNOWN';
        acc[severity] = (acc[severity] || 0) + 1;
        return acc;
      }, {});

      const fileType = file.name.split('.').pop() || 'unknown';
      const smellTypes = Object.keys(smellTypeCounts).join('; ');
      
      return [
        file.relativePath,
        file.name,
        fileType,
        file.metrics?.linesOfCode || 0,
        file.metrics?.classCount || 0,
        file.metrics?.methodCount || 0,
        file.metrics?.cyclomaticComplexity || 0,
        evidencesForFile.length,
        smellTypes,
        smellTypeCounts['design.long-method'] || 0,
        smellTypeCounts['design.god-class'] || 0,
        smellTypeCounts['design.duplicate-code'] || 0,
        smellTypeCounts['design.complex-method'] || 0,
        smellTypeCounts['design.long-parameter-list'] || 0,
        smellTypeCounts['design.feature-envy'] || 0,
        smellTypeCounts['design.data-clumps'] || 0,
        smellTypeCounts['design.primitive-obsession'] || 0,
        smellTypeCounts['design.switch-statements'] || 0,
        smellTypeCounts['design.temporary-field'] || 0,
        smellTypeCounts['design.lazy-class'] || 0,
        smellTypeCounts['design.middle-man'] || 0,
        smellTypeCounts['design.speculative-generality'] || 0,
        smellTypeCounts['design.message-chains'] || 0,
        smellTypeCounts['design.inappropriate-intimacy'] || 0,
        smellTypeCounts['design.shotgun-surgery'] || 0,
        smellTypeCounts['design.divergent-change'] || 0,
        smellTypeCounts['design.parallel-inheritance'] || 0,
        smellTypeCounts['design.excessive-comments'] || 0,
        smellTypeCounts['design.dead-code'] || 0,
        smellTypeCounts['design.large-class'] || 0,
        smellTypeCounts['design.data-class'] || 0,
        smellTypeCounts['design.magic-numbers'] || 0,
        smellTypeCounts['design.string-constants'] || 0,
        smellTypeCounts['design.inconsistent-naming'] || 0,
        smellTypeCounts['design.nested-conditionals'] || 0,
        smellTypeCounts['design.flag-arguments'] || 0,
        smellTypeCounts['design.try-catch-hell'] || 0,
        smellTypeCounts['design.null-abuse'] || 0,
        smellTypeCounts['design.type-embedded-name'] || 0,
        smellTypeCounts['design.refused-bequest'] || 0,
        smellTypeCounts['design.empty-catch-block'] || 0,
        smellTypeCounts['design.resource-leak'] || 0,
        smellTypeCounts['design.raw-types'] || 0,
        smellTypeCounts['design.circular-dependencies'] || 0,
        smellTypeCounts['design.long-line'] || 0,
        smellTypeCounts['design.string-concatenation'] || 0,
        smellTypeCounts['design.generic-exception'] || 0,
        smellTypeCounts['design.single-letter-vars'] || 0,
        smellTypeCounts['design.hardcoded-credentials'] || 0,
        severityCounts['CRITICAL'] || 0,
        severityCounts['MAJOR'] || 0,
        severityCounts['MINOR'] || 0
      ];
    });

    // Escape CSV values
    const escapeCSV = (value: any) => {
      if (value === null || value === undefined) return '';
      const str = String(value);
      if (str.includes(',') || str.includes('"') || str.includes('\n')) {
        return `"${str.replace(/"/g, '""')}"`;
      }
      return str;
    };

    const csvContent = [
      headers.map(escapeCSV).join(','),
      ...rows.map(row => row.map(escapeCSV).join(','))
    ].join('\n');

    return csvContent;
  };

  const exportToCSV = async () => {
    setIsExporting(true);
    try {
      const csvContent = generateCSVContent();
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
      const filename = `refactai-${workspaceId}-${timestamp}-analysis-report.csv`;
      link.setAttribute('download', filename);
      
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      console.log('CSV export completed:', filename);
    } catch (error) {
      console.error('CSV export failed:', error);
    } finally {
      setIsExporting(false);
    }
  };

  const toggleCategoryExpansion = (category: string) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(category)) {
      newExpanded.delete(category);
    } else {
      newExpanded.add(category);
    }
    setExpandedCategories(newExpanded);
  };

  // Filter code smells based on search and filter criteria
  const filterCodeSmells = (smells: any[]) => {
    return smells.filter(smell => {
      const matchesSearch = !smellSearchTerm || 
        smell.name.toLowerCase().includes(smellSearchTerm.toLowerCase()) ||
        smell.description.toLowerCase().includes(smellSearchTerm.toLowerCase()) ||
        smell.suggestion.toLowerCase().includes(smellSearchTerm.toLowerCase());
      
      const matchesSeverity = !smellSeverityFilter || smell.severity === smellSeverityFilter;
      
      return matchesSearch && matchesSeverity;
    });
  };

  // Filter categories based on category filter
  const filterCategories = (categories: any) => {
    if (!smellCategoryFilter) return categories;
    
    const filtered: any = {};
    Object.entries(categories).forEach(([category, smells]) => {
      // Check if the category matches the filter
      const categoryMatches = category.toLowerCase().includes(smellCategoryFilter.toLowerCase());
      if (categoryMatches) {
        filtered[category] = filterCodeSmells(smells as any[]);
      }
    });
    return filtered;
  };

  const getFileTypeIcon = (file: FileInfo) => {
    if (file.name.endsWith('.java')) return <FileCode className="w-4 h-4 text-blue-400" />;
    if (file.relativePath.includes('/resources/')) return <Database className="w-4 h-4 text-yellow-400" />;
    if (file.relativePath.includes('/test/')) return <TestTube className="w-4 h-4 text-green-400" />;
    if (file.name.match(/\.(xml|yml|yaml|properties|json)$/)) return <Settings className="w-4 h-4 text-purple-400" />;
    return <FileText className="w-4 h-4 text-gray-400" />;
  };

  const getFileTypeBadge = (file: FileInfo) => {
    if (file.name.endsWith('.java')) return { text: 'JAVA', color: 'bg-blue-100 text-blue-800' };
    if (file.relativePath.includes('/resources/')) return { text: 'RESOURCE', color: 'bg-yellow-100 text-yellow-800' };
    if (file.relativePath.includes('/test/')) return { text: 'TEST', color: 'bg-green-100 text-green-800' };
    if (file.name.match(/\.(xml|yml|yaml|properties|json)$/)) return { text: 'CONFIG', color: 'bg-purple-100 text-purple-800' };
    return { text: 'OTHER', color: 'bg-gray-100 text-gray-800' };
  };

  // File Analysis View Component
  const FileAnalysisView = ({ file }: { file: FileInfo }) => {
    // Check if file is suitable for Java code analysis
    const isJavaFile = file.name.endsWith('.java') || file.relativePath.includes('/java/');
    
    if (!isJavaFile) {
      return (
        <div className="h-full overflow-y-auto p-6">
          <div className="max-w-2xl mx-auto">
            <div className="bg-slate-800 rounded-xl p-8 border border-slate-700 text-center">
              <div className="w-16 h-16 bg-yellow-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                <FileText className="w-8 h-8 text-yellow-400" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">File Type Not Supported</h3>
              <p className="text-slate-300 mb-4">
                Code smell analysis is only available for Java files (.java). 
                This file ({file.name}) cannot be analyzed for Java-specific code smells.
              </p>
              <div className="bg-slate-700/50 rounded-lg p-4 text-left">
                <h4 className="text-white font-medium mb-2">Supported File Types:</h4>
                <ul className="text-slate-300 text-sm space-y-1">
                  <li>• Java source files (.java)</li>
                  <li>• Files in Java source directories</li>
                </ul>
              </div>
              <div className="mt-6">
                <button
                  onClick={() => setActiveView('files')}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg transition-colors"
                >
                  Browse Java Files
                </button>
              </div>
            </div>
          </div>
        </div>
      );
    }
    // Category name mapping for user-friendly display
    const getCategoryDisplayName = (category: string) => {
      const categoryMap: { [key: string]: { display: string; technical: string; description: string } } = {
        'BLOATER': {
          display: 'Large Code Blocks',
          technical: 'Bloater',
          description: 'Methods, classes, or parameters that have grown too large'
        },
        'DISPENSABLE': {
          display: 'Unused Code',
          technical: 'Dispensable',
          description: 'Dead code, unused variables, or redundant functionality'
        },
        'CHANGE_PREVENTER': {
          display: 'Hard to Modify',
          technical: 'Change Preventer',
          description: 'Code that is difficult to change without affecting other parts'
        },
        'HIERARCHY_ISSUE': {
          display: 'Inheritance Problems',
          technical: 'Hierarchy Issue',
          description: 'Issues with class inheritance and object-oriented design'
        },
        'ENCAPSULATION_ISSUE': {
          display: 'Data Exposure',
          technical: 'Encapsulation Issue',
          description: 'Improper data hiding and encapsulation violations'
        },
        'TESTING_ISSUE': {
          display: 'Test Problems',
          technical: 'Testing Issue',
          description: 'Issues with testability and test coverage'
        },
        'COUPLING_ISSUE': {
          display: 'Tight Coupling',
          technical: 'Coupling Issue',
          description: 'Classes that are too dependent on each other'
        },
        'COHESION_ISSUE': {
          display: 'Low Cohesion',
          technical: 'Cohesion Issue',
          description: 'Classes or methods that do too many different things'
        },
        'COUPLER': {
          display: 'Tight Coupling',
          technical: 'Coupler',
          description: 'Classes that are too dependent on each other'
        }
      };
      
      return categoryMap[category] || {
        display: category,
        technical: category,
        description: 'Code quality issue'
      };
    };

    // Organize code smells by category
    const organizeCodeSmellsByCategory = (codeSmells: any[]) => {
      const categories: { [key: string]: any[] } = {};
      
      codeSmells.forEach(smell => {
        const category = smell.category || 'Other';
        if (!categories[category]) {
          categories[category] = [];
        }
        categories[category].push(smell);
      });
      
      return categories;
    };


    const getSeverityColor = (severity: string) => {
      switch (severity) {
        case 'CRITICAL': return 'text-red-100 bg-red-500/20 border-red-500/50 shadow-red-500/20';
        case 'MAJOR': return 'text-orange-100 bg-orange-500/20 border-orange-500/50 shadow-orange-500/20';
        case 'MINOR': return 'text-yellow-100 bg-yellow-500/20 border-yellow-500/50 shadow-yellow-500/20';
        default: return 'text-gray-100 bg-gray-500/20 border-gray-500/50 shadow-gray-500/20';
      }
    };

    const getSeverityIcon = (severity: string) => {
      switch (severity) {
        case 'CRITICAL': return <AlertTriangle className="w-3 h-3" />;
        case 'MAJOR': return <AlertCircle className="w-3 h-3" />;
        case 'MINOR': return <Info className="w-3 h-3" />;
        default: return <Info className="w-3 h-3" />;
      }
    };

    return (
      <div className="space-y-6">
        {/* File Header */}
        <div className="bg-slate-800 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <h2 className="text-xl font-semibold text-white">File Analysis</h2>
              <span className={`px-2 py-1 rounded text-xs font-medium ${getFileTypeBadge(file).color}`}>
                {getFileTypeBadge(file).text}
              </span>
            </div>
            <button
              onClick={() => setSelectedFile(null)}
              className="text-slate-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          
          <div className="mb-4">
            <h3 className="text-lg font-medium text-white">{file.name}</h3>
            <p className="text-sm text-slate-400">{file.relativePath}</p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-slate-700 rounded-lg p-3 text-center">
              <div className="text-xl font-bold text-blue-400">{file.metrics.linesOfCode}</div>
              <div className="text-xs text-slate-300">Lines of Code</div>
            </div>
            <div className="bg-slate-700 rounded-lg p-3 text-center">
              <div className="text-xl font-bold text-green-400">{file.metrics.classCount}</div>
              <div className="text-xs text-slate-300">Classes</div>
            </div>
            <div className="bg-slate-700 rounded-lg p-3 text-center">
              <div className="text-xl font-bold text-yellow-400">{file.metrics.methodCount}</div>
              <div className="text-xs text-slate-300">Methods</div>
            </div>
            <div className="bg-slate-700 rounded-lg p-3 text-center">
              <div className="text-xl font-bold text-purple-400">{file.metrics.cyclomaticComplexity}</div>
              <div className="text-xs text-slate-300">Complexity</div>
            </div>
          </div>

          {/* File-Specific Charts Section */}
          {fileAnalysis && (
            <div className="space-y-6 mb-6">
              {/* Row 1: File Code Smells Analysis */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
                  <div className="flex items-center mb-4">
                    <AlertTriangle className="w-5 h-5 text-red-400 mr-2" />
                    <h3 className="text-lg font-semibold text-white">File Code Smells by Severity</h3>
                  </div>
                  <div className="h-64">
                    <CodeSmellsPieChart 
                      critical={fileAnalysis.codeSmells?.filter((s: any) => s.severity === 'CRITICAL').length || 0}
                      major={fileAnalysis.codeSmells?.filter((s: any) => s.severity === 'MAJOR').length || 0}
                      minor={fileAnalysis.codeSmells?.filter((s: any) => s.severity === 'MINOR').length || 0}
                    />
                  </div>
                </div>
                
                <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
                  <div className="flex items-center mb-4">
                    <Bug className="w-5 h-5 text-orange-400 mr-2" />
                    <h3 className="text-lg font-semibold text-white">File Code Smells by Category</h3>
                  </div>
                  <div className="h-64">
                    {fileAnalysis.codeSmells && fileAnalysis.codeSmells.length > 0 ? (
                      <div className="space-y-3">
                        {Object.entries(organizeCodeSmellsByCategory(fileAnalysis.codeSmells)).map(([category, smells]: [string, any[]]) => {
                          const categoryInfo = getCategoryDisplayName(category);
                          return (
                            <div key={category} className="flex items-center justify-between">
                              <div className="flex flex-col">
                                <span className="text-slate-300 text-sm font-medium">{categoryInfo.display}</span>
                                <span className="text-slate-500 text-xs">a.k.a {categoryInfo.technical}</span>
                              </div>
                              <div className="flex items-center space-x-2">
                                <div className="w-20 bg-slate-700 rounded-full h-2">
                                  <div 
                                    className="bg-gradient-to-r from-orange-400 to-red-500 h-2 rounded-full"
                                    style={{ width: `${Math.min(100, (smells.length / Math.max(...Object.values(organizeCodeSmellsByCategory(fileAnalysis.codeSmells)).map((s: any[]) => s.length))) * 100)}%` }}
                                  />
                                </div>
                                <span className="text-white font-semibold text-sm w-8 text-right">{smells.length}</span>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <div className="flex items-center justify-center h-full text-slate-400">
                        <div className="text-center">
                          <Bug className="w-12 h-12 mx-auto mb-2 opacity-50" />
                          <p>No code smells found in this file</p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Row 2: File Metrics and Quality */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
                  <div className="flex items-center mb-4">
                    <BarChart3 className="w-5 h-5 text-green-400 mr-2" />
                    <h3 className="text-lg font-semibold text-white">File Metrics</h3>
                  </div>
                  <div className="h-64">
                    <MetricsBarChart 
                      classes={file.metrics.classCount}
                      methods={file.metrics.methodCount}
                       comments={file.metrics.commentLines || 0}
                      lines={file.metrics.linesOfCode}
                    />
                  </div>
                </div>
                
                <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
                  <div className="flex items-center mb-4">
                    <Target className="w-5 h-5 text-purple-400 mr-2" />
                    <h3 className="text-lg font-semibold text-white">File Quality Score</h3>
                  </div>
                  <div className="h-64 flex items-center justify-center">
                    <div className="w-32 h-32">
                       <QualityGauge 
                         score={fileAnalysis.metrics?.overallScore || Math.max(0, 100 - (fileAnalysis.codeSmells?.length || 0) * 10)}
                         maxScore={100}
                         label="Quality Score"
                       />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Quality Gauge */}
          {fileAnalysis && (
            <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 mb-6">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                <Target className="w-5 h-5 mr-2 text-purple-400" />
                Code Quality Score
              </h3>
              <div className="flex justify-center">
                <div className="w-48 h-48">
                  <QualityGauge 
                    score={Math.max(0, 100 - (fileAnalysis.codeSmells?.length || 0) * 10)}
                    maxScore={100}
                    label="Quality Score"
                  />
                </div>
              </div>
            </div>
          )}

          <div className="flex space-x-3">
            <button
              onClick={analyzeFile}
              disabled={isAnalyzing}
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
            >
              {isAnalyzing ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 inline animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Code className="w-4 h-4 mr-2 inline" />
                  Analyze File
                </>
              )}
            </button>
            
            <button
              onClick={() => loadFileContent(file)}
              disabled={loadingFileContent}
              className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50 flex items-center"
            >
              {loadingFileContent ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  Loading...
                </>
              ) : (
                <>
                  <Eye className="w-4 h-4 mr-2" />
                  View Code
                </>
              )}
            </button>
            
            {fileAnalysis && (
              <button
                onClick={() => {
                  const exportData = {
                    file: file.name,
                    path: file.relativePath,
                    metrics: file.metrics,
                    codeSmells: fileAnalysis.codeSmells || [],
                    categories: fileAnalysis.categories,
                    timestamp: new Date().toISOString()
                  };
                  const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `${file.name.replace(/\.[^/.]+$/, '')}_analysis.json`;
                  document.body.appendChild(a);
                  a.click();
                  document.body.removeChild(a);
                  URL.revokeObjectURL(url);
                }}
                className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors flex items-center"
              >
                <Download className="w-4 h-4 mr-2" />
                Export
              </button>
            )}
          </div>
        </div>

        {/* Analysis Results */}
        {isAnalyzing ? (
          <div className="space-y-6">
            <FileAnalysisSkeleton />
            <CodeSmellListSkeleton />
          </div>
        ) : fileAnalysis && (
          <div className="space-y-6">
            {/* Code Smell Filters */}
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <div className="flex items-center space-x-4">
                <div className="flex-1 relative">
                  <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" />
                  <input
                    type="text"
                    placeholder="Search code smells..."
                    value={smellSearchTerm}
                    onChange={(e) => setSmellSearchTerm(e.target.value)}
                    className="w-full bg-slate-700 text-white pl-10 pr-4 py-2 rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none"
                  />
                </div>
                <select 
                  value={smellSeverityFilter}
                  onChange={(e) => setSmellSeverityFilter(e.target.value)}
                  className="bg-slate-700 text-white px-3 py-2 rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none"
                >
                  <option value="">All Severities</option>
                  <option value="CRITICAL">Critical</option>
                  <option value="MAJOR">Major</option>
                  <option value="MINOR">Minor</option>
                </select>
                <select 
                  value={smellCategoryFilter}
                  onChange={(e) => setSmellCategoryFilter(e.target.value)}
                  className="bg-slate-700 text-white px-3 py-2 rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none"
                >
                  <option value="">All Categories</option>
                  <option value="Class-Level">Class-Level</option>
                  <option value="Method-Level">Method-Level</option>
                  <option value="Code Structure">Code Structure</option>
                  <option value="Design & Architecture">Design & Architecture</option>
                  <option value="Concurrency & Performance">Concurrency & Performance</option>
                  <option value="Testability">Testability</option>
                </select>
                <button 
                  onClick={() => {
                    setSmellSearchTerm('');
                    setSmellSeverityFilter('');
                    setSmellCategoryFilter('');
                  }}
                  className="bg-slate-600 hover:bg-slate-500 text-white px-3 py-2 rounded-lg transition-colors"
                  title="Clear all filters"
                >
                  <Filter className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Code Smells by Category */}
            {(() => {
              // Use file-specific code smells instead of project-wide ones
              const fileCodeSmells = fileAnalysis?.codeSmells || [];
              const categories = organizeCodeSmellsByCategory(fileCodeSmells);
              const filteredCategories = filterCategories(categories);
              const hasResults = Object.values(filteredCategories).some((smells) => filterCodeSmells(smells as any[]).length > 0);
              
              if (!hasResults && (smellSearchTerm || smellSeverityFilter || smellCategoryFilter)) {
                return (
                  <div className="bg-slate-800 rounded-lg p-8 border border-slate-700 text-center">
                    <Search className="w-12 h-12 text-slate-400 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-white mb-2">No code smells found</h3>
                    <p className="text-slate-400 mb-4">Try adjusting your search criteria or filters</p>
                    <button
                      onClick={() => {
                        setSmellSearchTerm('');
                        setSmellSeverityFilter('');
                        setSmellCategoryFilter('');
                      }}
                      className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
                    >
                      Clear Filters
                    </button>
                  </div>
                );
              }
              
              return Object.entries(filteredCategories).map(([category, smells]) => {
                const filteredSmells = filterCodeSmells(smells as any[]);
                if (filteredSmells.length === 0) return null;
                const isExpanded = expandedCategories.has(category);
                const categoryInfo = getCategoryDisplayName(category);
              
              return (
                <div key={category} className="bg-slate-800 rounded-lg border border-slate-700">
                  <button
                    onClick={() => toggleCategoryExpansion(category)}
                    className="w-full p-4 flex items-center justify-between hover:bg-slate-700/30 transition-colors rounded-t-lg"
                  >
                    <div className="flex items-center space-x-3">
                      <Bug className="w-5 h-5 text-red-400" />
                      <div className="flex flex-col">
                        <h3 className="text-lg font-semibold text-white">{categoryInfo.display}</h3>
                        <span className="text-slate-400 text-sm">a.k.a {categoryInfo.technical}</span>
                      </div>
                      <span className="bg-red-500/20 text-red-400 px-2 py-1 rounded text-xs font-medium">
                        {filteredSmells.length}
                      </span>
                    </div>
                    {isExpanded ? <ChevronUp className="w-5 h-5 text-slate-400" /> : <ChevronDown className="w-5 h-5 text-slate-400" />}
                  </button>
                  
                  {isExpanded && (
                    <div className="p-6 pt-0 space-y-6">
                      {filteredSmells.map((smell: any) => (
                        <div key={smell.id} className="bg-gradient-to-r from-slate-700/60 to-slate-700/40 rounded-xl p-6 border border-slate-600/50 shadow-lg hover:shadow-xl transition-all duration-200 hover:border-slate-500/70">
                          {/* Header Section */}
                          <div className="flex items-start justify-between mb-4">
                            <div className="flex items-center space-x-3">
                              <span className={`px-3 py-1.5 rounded-full text-xs font-semibold border-2 flex items-center space-x-1.5 ${getSeverityColor(smell.severity)}`}>
                                {getSeverityIcon(smell.severity)}
                                <span>{smell.severity}</span>
                              </span>
                              <h4 className="text-base font-bold text-white leading-tight">{smell.name}</h4>
                            </div>
                            <span className="text-xs font-medium text-slate-300 bg-slate-600/70 px-3 py-1.5 rounded-full border border-slate-500/50">
                              Impact: {smell.impact}
                            </span>
                          </div>
                          
                          {/* Description Section */}
                          <div className="mb-5">
                            <p className="text-sm leading-relaxed text-slate-200 bg-slate-800/40 rounded-lg p-4 border-l-4 border-blue-500/50">
                              {smell.description}
                            </p>
                          </div>
                          
                          {/* Action Cards Section */}
                          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                            <div className="bg-gradient-to-br from-yellow-500/10 to-orange-500/5 rounded-xl p-4 border border-yellow-500/20 hover:border-yellow-500/40 transition-colors">
                              <div className="flex items-start space-x-3">
                                <div className="bg-yellow-500/20 p-2 rounded-lg">
                                  <Lightbulb className="w-5 h-5 text-yellow-400" />
                                </div>
                                <div className="flex-1">
                                  <p className="text-sm font-semibold text-yellow-400 mb-2">💡 How to Fix</p>
                                  <p className="text-sm text-slate-200 leading-relaxed mb-3">{smell.recommendation}</p>
                                  {(smell.startLine && smell.endLine && smell.startLine > 0 && smell.endLine > 0) ? (
                                    <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-600/50">
                                      <p className="text-xs text-slate-400 mb-2">📍 Location: Lines {smell.startLine}-{smell.endLine}</p>
                                      <button className="text-xs text-blue-400 hover:text-blue-300 underline">
                                        View Code →
                                      </button>
                                    </div>
                                  ) : (
                                    <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-600/50">
                                      <p className="text-xs text-slate-400 mb-2">📍 Location: Class-level issue</p>
                                      <button className="text-xs text-blue-400 hover:text-blue-300 underline">
                                        View Code →
                                      </button>
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>
                            
                            <div className="bg-gradient-to-br from-blue-500/10 to-cyan-500/5 rounded-xl p-4 border border-blue-500/20 hover:border-blue-500/40 transition-colors">
                              <div className="flex items-start space-x-3">
                                <div className="bg-blue-500/20 p-2 rounded-lg">
                                  <Info className="w-5 h-5 text-blue-400" />
                                </div>
                                <div className="flex-1">
                                  <p className="text-sm font-semibold text-blue-400 mb-2">ℹ️ Impact & Priority</p>
                                  <p className="text-sm text-slate-200 leading-relaxed mb-3">
                                    {smell.impact || 'This issue affects code maintainability and readability.'}
                                  </p>
                                  <div className="flex items-center space-x-2">
                                    <span className="text-xs text-slate-400">Priority:</span>
                                    <span className={`text-xs px-2 py-1 rounded ${
                                      smell.severity === 'CRITICAL' ? 'bg-red-500/20 text-red-400' :
                                      smell.severity === 'MAJOR' ? 'bg-orange-500/20 text-orange-400' :
                                      'bg-yellow-500/20 text-yellow-400'
                                    }`}>
                                      {smell.severity}
                                    </span>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>

                          {/* Step-by-Step Guidance */}
                          {smell.refactoringSuggestions && smell.refactoringSuggestions.length > 0 && (
                            <div className="mt-4 bg-gradient-to-br from-green-500/10 to-emerald-500/5 rounded-xl p-4 border border-green-500/20">
                              <div className="flex items-start space-x-3">
                                <div className="bg-green-500/20 p-2 rounded-lg">
                                  <Target className="w-5 h-5 text-green-400" />
                                </div>
                                <div className="flex-1">
                                  <p className="text-sm font-semibold text-green-400 mb-3">🎯 Step-by-Step Refactoring</p>
                                  <div className="space-y-2">
                                    {smell.refactoringSuggestions.map((step: string, index: number) => (
                                      <div key={index} className="flex items-start space-x-2">
                                        <span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded-full font-medium min-w-[20px] text-center">
                                          {index + 1}
                                        </span>
                                        <p className="text-sm text-slate-200 leading-relaxed">{step}</p>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
              });
            })()}

            {/* No Code Smells */}
            {fileAnalysis && (!fileAnalysis.codeSmells || fileAnalysis.codeSmells.length === 0) && (
              <div className="bg-slate-800 rounded-lg p-6 text-center">
                <CheckCircle className="w-16 h-16 text-green-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-white mb-2">No Code Smells Detected!</h3>
                <p className="text-slate-400">This file follows good coding practices and design principles.</p>
              </div>
            )}
          </div>
        )}
      </div>
    );
  }

  // Filter handler
  const handleFiltersChange = useCallback((filters: any) => {
    setActiveFilters(filters);
  }, []);

  // Calculate total issues for filter sidebar
  const totalIssues = assessment?.evidences?.length || 0;
  
  // Calculate filtered issues by applying the same filters to all evidences
  const filteredIssues = useMemo(() => {
    if (!assessment?.evidences) return 0;
    
    const filtered = assessment.evidences.filter((evidence: any) => {
      // Apply severity and smell type filters
      const matchesSmellType = activeFilters.smellTypes.length === 0 || 
        activeFilters.smellTypes.includes(evidence.detectorId);
      const matchesSeverity = activeFilters.severities.length === 0 || 
        activeFilters.severities.includes(evidence.severity);
      
      return matchesSmellType && matchesSeverity;
    });
    
    // Debug logging
    console.log('🔍 FILTER DEBUG:', {
      totalEvidences: assessment.evidences.length,
      activeFilters,
      filteredCount: filtered.length,
      sampleEvidences: assessment.evidences.slice(0, 3).map(e => ({
        detectorId: e.detectorId,
        severity: e.severity,
        file: e.pointer?.file
      }))
    });
    
    return filtered.length;
  }, [assessment?.evidences, activeFilters.smellTypes, activeFilters.severities]);

  // Create filtered assessment for charts
  const filteredAssessment = useMemo(() => {
    if (!assessment?.evidences) return assessment;
    
    const filteredEvidences = assessment.evidences.filter((evidence: any) => {
      // Apply severity and smell type filters
      const matchesSmellType = activeFilters.smellTypes.length === 0 || 
        activeFilters.smellTypes.includes(evidence.detectorId);
      const matchesSeverity = activeFilters.severities.length === 0 || 
        activeFilters.severities.includes(evidence.severity);
      
      return matchesSmellType && matchesSeverity;
    });
    
    return {
      ...assessment,
      evidences: filteredEvidences
    };
  }, [assessment, activeFilters.smellTypes, activeFilters.severities]);

  return (
    <div className="flex h-full bg-slate-900">
      {/* Left Sidebar - Compact */}
      <div className="w-64 bg-slate-800 border-r border-slate-700 flex flex-col">
        {/* Logo & Navigation */}
        <div className="p-4 border-b border-slate-700">
          <div className="flex items-center space-x-2 mb-4">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <Code className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">{BrandName}</h1>
              <p className="text-xs text-slate-400">Code Analysis</p>
            </div>
          </div>
          
          <nav className="space-y-1">
            {[
              { id: 'overview', label: 'Overview', icon: BarChart3 },
              { id: 'files', label: 'Files', icon: Folder, count: files.length },
              { id: 'analysis', label: 'Analysis', icon: Code },
              { id: 'security', label: 'Security', icon: Shield },
              { id: 'dependencies', label: 'Dependencies', icon: Network },
              { id: 'enhanced', label: 'Enhanced', icon: Zap },
              { id: 'refactoring', label: 'Refactoring', icon: Wrench },
              { id: 'llm-refactoring', label: 'AI Refactoring', icon: Brain },
        { id: 'controlled-refactoring', label: 'Controlled Refactoring', icon: Shield },
              { id: 'monitor', label: 'Monitor', icon: Activity },
              { id: 'projects', label: 'Project Hub', icon: Database }
            ].map(({ id, label, icon: Icon, count }) => (
              <button
                key={id}
                onClick={() => setActiveView(id as any)}
                className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-left transition-colors ${
                  activeView === id
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-300 hover:bg-slate-700'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Icon className="w-4 h-4" />
                  <span className="text-sm">{label}</span>
                </div>
                {count !== undefined && (
                  <span className="text-xs bg-slate-600 text-slate-200 px-2 py-0.5 rounded-full">
                    {count}
                  </span>
                )}
              </button>
            ))}
          </nav>
        </div>

        {/* Quick Stats */}
        <div className="p-4 border-b border-slate-700">
          <div className="bg-gradient-to-br from-slate-700 to-slate-800 rounded-xl p-4 border border-slate-600">
            <h3 className="text-sm font-semibold text-white mb-3 flex items-center">
              <BarChart3 className="w-4 h-4 mr-2 text-blue-400" />
              Project Overview
            </h3>
            
            {/* File Type Distribution Chart */}
            <div className="mb-4">
              <div className="h-32">
                <CodeSmellsPieChart 
                  critical={0}
                  major={0}
                  minor={0}
                />
              </div>
            </div>
            
            {/* Stats Grid */}
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="bg-slate-600/50 rounded-lg p-2">
                <div className="text-slate-300">Total Files</div>
                <div className="text-white font-bold text-lg">{fileStats.total}</div>
              </div>
              <div className="bg-slate-600/50 rounded-lg p-2">
                <div className="text-slate-300">Java Files</div>
                <div className="text-blue-400 font-bold text-lg">{fileStats.java}</div>
              </div>
              <div className="bg-slate-600/50 rounded-lg p-2">
                <div className="text-slate-300">Resources</div>
                <div className="text-yellow-400 font-bold text-lg">{fileStats.resources}</div>
              </div>
              <div className="bg-slate-600/50 rounded-lg p-2">
                <div className="text-slate-300">Tests</div>
                <div className="text-green-400 font-bold text-lg">{fileStats.tests}</div>
              </div>
            </div>
            
            {/* Quality Score */}
            {assessment && (
              <div className="mt-3 pt-3 border-t border-slate-600">
                <div className="flex items-center justify-between">
                  <span className="text-slate-300 text-xs">Quality Score</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-16 h-2 bg-slate-600 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gradient-to-r from-red-500 to-green-500 transition-all duration-300"
                        style={{ width: `${assessment.summary.maintainabilityIndex}%` }}
                      />
                    </div>
                    <span className="text-green-400 font-bold text-sm">
                      {assessment.summary.maintainabilityIndex}/100
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Analysis Summary */}
        {assessment && (
          <div className="p-4 flex-1 overflow-y-auto">
            <div className="bg-slate-700 rounded-lg p-3">
              <h3 className="text-sm font-semibold text-white mb-2">Issues Found</h3>
              <div className="space-y-1 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-300">Critical:</span>
                  <span className="text-red-400 font-semibold">
                    {assessment.summary.criticalFindings || 0}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-300">Major:</span>
                  <span className="text-orange-400 font-semibold">
                    {assessment.summary.majorFindings || 0}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-300">Minor:</span>
                  <span className="text-yellow-400 font-semibold">
                    {assessment.summary.minorFindings || 0}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex min-h-0">
        {/* Filter Sidebar */}
        {showFilterSidebar && (
          <FilterSidebar
            onFiltersChange={handleFiltersChange}
            totalIssues={totalIssues}
            filteredIssues={filteredIssues}
          />
        )}
        
        {/* Main Content */}
      <div className="flex-1 flex flex-col min-h-0">
        {/* File-Level Analysis Section - Show at top when file is selected */}
        {selectedFile && (
          <div className="bg-slate-800 border-b border-slate-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-white flex items-center">
                <FileText className="w-5 h-5 mr-2" />
                File-Level Analysis: {selectedFile.name}
              </h2>
              <div className="flex space-x-2">
                <button
                  onClick={() => {
                    setSelectedFile(null);
                    setFileAnalysis(null);
                    setActiveView('overview');
                  }}
                  className="px-4 py-2 bg-slate-600 hover:bg-slate-700 text-white rounded-lg transition-colors flex items-center"
                >
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back to Dashboard
                </button>
                <button
                  onClick={() => analyzeFile()}
                  disabled={isAnalyzing}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-lg transition-colors flex items-center"
                >
                  <RefreshCw className={`w-4 h-4 mr-2 ${isAnalyzing ? 'animate-spin' : ''}`} />
                  Re-analyze
                </button>
                <button
                  onClick={() => setActiveView('controlled-refactoring')}
                  className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors flex items-center"
                >
                  <Shield className="w-4 h-4 mr-2" />
                  Controlled Refactor
                </button>
                <button
                  onClick={() => {
                    console.log('🔍 Debug file analysis state:', {
                      fileAnalysis,
                      fileAnalysisRef: fileAnalysisRef.current,
                      currentAnalysis: fileAnalysis || fileAnalysisRef.current,
                      selectedFile,
                      isAnalyzing,
                      fileCodeSmells: (fileAnalysis || fileAnalysisRef.current)?.codeSmells || [],
                      fileMetrics: (fileAnalysis || fileAnalysisRef.current)?.metrics || {}
                    });
                  }}
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
                >
                  Debug
                </button>
              </div>
            </div>

            {/* File Analysis Content */}
            <div className="bg-slate-700 rounded-lg p-6">
              {(() => {
                // Always show file analysis results
                const currentAnalysis = fileAnalysis || fileAnalysisRef.current;
                console.log('🔍 Rendering file analysis section:', {
                  fileAnalysis,
                  fileAnalysisRef: fileAnalysisRef.current,
                  currentAnalysis,
                  selectedFile: selectedFile?.relativePath,
                  isAnalyzing,
                  hasFileAnalysis: !!currentAnalysis,
                  analysisKeys: currentAnalysis ? Object.keys(currentAnalysis) : []
                });
                
                // Show loading state
                if (isAnalyzing) {
                  return (
                    <div className="text-center py-8">
                      <RefreshCw className="w-12 h-12 text-blue-400 mx-auto mb-4 animate-spin" />
                      <h4 className="text-lg font-semibold text-white mb-2">Analyzing File...</h4>
                      <p className="text-slate-400">Please wait while we analyze this file.</p>
                    </div>
                  );
                }
                
                // Show prompt to analyze if no analysis yet
                if (!currentAnalysis) {
                  return (
                    <div className="text-center py-8">
                      <RefreshCw className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                      <h4 className="text-lg font-semibold text-white mb-2">Click Analyze to Start</h4>
                      <p className="text-slate-400">Click the "Analyze" button to analyze this file.</p>
                    </div>
                  );
                }
                
                // Show analysis results
                const fileMetrics = currentAnalysis?.metrics || {};
                const fileCodeSmells = (() => {
                  // Prefer Assessment evidences for consistent counts across the app
                  if (assessment?.evidences && selectedFile) {
                    const evidencesForFile = assessment.evidences.filter((e: any) => {
                      const filePath = e.pointer?.file;
                      if (!filePath) return false;
                      const norm = (p: string) => String(p).replace(/\\\\/g, '/').toLowerCase();
                      const ev = norm(filePath);
                      const rel = norm(selectedFile.relativePath);
                      const fileName = selectedFile.name.toLowerCase();
                      const exactMatch = ev === rel;
                      const endsWithMatch = ev.endsWith('/' + fileName) && ev.includes('src/');
                      const containsMatch = ev.includes('/' + fileName) && ev.includes('src/');
                      return exactMatch || endsWithMatch || containsMatch;
                    });
                    if (evidencesForFile.length > 0) {
                      return evidencesForFile.map((e: any) => ({
                        type: e.detectorId || e.summary || 'Code Smell',
                        severity: e.severity || 'MINOR',
                        description: e.summary || '',
                        location: e.pointer?.file,
                        startLine: e.pointer?.startLine,
                        endLine: e.pointer?.endLine,
                      }));
                    }
                  }
                  // Fallback to enhanced analysis results when no assessment data
                  return currentAnalysis?.codeSmells || [];
                })();
                
                // Debug logging
                console.log('🔍 File analysis display debug:', {
                  currentAnalysis: currentAnalysis,
                  fileCodeSmells: fileCodeSmells.length,
                  fileMetrics: fileMetrics,
                  selectedFile: selectedFile?.relativePath,
                  codeSmellsArray: currentAnalysis?.codeSmells,
                  codeSmellsLength: currentAnalysis?.codeSmells?.length,
                  hasCodeSmells: currentAnalysis?.codeSmells ? 'YES' : 'NO',
                  codeSmellsType: typeof currentAnalysis?.codeSmells,
                  currentAnalysisKeys: currentAnalysis ? Object.keys(currentAnalysis) : 'NO_ANALYSIS'
                });
                
                // Show analysis results - always display something
                return (
                  <div className="space-y-4">
                    {/* Analysis Status */}
                    <div className="text-center py-4">
                      {fileCodeSmells.length === 0 ? (
                        <>
                          <CheckCircle className="w-12 h-12 text-green-400 mx-auto mb-4" />
                          <h4 className="text-lg font-semibold text-white mb-2">File Analysis Complete</h4>
                          <p className="text-slate-400 mb-4">This file appears to be clean with no code quality issues detected.</p>
                        </>
                      ) : (
                        <>
                          <AlertTriangle className="w-12 h-12 text-orange-400 mx-auto mb-4" />
                          <h4 className="text-lg font-semibold text-white mb-2">File Analysis Complete</h4>
                          <p className="text-slate-400 mb-4">Found {fileCodeSmells.length} code quality issues in this file.</p>
                        </>
                      )}
                    </div>

                    {/* Analysis Results */}
                    <div className="bg-slate-600 rounded-lg p-4">
                      <h5 className="text-white font-semibold mb-3">Analysis Results:</h5>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <span className="text-slate-400">File:</span>
                          <p className="text-white font-mono text-xs">{selectedFile.relativePath}</p>
                        </div>
                        <div>
                          <span className="text-slate-400">Analysis Status:</span>
                          <p className="text-green-400">✅ Completed</p>
                        </div>
                        <div>
                          <span className="text-slate-400">Code Smells:</span>
                          <p className="text-white">{fileCodeSmells.length}</p>
                        </div>
                        <div>
                          <span className="text-slate-400">Total Lines:</span>
                          <p className="text-white">{currentAnalysis?.linesOfCode || fileMetrics.totalLines || 0}</p>
                        </div>
                        <div>
                          <span className="text-slate-400">Complexity:</span>
                          <p className="text-white">{currentAnalysis?.complexity || fileMetrics.cyclomaticComplexity || 0}</p>
                        </div>
                        <div>
                          <span className="text-slate-400">Maintainability:</span>
                          <p className="text-white">{currentAnalysis?.maintainability || fileMetrics.maintainabilityIndex || 0}</p>
                        </div>
                        <div>
                          <span className="text-slate-400">Quality Grade:</span>
                          <p className="text-white">{fileMetrics.qualityGrade || 'N/A'}</p>
                        </div>
                      </div>
                    </div>

                    {/* Quality Assessment */}
                    {(currentAnalysis as any)?.qualityInsights && (
                      <div className="bg-slate-600 rounded-lg p-4">
                        <h5 className="text-white font-semibold mb-3">Quality Assessment</h5>
                        <div className="text-sm text-slate-300 space-y-2">
                          <p><strong>Overall Quality:</strong> {(currentAnalysis as any).qualityInsights.qualityCategory}</p>
                          {(currentAnalysis as any).qualityInsights.specificInsights && (
                            <div className="space-y-1">
                              {Object.entries((currentAnalysis as any).qualityInsights.specificInsights).map(([key, value]: [string, any]) => (
                                <p key={key}><strong>{key.charAt(0).toUpperCase() + key.slice(1)}:</strong> {value}</p>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                       {/* Code Smells Details */}
                       {fileCodeSmells.length > 0 && (
                         <div className="bg-slate-600 rounded-lg p-4">
                           <h5 className="text-white font-semibold mb-3">Code Smells Found:</h5>
                           <div className="space-y-3">
                             {fileCodeSmells.slice(0, 5).map((smell: any, index: number) => (
                               <div key={index} className="bg-slate-700 rounded p-3">
                                 <div className="flex items-center justify-between mb-2">
                                   <span className="font-medium text-white">{smell.type || 'Code Smell'}</span>
                                   <span className={`px-2 py-1 rounded text-xs font-medium ${
                                     smell.severity === 'CRITICAL' ? 'bg-red-500/80 text-white' :
                                     smell.severity === 'MAJOR' ? 'bg-orange-500/80 text-white' :
                                     smell.severity === 'MINOR' ? 'bg-yellow-500/80 text-white' :
                                     'bg-slate-500/80 text-white'
                                   }`}>
                                     {smell.severity || 'UNKNOWN'}
                                   </span>
                                 </div>
                                 <p className="text-slate-300 text-sm mb-2">{smell.description || 'No description available'}</p>
                                 {smell.recommendation && (
                                   <p className="text-blue-300 text-sm"><strong>Recommendation:</strong> {smell.recommendation}</p>
                                 )}
                               </div>
                             ))}
                             {fileCodeSmells.length > 5 && (
                               <p className="text-slate-400 text-sm">... and {fileCodeSmells.length - 5} more issues</p>
                             )}
                           </div>
                         </div>
                       )}

                       {/* AI Refactoring Quick Actions */}
                       {fileCodeSmells.length > 0 && (
                         <div className="bg-gradient-to-r from-green-600/20 to-blue-600/20 rounded-lg p-4 border border-green-500/30">
                           <h5 className="text-white font-semibold mb-3 flex items-center">
                             <Brain className="w-5 h-5 mr-2 text-green-400" />
                             AI-Powered Refactoring
                           </h5>
                           <p className="text-slate-300 text-sm mb-4">
                             Found {fileCodeSmells.length} code smells. Let AI help you refactor this file automatically.
                           </p>
                           <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                             <button
                               onClick={() => setActiveView('controlled-refactoring')}
                               className="bg-green-600 hover:bg-green-700 text-white rounded-lg p-3 text-sm transition-colors flex items-center justify-center"
                             >
                               <Wand2 className="w-4 h-4 mr-2" />
                               Fix Code Smells
                             </button>
                             <button
                               onClick={() => setActiveView('controlled-refactoring')}
                               className="bg-blue-600 hover:bg-blue-700 text-white rounded-lg p-3 text-sm transition-colors flex items-center justify-center"
                             >
                               <Code className="w-4 h-4 mr-2" />
                               Extract Methods
                             </button>
                             <button
                               onClick={() => setActiveView('controlled-refactoring')}
                               className="bg-purple-600 hover:bg-purple-700 text-white rounded-lg p-3 text-sm transition-colors flex items-center justify-center"
                             >
                               <Zap className="w-4 h-4 mr-2" />
                               Optimize Performance
                             </button>
                             <button
                               onClick={() => setActiveView('controlled-refactoring')}
                               className="bg-orange-600 hover:bg-orange-700 text-white rounded-lg p-3 text-sm transition-colors flex items-center justify-center"
                             >
                               <Eye className="w-4 h-4 mr-2" />
                               Improve Readability
                             </button>
                           </div>
                         </div>
                       )}
                  </div>
                );
              })()}
            </div>
            
            {/* Close Analysis Button */}
            <div className="mt-4 flex justify-center">
              <button
                onClick={() => {
                  setSelectedFile(null);
                  setFileAnalysis(null);
                  setActiveView('overview');
                }}
                className="px-6 py-3 bg-slate-600 hover:bg-slate-700 text-white rounded-lg transition-colors flex items-center space-x-2"
              >
                <X className="w-4 h-4" />
                <span>Close Analysis</span>
              </button>
            </div>
          </div>
        )}

        {/* Top Header */}
        <div className="bg-slate-800 border-b border-slate-700 p-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-white capitalize">
                {activeView} Dashboard
              </h2>
              <p className="text-sm text-slate-400">
                Workspace: {workspaceId}
              </p>
            </div>
            <div className="flex items-center space-x-3">
              {/* Filter Toggle */}
              <button
                onClick={() => setShowFilterSidebar(!showFilterSidebar)}
                className={`px-3 py-2 rounded-lg text-sm transition-colors flex items-center space-x-2 ${
                  showFilterSidebar 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-slate-700 text-slate-300 hover:text-white hover:bg-slate-600'
                }`}
              >
                <FilterIcon className="w-4 h-4" />
                <span>Filters</span>
                {activeFilters.severities.length > 0 || activeFilters.smellTypes.length > 0 || 
                 activeFilters.fileTypes.length > 0 || activeFilters.searchTerm.length > 0 ? (
                  <span className="bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                    {(activeFilters.severities.length + activeFilters.smellTypes.length + 
                      activeFilters.fileTypes.length + (activeFilters.searchTerm ? 1 : 0))}
                  </span>
                ) : null}
              </button>
              
              {/* View Toggle */}
              <div className="flex bg-slate-700 rounded-lg p-1">
                <button
                  onClick={() => setCurrentView('files')}
                  className={`px-3 py-1 rounded text-sm transition-colors ${
                    currentView === 'files' 
                      ? 'bg-blue-600 text-white' 
                      : 'text-slate-300 hover:text-white'
                  }`}
                >
                  <FileText className="w-4 h-4 mr-1 inline" />
                  Files
                </button>
                <button
                  onClick={() => setCurrentView('dashboard')}
                  className={`px-3 py-1 rounded text-sm transition-colors ${
                    currentView === 'dashboard' 
                      ? 'bg-blue-600 text-white' 
                      : 'text-slate-300 hover:text-white'
                  }`}
                >
                  <BarChart3 className="w-4 h-4 mr-1 inline" />
                  Dashboard
                </button>
              </div>
              
              <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm transition-colors">
                <Play className="w-4 h-4 mr-2 inline" />
                Run Analysis
              </button>
              <button 
                onClick={exportToCSV}
                disabled={isExporting}
                className="bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white px-4 py-2 rounded-lg text-sm transition-colors flex items-center"
              >
                {isExporting ? (
                  <RefreshCw className="w-4 h-4 mr-2 inline animate-spin" />
                ) : (
                <Download className="w-4 h-4 mr-2 inline" />
                )}
                {isExporting ? 'Exporting...' : 'Export CSV'}
              </button>
            </div>
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-hidden">
          {currentView === 'dashboard' ? (
            <CodeSmellsDashboard 
              assessment={filteredAssessment}
              files={files}
              workspaceId={workspaceId}
            />
          ) : (
            <>
          {activeView === 'overview' && (
            <div className="h-full overflow-y-auto p-6">
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
                {/* Project Overview Card */}
                <div className="lg:col-span-2 bg-slate-800 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-white mb-4">Project Overview</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-slate-700 rounded-lg p-4 text-center">
                      <div className="text-2xl font-bold text-blue-400">{fileStats.total}</div>
                      <div className="text-sm text-slate-300">Total Files</div>
                    </div>
                    <div className="bg-slate-700 rounded-lg p-4 text-center">
                      <div className="text-2xl font-bold text-green-400">{fileStats.java}</div>
                      <div className="text-sm text-slate-300">Java Files</div>
                    </div>
                    <div className="bg-slate-700 rounded-lg p-4 text-center">
                      <div className="text-2xl font-bold text-yellow-400">{fileStats.resources}</div>
                      <div className="text-sm text-slate-300">Resources</div>
                    </div>
                    <div className="bg-slate-700 rounded-lg p-4 text-center">
                      <div className="text-2xl font-bold text-purple-400">{fileStats.tests}</div>
                      <div className="text-sm text-slate-300">Tests</div>
                    </div>
                  </div>
                </div>

                {/* Quality Score Card */}
                <div className="bg-slate-800 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-white mb-4">Quality Score</h3>
                  <div className="flex justify-center">
                    <QualityGauge 
                      score={assessment?.summary.maintainabilityIndex || 0}
                      maxScore={100}
                      label="Overall Quality"
                    />
                  </div>
                </div>
              </div>

              {/* Enhanced Charts Section */}
              <div className="space-y-6">
                {/* Row 1: Project Overview Charts */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
                    <div className="flex items-center mb-4">
                      <AlertTriangle className="w-5 h-5 text-red-400 mr-2" />
                      <h3 className="text-lg font-semibold text-white">Project Code Smells by Severity</h3>
                    </div>
                    <div className="h-64">
                       <CodeSmellsPieChart 
                         critical={assessment?.summary.criticalFindings || 0}
                         major={assessment?.summary.majorFindings || 0}
                         minor={assessment?.summary.minorFindings || 0}
                       />
                    </div>
                  </div>
                  
                  <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
                    <div className="flex items-center mb-4">
                      <Bug className="w-5 h-5 text-orange-400 mr-2" />
                      <h3 className="text-lg font-semibold text-white">Project Code Smells by Category</h3>
                    </div>
                    <div className="h-64">
                      {assessment ? (
                        <div className="space-y-3">
                          <div className="flex items-center justify-between">
                            <span className="text-slate-300 text-sm">Total Issues</span>
                            <div className="flex items-center space-x-2">
                              <div className="w-20 bg-slate-700 rounded-full h-2">
                                <div 
                                  className="bg-gradient-to-r from-orange-400 to-red-500 h-2 rounded-full"
                                  style={{ width: `${Math.min(100, (assessment.summary.totalFindings / Math.max(1, assessment.summary.totalFiles)) * 100)}%` }}
                                />
                              </div>
                              <span className="text-white font-semibold text-sm w-8 text-right">{assessment.summary.totalFindings}</span>
                            </div>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-slate-300 text-sm">Files Analyzed</span>
                            <span className="text-white font-semibold text-sm">{assessment.summary.totalFiles}</span>
                          </div>
                        </div>
                      ) : (
                        <div className="flex items-center justify-center h-full text-slate-400">
                          <div className="text-center">
                            <Bug className="w-12 h-12 mx-auto mb-2 opacity-50" />
                            <p>No category data available</p>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Row 2: File Metrics and Quality */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
                    <div className="flex items-center mb-4">
                      <PieChart className="w-5 h-5 text-blue-400 mr-2" />
                      <h3 className="text-lg font-semibold text-white">File Type Distribution</h3>
                    </div>
                    <div className="h-64">
                      <MetricsBarChart 
                        classes={fileStats.java}
                        methods={fileStats.tests}
                        comments={fileStats.resources}
                        lines={fileStats.total}
                      />
                    </div>
                  </div>
                  
                  <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
                    <div className="flex items-center mb-4">
                      <BarChart3 className="w-5 h-5 text-green-400 mr-2" />
                      <h3 className="text-lg font-semibold text-white">Project Quality Metrics</h3>
                    </div>
                    <div className="h-64">
                      {assessment ? (
                        <div className="space-y-4">
                          <div className="flex items-center justify-between">
                            <span className="text-slate-300">Overall Score</span>
                            <div className="flex items-center space-x-2">
                              <div className="w-24 bg-slate-700 rounded-full h-3">
                                <div 
                                  className={`h-3 rounded-full transition-all duration-300 ${
                                    assessment.summary.maintainabilityIndex >= 80 ? 'bg-green-500' :
                                    assessment.summary.maintainabilityIndex >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                                  }`}
                                  style={{ width: `${assessment.summary.maintainabilityIndex}%` }}
                                />
                              </div>
                              <span className="text-white font-semibold">{assessment.summary.maintainabilityIndex}/100</span>
                            </div>
                          </div>
                          
                          <div className="flex items-center justify-between">
                            <span className="text-slate-300">Total Issues</span>
                            <div className="flex items-center space-x-2">
                              <div className="w-24 bg-slate-700 rounded-full h-3">
                                <div 
                                  className={`h-3 rounded-full ${
                                    ((assessment.summary.criticalFindings || 0) + (assessment.summary.majorFindings || 0) + (assessment.summary.minorFindings || 0)) === 0 ? 'bg-green-500' :
                                    ((assessment.summary.criticalFindings || 0) + (assessment.summary.majorFindings || 0) + (assessment.summary.minorFindings || 0)) <= 10 ? 'bg-yellow-500' : 'bg-red-500'
                                  }`}
                                  style={{ width: `${Math.min(100, ((assessment.summary.criticalFindings || 0) + (assessment.summary.majorFindings || 0) + (assessment.summary.minorFindings || 0)) * 5)}%` }}
                                />
                              </div>
                              <span className="text-white font-semibold">
                                {(assessment.summary.criticalFindings || 0) + (assessment.summary.majorFindings || 0) + (assessment.summary.minorFindings || 0)}
                              </span>
                            </div>
                          </div>
                          
                          <div className="flex items-center justify-between">
                            <span className="text-slate-300">Files Analyzed</span>
                            <div className="flex items-center space-x-2">
                              <div className="w-24 bg-slate-700 rounded-full h-3">
                                <div 
                                  className="bg-blue-500 h-3 rounded-full"
                                  style={{ width: `${Math.min(100, (fileStats.total / 1000) * 100)}%` }}
                                />
                              </div>
                              <span className="text-white font-semibold">{fileStats.total}</span>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="flex items-center justify-center h-full text-slate-400">
                          <div className="text-center">
                            <BarChart3 className="w-12 h-12 mx-auto mb-2 opacity-50" />
                            <p>No quality metrics available</p>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Row 3: Project Summary */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* Project Statistics */}
                  <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
                    <div className="flex items-center mb-4">
                      <FileText className="w-5 h-5 text-blue-400 mr-2" />
                      <h3 className="text-lg font-semibold text-white">Project Statistics</h3>
                    </div>
                    <div className="space-y-3">
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-300">Total Files</span>
                        <span className="text-white font-semibold">{fileStats.total}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-300">Java Files</span>
                        <span className="text-white font-semibold">{fileStats.java}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-300">Test Files</span>
                        <span className="text-white font-semibold">{fileStats.tests}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-300">Resource Files</span>
                        <span className="text-white font-semibold">{fileStats.resources}</span>
                      </div>
                    </div>
                  </div>

                  {/* Refactoring Suggestions */}
                  <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
                    <div className="flex items-center mb-4">
                      <Lightbulb className="w-5 h-5 text-yellow-400 mr-2" />
                      <h3 className="text-lg font-semibold text-white">Refactoring Suggestions</h3>
                    </div>
                    <div className="space-y-3">
                      {plan?.transforms?.slice(0, 5).map((transform: any, index: number) => (
                        <div key={index} className="p-3 bg-slate-700/50 rounded-lg">
                          <p className="text-white text-sm font-medium mb-1">{transform.name}</p>
                          <p className="text-slate-400 text-xs">{transform.description || 'No description available'}</p>
                        </div>
                      )) || (
                        <div className="text-center text-slate-400 py-8">
                          <Lightbulb className="w-8 h-8 mx-auto mb-2 opacity-50" />
                          <p className="text-sm">No suggestions available</p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Project Health */}
                  <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
                    <div className="flex items-center mb-4">
                      <Activity className="w-5 h-5 text-green-400 mr-2" />
                      <h3 className="text-lg font-semibold text-white">Project Health</h3>
                    </div>
                    <div className="space-y-6">
                      <div className="text-center">
                        <div className="w-24 h-24 mx-auto mb-4">
                          <QualityGauge 
                            score={assessment?.summary.maintainabilityIndex || 0}
                            maxScore={100}
                            label="Quality"
                          />
                        </div>
                        <div className="space-y-1">
                          <p className="text-slate-300 text-sm font-medium">
                            {(assessment?.summary.maintainabilityIndex || 0) >= 80 ? 'Excellent' :
                             (assessment?.summary.maintainabilityIndex || 0) >= 60 ? 'Good' :
                             (assessment?.summary.maintainabilityIndex || 0) >= 40 ? 'Fair' : 'Needs Improvement'}
                          </p>
                          <p className="text-slate-400 text-xs">
                            Score: {Math.round(assessment?.summary.maintainabilityIndex || 0)}/100
                          </p>
                        </div>
                      </div>
                      
                      <div className="space-y-3 text-sm">
                        <div className="flex justify-between items-center py-2 border-b border-slate-700/50">
                          <span className="text-slate-300">Files Analyzed</span>
                          <span className="text-white font-semibold">{fileStats.total}</span>
                        </div>
                        <div className="flex justify-between items-center py-2 border-b border-slate-700/50">
                          <span className="text-slate-300">Issues Found</span>
                          <span className="text-white font-semibold">
                            {(assessment?.summary.criticalFindings || 0) + 
                             (assessment?.summary.majorFindings || 0) + 
                             (assessment?.summary.minorFindings || 0)}
                          </span>
                        </div>
                        <div className="flex justify-between items-center py-2">
                          <span className="text-slate-300">Last Updated</span>
                          <span className="text-white font-semibold">{new Date().toLocaleDateString()}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeView === 'files' && (
            <div className="h-full flex flex-col">
              {/* Files Header */}
              <div className="bg-slate-800 border-b border-slate-700 p-4">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-white">File Browser</h3>
                    <p className="text-sm text-slate-400 mt-1">
                      {filteredFiles.length} files {showOnlyCodeSmellsFiles ? 'with code smells' : 'available'}
                      {filteredAssessment?.evidences && (
                        <span className="ml-2 text-green-400">
                          ({filteredAssessment.evidences.length} total code smells, {new Set(filteredAssessment.evidences.map((e: any) => e.filePath)).size} unique files with smells)
                        </span>
                      )}
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setFileViewMode('list')}
                      className={`p-2 rounded ${fileViewMode === 'list' ? 'bg-blue-600 text-white' : 'bg-slate-700 text-slate-300'}`}
                    >
                      <List className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => setFileViewMode('grid')}
                      className={`p-2 rounded ${fileViewMode === 'grid' ? 'bg-blue-600 text-white' : 'bg-slate-700 text-slate-300'}`}
                    >
                      <Grid className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Search and Filters */}
                <div className="flex items-center space-x-4">
                  <div className="flex-1 relative">
                    <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" />
                    <input
                      type="text"
                      placeholder="Search files..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="w-full bg-slate-700 text-white pl-10 pr-4 py-2 rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none"
                    />
                  </div>
                  <select
                    value={fileTypeFilter}
                    onChange={(e) => setFileTypeFilter(e.target.value)}
                    className="bg-slate-700 text-white px-3 py-2 rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none"
                  >
                    <option value="">All Types</option>
                    <option value="java">Java Files</option>
                    <option value="resources">Resources</option>
                    <option value="tests">Tests</option>
                    <option value="config">Config</option>
                  </select>
                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value as 'name' | 'size' | 'type')}
                    className="bg-slate-700 text-white px-3 py-2 rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none"
                  >
                    <option value="size">Sort by Size</option>
                    <option value="name">Sort by Name</option>
                    <option value="type">Sort by Type</option>
                  </select>
                  
                  {/* Show only files with code smells checkbox */}
                  <div className="flex items-center space-x-2 bg-green-500/10 border border-green-500/30 rounded-lg px-3 py-2">
                    <input
                      type="checkbox"
                      id="showCodeSmellsOnly"
                      checked={showOnlyCodeSmellsFiles}
                      onChange={(e) => setShowOnlyCodeSmellsFiles(e.target.checked)}
                      className="w-4 h-4 text-green-600 bg-slate-700 border-slate-600 rounded focus:ring-green-500 focus:ring-2"
                    />
                    <label htmlFor="showCodeSmellsOnly" className="text-sm font-medium text-green-400 cursor-pointer flex items-center space-x-1">
                      <span>⚠️</span>
                      <span>Show only files with code smells</span>
                    </label>
                  </div>
                  
                  
                  <button
                    onClick={() => {
                      // Force refresh by toggling the filter state
                      setShowOnlyCodeSmellsFiles(!showOnlyCodeSmellsFiles);
                      setTimeout(() => {
                        setShowOnlyCodeSmellsFiles(!showOnlyCodeSmellsFiles);
                      }, 100);
                    }}
                    className="px-3 py-2 bg-green-600 hover:bg-green-700 text-white text-xs rounded transition-colors"
                  >
                    Force Refresh
                  </button>
                  <select
                    value={pageSize}
                    onChange={(e) => setPageSize(Number(e.target.value))}
                    className="bg-slate-700 text-white px-3 py-2 rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none"
                  >
                    <option value={10}>10 per page</option>
                    <option value={20}>20 per page</option>
                    <option value={50}>50 per page</option>
                    <option value={100}>100 per page</option>
                  </select>
                </div>
              </div>

              {/* Files List */}
              <div className="flex-1 overflow-y-auto p-4">
                {fileViewMode === 'list' ? (
                  <div className="space-y-2">
                    {paginatedFiles.map((file, index) => {
                      const isExpanded = expandedFiles.has(file.relativePath);
                      const badge = getFileTypeBadge(file);
                      
                      // Gather evidences that belong to this file (real data)
                      const evidencesForFile: any[] = (assessment?.evidences || []).filter((e: any) => {
                        // The file path is in e.pointer.file (CodePointer structure)
                        const filePath = e.pointer?.file;
                        if (!filePath) return false;
                        
                        const norm = (p: string) => String(p).replace(/\\\\/g, '/').toLowerCase();
                        const ev = norm(filePath);
                        const rel = norm(file.relativePath);
                        const fileName = file.name.toLowerCase();
                        
                        // More precise matching - require exact path match or very specific patterns
                        const exactMatch = ev === rel;
                        const endsWithMatch = ev.endsWith('/' + fileName) && ev.includes('src/');
                        const containsMatch = ev.includes('/' + fileName) && ev.includes('src/');
                        
                        const matchesFile = exactMatch || endsWithMatch || containsMatch;
                        
                        if (!matchesFile) return false;
                        
                        // Apply active filters from the sidebar
                        const matchesSmellType = activeFilters.smellTypes.length === 0 || 
                          activeFilters.smellTypes.includes(e.detectorId);
                        const matchesSeverity = activeFilters.severities.length === 0 || 
                          activeFilters.severities.includes(e.severity);
                        
                        return matchesSmellType && matchesSeverity;
                      });

                      const finalHasCodeSmells = evidencesForFile.length > 0;
                      const codeSmellsCount = evidencesForFile.length;
                      // Count smells by type for this file
                      const smellTypeCounts = evidencesForFile.reduce((acc: any, e: any) => {
                        const type = e.detectorId || e.summary || 'Unknown';
                        acc[type] = (acc[type] || 0) + 1;
                        return acc;
                      }, {});
                      
                      // Debug logging for first few files
                      if (index < 3) {
                        console.log(`File ${file.name} - Total evidences: ${evidencesForFile.length}`);
                        console.log(`File ${file.name} - Type counts:`, smellTypeCounts);
                        console.log(`File ${file.name} - Evidence samples:`, evidencesForFile.slice(0, 3));
                        console.log(`File ${file.name} - Math check:`, Object.values(smellTypeCounts).reduce((a: number, b: any) => a + (typeof b === 'number' ? b : 0), 0), 'should equal', evidencesForFile.length);
                      }
                      
                      // Create smell types with counts, limited to 3 types
                      const smellTypes = Object.entries(smellTypeCounts)
                        .map(([type, count]) => `${type} (${count})`)
                        .slice(0, 3);
                      
                      
                      return (
                        <div key={index} className="bg-slate-800 rounded-lg border border-slate-700">
                          <div className="p-4">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center space-x-3 flex-1 min-w-0">
                                <button
                                  onClick={() => toggleFileExpansion(file.relativePath)}
                                  className="text-slate-400 hover:text-white"
                                >
                                  {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                                </button>
                                {getFileTypeIcon(file)}
                                <div className="flex-1 min-w-0">
                                  <p className="text-sm font-medium text-white truncate">{file.name}</p>
                                  <p className="text-xs text-slate-400 truncate">{file.relativePath}</p>
                                </div>
                                <span className={`px-2 py-1 rounded text-xs font-medium ${badge.color}`}>
                                  {badge.text}
                                </span>
                                {finalHasCodeSmells && (
                                  <span className="px-2 py-1 rounded text-xs font-medium bg-orange-500/20 text-orange-400 border border-orange-500/30">
                                    ⚠️ {codeSmellsCount} smells
                                  </span>
                                )}
                              </div>
                              <div className="flex items-center space-x-2">
                                {/* View Button */}
                                <button 
                                  onClick={() => loadFileContent(file)}
                                  className="bg-slate-700 hover:bg-slate-600 text-white px-3 py-1 rounded text-xs transition-colors"
                                >
                                  View
                                </button>
                                
                                {/* Analyze Button */}
                                <button
                                  onClick={() => {
                                    console.log('🔍 Manual analyze button clicked for:', file.relativePath);
                                    setSelectedFile(file);
                                    setActiveView('analysis');
                                    // Force analysis even if one exists
                                    setFileAnalysis(null);
                                    setTimeout(() => analyzeFile(), 100);
                                  }}
                                  disabled={isAnalyzing}
                                  className={`px-3 py-1 rounded text-xs transition-colors ${
                                    isAnalyzing 
                                      ? 'bg-gray-600 text-gray-400 cursor-not-allowed' 
                                      : 'bg-blue-600 hover:bg-blue-700 text-white'
                                  }`}
                                >
                                  {isAnalyzing ? (
                                    <>
                                      <RefreshCw className="w-3 h-3 mr-1 animate-spin inline" />
                                      Analyzing...
                                    </>
                                  ) : (
                                    'Analyze'
                                  )}
                                </button>
                                
                                {/* Refactoring Button - Enhanced AI Refactoring */}
                                <button
                                  onClick={async () => {
                                    console.log('🚀 Enhanced AI Refactoring triggered for:', file.relativePath);
                                    setSelectedFile(file);
                                    setLoadingFileContent(true);
                                    try {
                                      // Load file content
                                      const content = await apiClient.getFileContent(workspaceId, file.relativePath);
                                      setFileContent(typeof content === 'string' ? content : content.content || '');
                                      
                                      // Load code smells for this file
                                      try {
                                        const analysisResponse = await apiClient.analyzeFileEnhanced(workspaceId, file.relativePath);
                                        console.log('✅ Enhanced analysis loaded:', analysisResponse);
                                        setFileCodeSmells(analysisResponse.codeSmells || []);
                                      } catch (analysisError) {
                                        console.warn('⚠️ Enhanced analysis failed, using assessment data:', analysisError);
                                        // Fallback to assessment data
                                        const fileCodeSmells = assessment?.evidences?.filter((evidence: any) => 
                                          evidence.pointer?.file?.includes(file.relativePath)
                                        ) || [];
                                        setFileCodeSmells(fileCodeSmells);
                                      }
                                      
                                      setActiveView('enhanced-refactoring');
                                    } catch (error) {
                                      console.error('Failed to load file content:', error);
                                      setFileContent('// Failed to load file content');
                                      setFileCodeSmells([]);
                                      setActiveView('enhanced-refactoring');
                                    } finally {
                                      setLoadingFileContent(false);
                                    }
                                  }}
                                  className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white px-3 py-1 rounded text-xs transition-colors font-medium shadow-lg hover:shadow-xl transform hover:scale-105"
                                >
                                  🧠 AI Refactoring
                                </button>
                              </div>
                            </div>

                            {isExpanded && (
                              <div className="mt-4 pt-4 border-t border-slate-700">
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs mb-3">
                                  <div>
                                    <span className="text-slate-400">Lines:</span>
                                    <span className="text-white ml-2">{file.metrics.linesOfCode}</span>
                                  </div>
                                  <div>
                                    <span className="text-slate-400">Classes:</span>
                                    <span className="text-white ml-2">{file.metrics.classCount}</span>
                                  </div>
                                  <div>
                                    <span className="text-slate-400">Methods:</span>
                                    <span className="text-white ml-2">{file.metrics.methodCount}</span>
                                  </div>
                                  <div>
                                    <span className="text-slate-400">Complexity:</span>
                                    <span className="text-white ml-2">{file.metrics.cyclomaticComplexity}</span>
                                  </div>
                                </div>
                                
                                {/* Code Smells Section */}
                                {finalHasCodeSmells && (
                                  <div className="bg-slate-700/30 rounded-lg p-3 border border-slate-600/50">
                                    <div className="flex items-center justify-between mb-2">
                                      <span className="text-slate-300 text-xs font-medium">Code Smells:</span>
                                      <span className="text-orange-400 text-xs font-semibold">{codeSmellsCount} detected</span>
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                      {smellTypes.map((type, i) => (
                                        <span key={i} className="px-2 py-1 bg-slate-600/50 text-slate-200 text-[10px] rounded border border-slate-500/30">
                                          {type}
                                        </span>
                                      ))}
                                </div>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    {paginatedFiles.map((file, index) => {
                      const badge = getFileTypeBadge(file);
                      
                      // REAL CODE SMELLS CHECK: Use actual assessment data only (no fallback)
                      const hasRealCodeSmells = assessment?.evidences?.some((evidence: any) => {
                        const filePath = evidence.filePath || evidence.fileName || evidence.path || evidence.file || evidence.location || evidence.sourceFile || evidence.targetFile;
                        
                        // Try exact matches first
                        if (filePath === file.relativePath || filePath === file.name) {
                          return true;
                        }
                        
                        // Try partial matches
                        if (filePath && typeof filePath === 'string') {
                          return filePath.includes(file.name) || file.relativePath.includes(filePath);
                        }
                        
                        return false;
                      }) || false;
                      
                      const finalHasCodeSmells = hasRealCodeSmells;
                      
                      const codeSmellsCount = (() => {
                        if (hasRealCodeSmells) {
                          // Count real code smells for this file
                          const realCount = assessment?.evidences?.filter((evidence: any) => {
                            const filePath = evidence.filePath || evidence.fileName || evidence.path || evidence.file || evidence.location || evidence.sourceFile || evidence.targetFile;
                            return filePath === file.relativePath || filePath === file.name || filePath?.includes(file.name);
                          }).length || 0;
                          
                          if (realCount > 0) {
                            console.log(`✅ Real code smells count for ${file.name}: ${realCount}`);
                            return realCount;
                          }
                        }
                        console.log(`❌ No code smells for ${file.name}`);
                        return 0;
                      })();
                      
                      return (
                        <div key={index} className="bg-slate-800 rounded-lg border border-slate-700 p-4 hover:border-slate-600 transition-colors">
                          <div className="flex items-center space-x-2 mb-3">
                            {getFileTypeIcon(file)}
                            <span className={`px-2 py-1 rounded text-xs font-medium ${badge.color}`}>
                              {badge.text}
                            </span>
                            {finalHasCodeSmells && (
                              <span className="px-2 py-1 rounded text-xs font-medium bg-orange-500/20 text-orange-400 border border-orange-500/30">
                                ⚠️ {codeSmellsCount}
                              </span>
                            )}
                          </div>
                          <h4 className="text-sm font-medium text-white mb-1 truncate">{file.name}</h4>
                          <p className="text-xs text-slate-400 mb-3 truncate">{file.relativePath}</p>
                          <div className="flex items-center justify-between">
                            <div className="text-xs text-slate-300">
                              {file.metrics.linesOfCode} lines
                            </div>
                            <button
                              onClick={() => {
                                console.log('🔍 File list analyze button clicked for:', file.relativePath);
                                setSelectedFile(file);
                                setActiveView('analysis');
                                setFileAnalysis(null);
                                setTimeout(() => analyzeFile(), 100);
                              }}
                              className="bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded text-xs transition-colors"
                            >
                              Analyze
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="flex items-center justify-between mt-6">
                    <div className="text-sm text-slate-400">
                      Showing {currentPage * pageSize + 1} to {Math.min((currentPage + 1) * pageSize, filteredFiles.length)} of {filteredFiles.length} files
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => setCurrentPage(0)}
                        disabled={currentPage === 0}
                        className="p-2 text-slate-400 hover:text-white disabled:opacity-50"
                      >
                        <ChevronFirst className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => setCurrentPage(currentPage - 1)}
                        disabled={currentPage === 0}
                        className="p-2 text-slate-400 hover:text-white disabled:opacity-50"
                      >
                        <ChevronLeft className="w-4 h-4" />
                      </button>
                      <span className="text-sm text-slate-300">
                        Page {currentPage + 1} of {totalPages}
                      </span>
                      <button
                        onClick={() => setCurrentPage(currentPage + 1)}
                        disabled={currentPage >= totalPages - 1}
                        className="p-2 text-slate-400 hover:text-white disabled:opacity-50"
                      >
                        <ChevronRight className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => setCurrentPage(totalPages - 1)}
                        disabled={currentPage >= totalPages - 1}
                        className="p-2 text-slate-400 hover:text-white disabled:opacity-50"
                      >
                        <ChevronLast className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Comprehensive Analysis View */}
          {activeView === 'analysis' && (
            <div className="h-full flex flex-col">
                <div className="h-full overflow-y-auto p-6">
                <div className="space-y-6">
                  {/* Analysis Header */}
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-2xl font-bold text-white flex items-center">
                        <Code className="w-8 h-8 text-blue-600 mr-3" />
                        Code Analysis
                      </h2>
                      <p className="text-gray-400 mt-1">
                        Comprehensive analysis of your project
                      </p>
                </div>
                    <div className="flex items-center space-x-3">
                      <span className="text-sm text-gray-500">
                        {files.length} files analyzed
                      </span>
                  </div>
                </div>

                  {/* Analysis Results Grid */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Project Overview */}
                    <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
                      <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                        <BarChart3 className="w-5 h-5 text-blue-400 mr-2" />
                        Project Overview
                      </h3>
                      <div className="space-y-3">
                        <div className="flex justify-between items-center">
                          <span className="text-slate-300">Total Files</span>
                          <span className="text-white font-semibold">{files.length}</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-slate-300">Java Files</span>
                          <span className="text-white font-semibold">
                            {files.filter(f => f.relativePath.endsWith('.java')).length}
                          </span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-slate-300">Test Files</span>
                          <span className="text-white font-semibold">
                            {files.filter(f => f.relativePath.includes('test')).length}
                          </span>
                        </div>
                        {assessment && (
                          <>
                            <div className="flex justify-between items-center">
                              <span className="text-slate-300">Code Smells</span>
                              <span className="text-white font-semibold">
                                {filteredAssessment?.evidences?.length || filteredAssessment?.summary?.totalFindings || 0}
                              </span>
                            </div>
                            <div className="flex justify-between items-center">
                              <span className="text-slate-300">Technical Debt</span>
                              <span className="text-white font-semibold">
                                {assessment.summary?.maintainabilityIndex ? `${assessment.summary.maintainabilityIndex.toFixed(1)}/100` : 'N/A'}
                              </span>
                            </div>
                          </>
                        )}
                      </div>
                    </div>

                    {/* File Analysis */}
                    <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold text-white flex items-center">
                          <FileText className="w-5 h-5 text-green-400 mr-2" />
                          File Analysis
                        </h3>
                        <div className="flex items-center space-x-2">
                          <select 
                            className="bg-slate-700 text-white text-xs px-2 py-1 rounded border border-slate-600"
                            onChange={(e) => {
                              // TODO: Implement sorting logic
                              console.log('Sort by:', e.target.value);
                            }}
                          >
                            <option value="name">Sort by Name</option>
                            <option value="code-smells">Sort by Code Smells</option>
                            <option value="severity">Sort by Severity</option>
                            <option value="size">Sort by Size</option>
                          </select>
                        </div>
                      </div>
                      <div className="space-y-3 max-h-64 overflow-y-auto">
                        {files.slice(0, 10).map((file, index) => {
                          // Count code smells for this file
                          const fileCodeSmells = assessment?.evidences?.filter((evidence: any) => 
                            evidence.pointer?.file?.includes(file.relativePath)
                          ) || [];
                          
                          const hasCodeSmells = fileCodeSmells.length > 0;
                          const majorSmells = fileCodeSmells.filter((s: any) => s.severity === 'MAJOR').length;
                          const minorSmells = fileCodeSmells.filter((s: any) => s.severity === 'MINOR').length;
                          
                          return (
                            <div key={index} className={`flex items-center justify-between p-3 rounded-lg ${
                              hasCodeSmells ? 'bg-red-900/20 border border-red-500/30' : 'bg-slate-700'
                            }`}>
                              <div className="flex items-center space-x-3">
                                <FileText className={`w-4 h-4 ${hasCodeSmells ? 'text-red-400' : 'text-slate-400'}`} />
                                <span className="text-white text-sm truncate">
                                  {file.name || file.relativePath.split('/').pop()}
                                </span>
                                {hasCodeSmells && (
                                  <div className="flex items-center space-x-1">
                                    {majorSmells > 0 && (
                                      <span className="px-1.5 py-0.5 text-xs bg-red-500 text-white rounded-full">
                                        {majorSmells}
                                      </span>
                                    )}
                                    {minorSmells > 0 && (
                                      <span className="px-1.5 py-0.5 text-xs bg-yellow-500 text-white rounded-full">
                                        {minorSmells}
                                      </span>
                                    )}
                                  </div>
                                )}
                              </div>
                              <div className="flex items-center space-x-2">
                                <span className="text-xs text-slate-400">
                                  {file.metrics?.linesOfCode ? `${file.metrics.linesOfCode} lines` : 'N/A'}
                                </span>
                                {hasCodeSmells && (
                                  <span className="text-xs text-red-400 font-medium">
                                    {fileCodeSmells.length} issues
                                  </span>
                                )}
                                <button
                                  onClick={() => {
                                    setSelectedFile(file);
                                    loadFileContent(file);
                                  }}
                                  className="p-1 text-blue-400 hover:text-blue-300 transition-colors"
                                  title="View File"
                                >
                                  <Eye className="w-4 h-4" />
                                </button>
                              </div>
                            </div>
                          );
                        })}
                        {files.length > 10 && (
                          <div className="text-center text-slate-400 text-sm">
                            ... and {files.length - 10} more files
                          </div>
                        )}
                      </div>
                    </div>
                  </div>



                  {/* File Selection Prompt */}
                  {!selectedFile && (
                    <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
                      <div className="text-center">
                        <FileText className="w-12 h-12 text-slate-400 mx-auto mb-4" />
                        <h3 className="text-lg font-semibold text-white mb-2">Detailed File Analysis</h3>
                        <p className="text-slate-400 mb-4">
                          Select a file from the Files tab to see detailed analysis including:
                        </p>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
                          <div className="space-y-2">
                            <div className="flex items-center space-x-2">
                              <CheckCircle className="w-4 h-4 text-green-400" />
                              <span className="text-slate-300">Code quality metrics</span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <CheckCircle className="w-4 h-4 text-green-400" />
                              <span className="text-slate-300">Complexity analysis</span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <CheckCircle className="w-4 h-4 text-green-400" />
                              <span className="text-slate-300">Security vulnerabilities</span>
                            </div>
                          </div>
                          <div className="space-y-2">
                            <div className="flex items-center space-x-2">
                              <CheckCircle className="w-4 h-4 text-green-400" />
                              <span className="text-slate-300">Refactoring suggestions</span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <CheckCircle className="w-4 h-4 text-green-400" />
                              <span className="text-slate-300">Performance insights</span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <CheckCircle className="w-4 h-4 text-green-400" />
                              <span className="text-slate-300">Best practices</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {activeView === 'security' && (
            <div className="h-full overflow-y-auto p-6">
              <SecurityAnalysisDashboard 
                workspaceId={workspaceId}
                onVulnerabilitySelect={(vulnerability) => {
                  console.log('Selected vulnerability:', vulnerability);
                  // Handle vulnerability selection if needed
                }}
              />
            </div>
          )}

          {activeView === 'dependencies' && (
            <div className="h-full overflow-y-auto p-6">
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-2xl font-bold text-white">Dependency Analysis</h2>
                    <p className="text-slate-400">Understand file relationships and refactoring impact</p>
                  </div>
                  <button
                    onClick={loadDependencyGraph}
                    disabled={loadingDependencies}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors flex items-center space-x-2"
                  >
                    <RefreshCw className={`w-4 h-4 ${loadingDependencies ? 'animate-spin' : ''}`} />
                    <span>Refresh</span>
                  </button>
                </div>

                {/* Dependency Graph */}
                {loadingDependencies ? (
                  <div className="space-y-6">
                    <SkeletonChart className="h-96" />
                    <SkeletonCard />
                  </div>
                ) : (
                  <>
                    <DependencyGraph
                      nodes={[]}
                      selectedNode={selectedFile?.relativePath}
                      onNodeSelect={(nodeId) => {
                        const file = files.find(f => f.relativePath === nodeId);
                        if (file) {
                          setSelectedFile(file);
                        }
                      }}
                    />

                    {/* Dependency Metrics */}
                    {dependencyGraph?.metrics && (
                      <DependencyMetrics
                        metrics={dependencyGraph.metrics}
                        fileAnalysis={fileDependencyAnalysis || undefined}
                      />
                    )}
                  </>
                )}
              </div>
            </div>
          )}

          {activeView === 'enhanced' && (
            <div className="h-full overflow-y-auto">
              <div className="p-6">
                <div className="mb-6">
                  <h2 className="text-2xl font-bold text-white mb-2">Enhanced Refactoring</h2>
                  <p className="text-slate-400">AI-powered refactoring with comprehensive analysis and dependency mapping</p>
                </div>
                
                {/* File Selection */}
                <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 mb-6">
                  <h3 className="text-lg font-semibold text-white mb-4">Select File for Enhanced Refactoring</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {files.slice(0, 9).map((file) => (
                      <button
                        key={file.relativePath}
                        onClick={async () => {
                          setSelectedFile(file);
                          setLoadingFileContent(true);
                          try {
                            const content = await apiClient.getFileContent(workspaceId, file.relativePath);
                            setFileContent(typeof content === 'string' ? content : content.content || '');
                            setActiveView('enhanced-refactoring');
                          } catch (error) {
                            console.error('Failed to load file content:', error);
                            setFileContent('// Failed to load file content');
                            setActiveView('enhanced-refactoring');
                          } finally {
                            setLoadingFileContent(false);
                          }
                        }}
                        className="bg-slate-700 hover:bg-slate-600 rounded-lg p-4 text-left transition-colors border border-slate-600 hover:border-blue-500"
                      >
                        <div className="flex items-center mb-2">
                          <FileText className="w-5 h-5 text-blue-400 mr-2" />
                          <span className="text-white font-medium truncate">{file.name}</span>
                        </div>
                        <p className="text-slate-400 text-sm truncate">{file.relativePath}</p>
                        <div className="flex items-center mt-2 text-xs text-slate-500">
                          <span>{file.metrics?.linesOfCode || 0} lines</span>
                        </div>
                      </button>
                    ))}
                  </div>
                  
                  {files.length > 9 && (
                    <div className="mt-4 text-center">
                      <button className="text-blue-400 hover:text-blue-300 text-sm">
                        View all {files.length} files
                      </button>
                    </div>
                  )}
                </div>
                
                {/* Quick Actions */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
                    <div className="flex items-center mb-4">
                      <Brain className="w-8 h-8 text-purple-400 mr-3" />
                      <h4 className="text-lg font-semibold text-white">AI Analysis</h4>
                    </div>
                    <p className="text-slate-400 text-sm mb-4">Comprehensive code analysis with AI-powered insights</p>
                    <button 
                      onClick={() => setActiveView('analysis')}
                      className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                    >
                      Start Analysis
                    </button>
                  </div>
                  
                  <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
                    <div className="flex items-center mb-4">
                      <Network className="w-8 h-8 text-blue-400 mr-3" />
                      <h4 className="text-lg font-semibold text-white">Dependencies</h4>
                    </div>
                    <p className="text-slate-400 text-sm mb-4">Visualize and analyze code dependencies</p>
                    <button 
                      onClick={() => setActiveView('dependencies')}
                      className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                    >
                      View Dependencies
                    </button>
                  </div>
                  
                  <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
                    <div className="flex items-center mb-4">
                      <Zap className="w-8 h-8 text-yellow-400 mr-3" />
                      <h4 className="text-lg font-semibold text-white">Quick Refactor</h4>
                    </div>
                    <p className="text-slate-400 text-sm mb-4">Fast refactoring with automated suggestions</p>
                    <button 
                      onClick={() => setActiveView('refactoring')}
                      className="bg-yellow-600 hover:bg-yellow-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                    >
                      Start Refactoring
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeView === 'enhanced-refactoring' && selectedFile && (
            <div className="h-full overflow-y-auto">
              <EnhancedRefactoringDashboard 
                workspaceId={workspaceId}
                selectedFile={selectedFile.relativePath}
                fileContent={fileContent}
                codeSmells={fileCodeSmells}
                onRefactoringComplete={(refactoredCode) => {
                  console.log('Enhanced refactoring completed:', refactoredCode);
                  setActiveView('enhanced');
                }}
                onBack={() => setActiveView('enhanced')}
              />
            </div>
          )}

          {activeView === 'refactoring' && (
            <div className="h-full overflow-y-auto p-6">
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-2xl font-bold text-white">Refactoring Operations</h2>
                    <p className="text-slate-400">Safe refactoring with ripple impact analysis</p>
                  </div>
                </div>

                <RefactoringOperations
                  workspaceId={workspaceId}
                  selectedFile={selectedFile?.relativePath || ''}
                  onRefactoringComplete={() => {
                    // Refresh the analysis after refactoring
                    if (onAnalysisComplete) {
                      onAnalysisComplete();
                    }
                  }}
                />
              </div>
            </div>
          )}

          {activeView === 'llm-refactoring' && (
            <div className="h-full overflow-y-auto p-6">
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-2xl font-bold text-white">AI-Powered Refactoring</h2>
                    <p className="text-slate-400">Intelligent code refactoring with LLM assistance</p>
                  </div>
                </div>

                <LLMRefactoring
                  workspaceId={workspaceId}
                  selectedFile={selectedFile?.relativePath || ''}
                  fileContent={selectedFile ? `// Loading content for ${selectedFile.name}...` : ''}
                  onRefactoringComplete={(refactoredCode) => {
                    console.log('LLM refactoring completed:', refactoredCode);
                    if (onAnalysisComplete) {
                      onAnalysisComplete();
                    }
                  }}
                  onBackToAnalysis={() => setActiveView('analysis')}
                />
              </div>
            </div>
          )}

          {activeView === 'controlled-refactoring' && (
            <div className="h-full overflow-y-auto p-6">
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-2xl font-bold text-white">Controlled AI Refactoring</h2>
                    <p className="text-slate-400">Safe, intelligent refactoring with AI recommendations</p>
                  </div>
                </div>

                <ControlledRefactoring
                  workspaceId={workspaceId}
                  selectedFile={selectedFile?.relativePath || ''}
                  fileContent={selectedFile ? `// Loading content for ${selectedFile.name}...` : ''}
                  codeSmells={fileAnalysis?.codeSmells || []}
                  onRefactoringComplete={(refactoredCode) => {
                    console.log('Controlled refactoring completed:', refactoredCode);
                    if (onAnalysisComplete) {
                      onAnalysisComplete();
                    }
                  }}
                  onBack={() => setActiveView('analysis')}
                />
              </div>
            </div>
          )}

          {activeView === 'monitor' && (
            <RefactoringMonitor
              workspaceId={workspaceId}
              onOperationComplete={() => {
                // Refresh the analysis after refactoring operations
                if (onAnalysisComplete) {
                  onAnalysisComplete();
                }
              }}
            />
          )}

          {activeView === 'projects' && (
            <div className="h-full overflow-y-auto p-6">
              <ProjectHub
                onProjectSelect={(project) => {
                  console.log('Project selected:', project);
                  // Handle project selection - could switch workspace
                }}
                onProjectDelete={(projectId) => {
                  console.log('Project deleted:', projectId);
                  // Handle project deletion
                }}
                onProjectAnalyze={(project) => {
                  console.log('Analyze project:', project);
                  // Convert project to workspace format and start analysis
                  const workspace = {
                    id: project.id,
                    name: project.name,
                    sourceFiles: project.sourceFiles,
                    testFiles: project.testFiles,
                    createdAt: project.createdAt
                  };
                  
                  // Set as current workspace and start analysis
                  setCurrentWorkspace?.(workspace);
                  setActiveView('analysis');
                  
                  // Start analysis after a short delay to ensure state is updated
                  setTimeout(() => {
                    startAnalysisWithWorkspace(workspace);
                  }, 100);
                }}
              />
            </div>
          )}
            </>
          )}
        </div>
      </div>

      {/* Code Preview Modal */}
      {showCodePreview && currentPreviewFile && (
        <ErrorBoundary>
          <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-800 rounded-lg border border-slate-700 w-full max-w-7xl h-[90vh] flex flex-col">
              {/* Header */}
              <div className="flex items-center justify-between p-4 border-b border-slate-700">
                <div>
                  <h2 className="text-xl font-semibold text-white">{currentPreviewFile.name}</h2>
                  <p className="text-sm text-slate-400">{currentPreviewFile.relativePath}</p>
                </div>
                <div className="flex items-center space-x-4">
                  <span className="text-sm text-slate-300">
                    Code Smells: {fileCodeSmells.length}
                  </span>
                  <button
                    onClick={() => {
                      console.log('Current file code smells:', fileCodeSmells);
                      console.log('Current file content length:', fileContent.length);
                    }}
                    className="text-blue-400 hover:text-blue-300 text-xs px-2 py-1 bg-blue-500/20 rounded"
                  >
                    Debug
                  </button>
                  <button
                    onClick={() => setShowCodePreview(false)}
                    className="text-slate-400 hover:text-white"
                  >
                    ✕
                  </button>
                </div>
              </div>
              
              {/* Content */}
              <div className="flex-1 flex overflow-hidden">
                {/* Code Content */}
                <div className="flex-1 overflow-auto p-4">
                  {/* Code Smell Legend */}
                  <div className="mb-4 bg-slate-800 rounded-lg p-3 border border-slate-600">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-sm font-semibold text-white">Code Smell Types:</h4>
                      <button
                        onClick={() => {
                          if (workspaceId) {
                            startAnalysisWithWorkspace({ id: workspaceId });
                          }
                        }}
                        className="text-xs bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded transition-colors"
                        title="Re-run analysis with updated detectors"
                      >
                        Refresh Analysis
                      </button>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <div className="flex items-center space-x-2">
                        <div className="w-3 h-3 bg-red-500 rounded"></div>
                        <span className="text-xs text-slate-300">Long Method</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="w-3 h-3 bg-purple-500 rounded"></div>
                        <span className="text-xs text-slate-300">God Class</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="w-3 h-3 bg-orange-500 rounded"></div>
                        <span className="text-xs text-slate-300">Duplicate Code</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="w-3 h-3 bg-yellow-500 rounded"></div>
                        <span className="text-xs text-slate-300">Complex Method</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-slate-900 rounded-lg border border-slate-600">
                    <pre className="text-sm text-slate-300 p-4">
                      {fileContent.split('\n').map((line, index) => {
                        const lineNumber = index + 1;
                        const codeSmell = fileCodeSmells.find(smell => {
                          // Handle cases where line ranges might be too broad
                          const startLine = smell.startLine || 1;
                          const endLine = smell.endLine || smell.startLine || 1;
                          
                          // For god class, only highlight the first few lines if the range is too broad
                          if (smell.detectorId === 'design.god-class' && (endLine - startLine) > 20) {
                            return lineNumber >= startLine && lineNumber <= Math.min(startLine + 5, endLine);
                          }
                          
                          return lineNumber >= startLine && lineNumber <= endLine;
                        });
                        
                        // Check if this is the first line of a code smell (to show badge only once)
                        const isFirstLineOfSmell = codeSmell && lineNumber === (codeSmell.startLine || 1);
                        
                        let lineClass = '';
                        let smellTypeColor = '';
                        let smellTypeName = '';
                        
                        if (codeSmell) {
                          // Get smell type from detectorId
                          const smellType = codeSmell.detectorId || codeSmell.type || 'unknown';
                          
                          // Color coding based on smell type
                          switch (smellType) {
                            case 'design.long-method':
                              lineClass = 'bg-red-500/20 border-l-4 border-red-500 pl-2';
                              smellTypeColor = 'bg-red-500/80 text-white';
                              smellTypeName = 'Long Method';
                              break;
                            case 'design.god-class':
                              lineClass = 'bg-purple-500/20 border-l-4 border-purple-500 pl-2';
                              smellTypeColor = 'bg-purple-500/80 text-white';
                              smellTypeName = 'God Class';
                              break;
                            case 'design.duplicate-code':
                              lineClass = 'bg-orange-500/20 border-l-4 border-orange-500 pl-2';
                              smellTypeColor = 'bg-orange-500/80 text-white';
                              smellTypeName = 'Duplicate Code';
                              break;
                            case 'design.complex-method':
                              lineClass = 'bg-yellow-500/20 border-l-4 border-yellow-500 pl-2';
                              smellTypeColor = 'bg-yellow-500/80 text-white';
                              smellTypeName = 'Complex Method';
                              break;
                            case 'design.long-parameter-list':
                              lineClass = 'bg-pink-500/20 border-l-4 border-pink-500 pl-2';
                              smellTypeColor = 'bg-pink-500/80 text-white';
                              smellTypeName = 'Long Parameter List';
                              break;
                            case 'design.feature-envy':
                              lineClass = 'bg-cyan-500/20 border-l-4 border-cyan-500 pl-2';
                              smellTypeColor = 'bg-cyan-500/80 text-white';
                              smellTypeName = 'Feature Envy';
                              break;
                            case 'design.data-clumps':
                              lineClass = 'bg-teal-500/20 border-l-4 border-teal-500 pl-2';
                              smellTypeColor = 'bg-teal-500/80 text-white';
                              smellTypeName = 'Data Clumps';
                              break;
                            case 'design.primitive-obsession':
                              lineClass = 'bg-indigo-500/20 border-l-4 border-indigo-500 pl-2';
                              smellTypeColor = 'bg-indigo-500/80 text-white';
                              smellTypeName = 'Primitive Obsession';
                              break;
                            case 'design.switch-statements':
                              lineClass = 'bg-rose-500/20 border-l-4 border-rose-500 pl-2';
                              smellTypeColor = 'bg-rose-500/80 text-white';
                              smellTypeName = 'Switch Statements';
                              break;
                            case 'design.temporary-field':
                              lineClass = 'bg-emerald-500/20 border-l-4 border-emerald-500 pl-2';
                              smellTypeColor = 'bg-emerald-500/80 text-white';
                              smellTypeName = 'Temporary Field';
                              break;
                            case 'design.lazy-class':
                              lineClass = 'bg-violet-500/20 border-l-4 border-violet-500 pl-2';
                              smellTypeColor = 'bg-violet-500/80 text-white';
                              smellTypeName = 'Lazy Class';
                              break;
                            case 'design.middle-man':
                              lineClass = 'bg-amber-500/20 border-l-4 border-amber-500 pl-2';
                              smellTypeColor = 'bg-amber-500/80 text-white';
                              smellTypeName = 'Middle Man';
                              break;
                            case 'design.speculative-generality':
                              lineClass = 'bg-sky-500/20 border-l-4 border-sky-500 pl-2';
                              smellTypeColor = 'bg-sky-500/80 text-white';
                              smellTypeName = 'Speculative Generality';
                              break;
                            case 'design.message-chains':
                              lineClass = 'bg-lime-500/20 border-l-4 border-lime-500 pl-2';
                              smellTypeColor = 'bg-lime-500/80 text-white';
                              smellTypeName = 'Message Chains';
                              break;
                            case 'design.inappropriate-intimacy':
                              lineClass = 'bg-red-600/20 border-l-4 border-red-600 pl-2';
                              smellTypeColor = 'bg-red-600/80 text-white';
                              smellTypeName = 'Inappropriate Intimacy';
                              break;
                            case 'design.shotgun-surgery':
                              lineClass = 'bg-orange-600/20 border-l-4 border-orange-600 pl-2';
                              smellTypeColor = 'bg-orange-600/80 text-white';
                              smellTypeName = 'Shotgun Surgery';
                              break;
                            case 'design.divergent-change':
                              lineClass = 'bg-fuchsia-500/20 border-l-4 border-fuchsia-500 pl-2';
                              smellTypeColor = 'bg-fuchsia-500/80 text-white';
                              smellTypeName = 'Divergent Change';
                              break;
                            case 'design.parallel-inheritance':
                              lineClass = 'bg-blue-500/20 border-l-4 border-blue-500 pl-2';
                              smellTypeColor = 'bg-blue-500/80 text-white';
                              smellTypeName = 'Parallel Inheritance';
                              break;
                            case 'design.excessive-comments':
                              lineClass = 'bg-gray-500/20 border-l-4 border-gray-500 pl-2';
                              smellTypeColor = 'bg-gray-500/80 text-white';
                              smellTypeName = 'Excessive Comments';
                              break;
                            case 'design.dead-code':
                              lineClass = 'bg-red-800/20 border-l-4 border-red-800 pl-2';
                              smellTypeColor = 'bg-red-800/80 text-white';
                              smellTypeName = 'Dead Code';
                              break;
                            case 'design.large-class':
                              lineClass = 'bg-purple-600/20 border-l-4 border-purple-600 pl-2';
                              smellTypeColor = 'bg-purple-600/80 text-white';
                              smellTypeName = 'Large Class';
                              break;
                            case 'design.data-class':
                              lineClass = 'bg-green-600/20 border-l-4 border-green-600 pl-2';
                              smellTypeColor = 'bg-green-600/80 text-white';
                              smellTypeName = 'Data Class';
                              break;
                            case 'design.magic-numbers':
                              lineClass = 'bg-yellow-600/20 border-l-4 border-yellow-600 pl-2';
                              smellTypeColor = 'bg-yellow-600/80 text-white';
                              smellTypeName = 'Magic Numbers';
                              break;
                            case 'design.string-constants':
                              lineClass = 'bg-teal-600/20 border-l-4 border-teal-600 pl-2';
                              smellTypeColor = 'bg-teal-600/80 text-white';
                              smellTypeName = 'String Constants';
                              break;
                            case 'design.inconsistent-naming':
                              lineClass = 'bg-pink-600/20 border-l-4 border-pink-600 pl-2';
                              smellTypeColor = 'bg-pink-600/80 text-white';
                              smellTypeName = 'Inconsistent Naming';
                              break;
                            case 'design.nested-conditionals':
                              lineClass = 'bg-indigo-600/20 border-l-4 border-indigo-600 pl-2';
                              smellTypeColor = 'bg-indigo-600/80 text-white';
                              smellTypeName = 'Nested Conditionals';
                              break;
                            case 'design.flag-arguments':
                              lineClass = 'bg-orange-500/20 border-l-4 border-orange-500 pl-2';
                              smellTypeColor = 'bg-orange-500/80 text-white';
                              smellTypeName = 'Flag Arguments';
                              break;
                            case 'design.try-catch-hell':
                              lineClass = 'bg-red-700/20 border-l-4 border-red-700 pl-2';
                              smellTypeColor = 'bg-red-700/80 text-white';
                              smellTypeName = 'Try-Catch Hell';
                              break;
                            case 'design.null-abuse':
                              lineClass = 'bg-gray-600/20 border-l-4 border-gray-600 pl-2';
                              smellTypeColor = 'bg-gray-600/80 text-white';
                              smellTypeName = 'Null Abuse';
                              break;
                            case 'design.type-embedded-name':
                              lineClass = 'bg-cyan-600/20 border-l-4 border-cyan-600 pl-2';
                              smellTypeColor = 'bg-cyan-600/80 text-white';
                              smellTypeName = 'Type Embedded Name';
                              break;
                            case 'design.refused-bequest':
                              lineClass = 'bg-purple-700/20 border-l-4 border-purple-700 pl-2';
                              smellTypeColor = 'bg-purple-700/80 text-white';
                              smellTypeName = 'Refused Bequest';
                              break;
                            case 'design.empty-catch-block':
                              lineClass = 'bg-red-900/20 border-l-4 border-red-900 pl-2';
                              smellTypeColor = 'bg-red-900/80 text-white';
                              smellTypeName = 'Empty Catch Block';
                              break;
                            case 'design.resource-leak':
                              lineClass = 'bg-orange-700/20 border-l-4 border-orange-700 pl-2';
                              smellTypeColor = 'bg-orange-700/80 text-white';
                              smellTypeName = 'Resource Leak';
                              break;
                            case 'design.raw-types':
                              lineClass = 'bg-yellow-700/20 border-l-4 border-yellow-700 pl-2';
                              smellTypeColor = 'bg-yellow-700/80 text-white';
                              smellTypeName = 'Raw Types';
                              break;
                            case 'design.circular-dependencies':
                              lineClass = 'bg-pink-700/20 border-l-4 border-pink-700 pl-2';
                              smellTypeColor = 'bg-pink-700/80 text-white';
                              smellTypeName = 'Circular Dependencies';
                              break;
                            case 'design.long-line':
                              lineClass = 'bg-gray-700/20 border-l-4 border-gray-700 pl-2';
                              smellTypeColor = 'bg-gray-700/80 text-white';
                              smellTypeName = 'Long Line';
                              break;
                            case 'design.string-concatenation':
                              lineClass = 'bg-teal-700/20 border-l-4 border-teal-700 pl-2';
                              smellTypeColor = 'bg-teal-700/80 text-white';
                              smellTypeName = 'String Concatenation';
                              break;
                            case 'design.generic-exception':
                              lineClass = 'bg-red-500/20 border-l-4 border-red-500 pl-2';
                              smellTypeColor = 'bg-red-500/80 text-white';
                              smellTypeName = 'Generic Exception';
                              break;
                            case 'design.single-letter-vars':
                              lineClass = 'bg-indigo-700/20 border-l-4 border-indigo-700 pl-2';
                              smellTypeColor = 'bg-indigo-700/80 text-white';
                              smellTypeName = 'Single Letter Variables';
                              break;
                            case 'design.hardcoded-credentials':
                              lineClass = 'bg-black/20 border-l-4 border-black pl-2';
                              smellTypeColor = 'bg-black/80 text-white';
                              smellTypeName = 'Hardcoded Credentials';
                              break;
                            default:
                              lineClass = 'bg-slate-500/20 border-l-4 border-slate-500 pl-2';
                              smellTypeColor = 'bg-slate-500/80 text-white';
                              smellTypeName = 'Code Smell';
                          }
                        }
                        
                        return (
                          <div key={index} className={`flex group hover:bg-slate-800/30 transition-colors ${lineClass}`}>
                            <span className="text-slate-500 w-12 text-right mr-4 select-none">
                              {lineNumber}
                            </span>
                            <span className="flex-1">
                              {line || '\u00A0'}
                            </span>
                            {/* Only show badge on the first line of each code smell */}
                            {isFirstLineOfSmell && (
                              <div className="ml-2 flex items-center space-x-2">
                                <span 
                                  className={`text-xs px-2 py-1 rounded font-medium ${smellTypeColor}`}
                                  title={`${smellTypeName}: ${codeSmell.summary || codeSmell.description || 'Code smell detected'} (Lines ${codeSmell.startLine}-${codeSmell.endLine})`}
                                >
                                  {smellTypeName}
                                </span>
                                <span className="text-xs px-2 py-1 rounded bg-slate-700 text-slate-300">
                                {codeSmell.severity}
                              </span>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </pre>
                  </div>
                </div>
                
                {/* Code Smells Sidebar */}
                <div className="w-80 bg-slate-700 border-l border-slate-600 overflow-y-auto p-4">
                  <h3 className="text-white font-semibold mb-4">Code Smells ({fileCodeSmells.length})</h3>
                  {fileCodeSmells.length > 0 ? (
                    <div className="space-y-3">
                      {fileCodeSmells.map((smell, index) => {
                        // Get color based on smell type
                        const getSmellTypeColor = (detectorId: string) => {
                          switch (detectorId) {
                            case 'design.long-method':
                              return 'bg-red-500/80 text-white';
                            case 'design.god-class':
                              return 'bg-purple-500/80 text-white';
                            case 'design.duplicate-code':
                              return 'bg-orange-500/80 text-white';
                            case 'design.complex-method':
                              return 'bg-yellow-500/80 text-white';
                            case 'design.long-parameter-list':
                              return 'bg-pink-500/80 text-white';
                            case 'design.feature-envy':
                              return 'bg-cyan-500/80 text-white';
                            case 'design.data-clumps':
                              return 'bg-teal-500/80 text-white';
                            case 'design.primitive-obsession':
                              return 'bg-indigo-500/80 text-white';
                            case 'design.switch-statements':
                              return 'bg-rose-500/80 text-white';
                            case 'design.temporary-field':
                              return 'bg-emerald-500/80 text-white';
                            case 'design.lazy-class':
                              return 'bg-violet-500/80 text-white';
                            case 'design.middle-man':
                              return 'bg-amber-500/80 text-white';
                            case 'design.speculative-generality':
                              return 'bg-sky-500/80 text-white';
                            case 'design.message-chains':
                              return 'bg-lime-500/80 text-white';
                            case 'design.inappropriate-intimacy':
                              return 'bg-red-600/80 text-white';
                            case 'design.shotgun-surgery':
                              return 'bg-orange-600/80 text-white';
                            case 'design.divergent-change':
                              return 'bg-fuchsia-500/80 text-white';
                            case 'design.parallel-inheritance':
                              return 'bg-blue-500/80 text-white';
                            case 'design.excessive-comments':
                              return 'bg-gray-500/80 text-white';
                            case 'design.dead-code':
                              return 'bg-red-800/80 text-white';
                            case 'design.large-class':
                              return 'bg-purple-600/80 text-white';
                            case 'design.data-class':
                              return 'bg-green-600/80 text-white';
                            case 'design.magic-numbers':
                              return 'bg-yellow-600/80 text-white';
                            case 'design.string-constants':
                              return 'bg-teal-600/80 text-white';
                            case 'design.inconsistent-naming':
                              return 'bg-pink-600/80 text-white';
                            case 'design.nested-conditionals':
                              return 'bg-indigo-600/80 text-white';
                            case 'design.flag-arguments':
                              return 'bg-orange-500/80 text-white';
                            case 'design.try-catch-hell':
                              return 'bg-red-700/80 text-white';
                            case 'design.null-abuse':
                              return 'bg-gray-600/80 text-white';
                            case 'design.type-embedded-name':
                              return 'bg-cyan-600/80 text-white';
                            case 'design.refused-bequest':
                              return 'bg-purple-700/80 text-white';
                            case 'design.empty-catch-block':
                              return 'bg-red-900/80 text-white';
                            case 'design.resource-leak':
                              return 'bg-orange-700/80 text-white';
                            case 'design.raw-types':
                              return 'bg-yellow-700/80 text-white';
                            case 'design.circular-dependencies':
                              return 'bg-pink-700/80 text-white';
                            case 'design.long-line':
                              return 'bg-gray-700/80 text-white';
                            case 'design.string-concatenation':
                              return 'bg-teal-700/80 text-white';
                            case 'design.generic-exception':
                              return 'bg-red-500/80 text-white';
                            case 'design.single-letter-vars':
                              return 'bg-indigo-700/80 text-white';
                            case 'design.hardcoded-credentials':
                              return 'bg-black/80 text-white';
                            default:
                              return 'bg-slate-500/80 text-white';
                          }
                        };

                        const getSmellTypeName = (detectorId: string) => {
                          switch (detectorId) {
                            case 'design.long-method':
                              return 'Long Method';
                            case 'design.god-class':
                              return 'God Class';
                            case 'design.duplicate-code':
                              return 'Duplicate Code';
                            case 'design.complex-method':
                              return 'Complex Method';
                            case 'design.long-parameter-list':
                              return 'Long Parameter List';
                            case 'design.feature-envy':
                              return 'Feature Envy';
                            case 'design.data-clumps':
                              return 'Data Clumps';
                            case 'design.primitive-obsession':
                              return 'Primitive Obsession';
                            case 'design.switch-statements':
                              return 'Switch Statements';
                            case 'design.temporary-field':
                              return 'Temporary Field';
                            case 'design.lazy-class':
                              return 'Lazy Class';
                            case 'design.middle-man':
                              return 'Middle Man';
                            case 'design.speculative-generality':
                              return 'Speculative Generality';
                            case 'design.message-chains':
                              return 'Message Chains';
                            case 'design.inappropriate-intimacy':
                              return 'Inappropriate Intimacy';
                            case 'design.shotgun-surgery':
                              return 'Shotgun Surgery';
                            case 'design.divergent-change':
                              return 'Divergent Change';
                            case 'design.parallel-inheritance':
                              return 'Parallel Inheritance';
                            case 'design.excessive-comments':
                              return 'Excessive Comments';
                            case 'design.dead-code':
                              return 'Dead Code';
                            case 'design.large-class':
                              return 'Large Class';
                            case 'design.data-class':
                              return 'Data Class';
                            case 'design.magic-numbers':
                              return 'Magic Numbers';
                            case 'design.string-constants':
                              return 'String Constants';
                            case 'design.inconsistent-naming':
                              return 'Inconsistent Naming';
                            case 'design.nested-conditionals':
                              return 'Nested Conditionals';
                            case 'design.flag-arguments':
                              return 'Flag Arguments';
                            case 'design.try-catch-hell':
                              return 'Try-Catch Hell';
                            case 'design.null-abuse':
                              return 'Null Abuse';
                            case 'design.type-embedded-name':
                              return 'Type Embedded Name';
                            case 'design.refused-bequest':
                              return 'Refused Bequest';
                            case 'design.empty-catch-block':
                              return 'Empty Catch Block';
                            case 'design.resource-leak':
                              return 'Resource Leak';
                            case 'design.raw-types':
                              return 'Raw Types';
                            case 'design.circular-dependencies':
                              return 'Circular Dependencies';
                            case 'design.long-line':
                              return 'Long Line';
                            case 'design.string-concatenation':
                              return 'String Concatenation';
                            case 'design.generic-exception':
                              return 'Generic Exception';
                            case 'design.single-letter-vars':
                              return 'Single Letter Variables';
                            case 'design.hardcoded-credentials':
                              return 'Hardcoded Credentials';
                            default:
                              return 'Code Smell';
                          }
                        };

                        return (
                        <div key={index} className="bg-slate-600 rounded-lg p-3">
                          <div className="flex items-center space-x-2 mb-2">
                              <span className={`px-2 py-1 rounded text-xs font-medium ${getSmellTypeColor(smell.detectorId)}`}>
                                {getSmellTypeName(smell.detectorId)}
                              </span>
                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                              smell.severity === 'CRITICAL' ? 'text-red-400 bg-red-500/20' :
                              smell.severity === 'MAJOR' ? 'text-orange-400 bg-orange-500/20' :
                              smell.severity === 'MINOR' ? 'text-yellow-400 bg-yellow-500/20' :
                              'text-slate-400 bg-slate-500/20'
                            }`}>
                              {smell.severity}
                            </span>
                          </div>
                          <p className="text-slate-300 text-xs mb-2">{smell.description}</p>
                          <p className="text-slate-400 text-xs">Lines: {smell.startLine}-{smell.endLine}</p>
                        </div>
                        );
                      })}
                    </div>
                  ) : (
                    <p className="text-slate-400 text-sm">No code smells detected</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </ErrorBoundary>
      )}
      </div>
    </div>
  );
}
