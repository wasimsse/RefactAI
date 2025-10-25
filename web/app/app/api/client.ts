// API client for RefactAI backend
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8081/api';

// Retry configuration
const RETRY_CONFIG = {
  maxRetries: 3,
  retryDelay: 1000, // 1 second
  retryMultiplier: 2, // Exponential backoff
};

// Enhanced fetch with retry logic
async function fetchWithRetry(
  url: string, 
  options: RequestInit = {}, 
  retryCount = 0
): Promise<Response> {
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    // If response is not ok, throw an error
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response;
  } catch (error) {
    // If we've reached max retries, throw the error
    if (retryCount >= RETRY_CONFIG.maxRetries) {
      throw error;
    }

    // Wait before retrying with exponential backoff
    const delay = RETRY_CONFIG.retryDelay * Math.pow(RETRY_CONFIG.retryMultiplier, retryCount);
    await new Promise(resolve => setTimeout(resolve, delay));

    // Retry the request
    return fetchWithRetry(url, options, retryCount + 1);
  }
}

export interface Workspace {
  id: string;
  name: string;
  sourceFiles: number;
  testFiles: number;
  createdAt: number;
}

export interface Assessment {
  projectId: string;
  evidences: ReasonEvidence[];
  summary: AssessmentSummary;
  metrics: ProjectMetrics;
  timestamp: number;
}

export interface ReasonEvidence {
  detectorId: string;
  pointer: CodePointer;
  metrics: Record<string, any>;
  summary: string;
  severity: string;
}

export interface CodePointer {
  file: string;
  className: string;
  methodName: string;
  startLine: number;
  endLine: number;
  startColumn: number;
  endColumn: number;
}

export interface AssessmentSummary {
  totalFindings: number;
  blockerFindings: number;
  criticalFindings: number;
  majorFindings: number;
  minorFindings: number;
  maintainabilityIndex: number;
  totalFiles: number;
  totalLines: number;
}

export interface ProjectMetrics {
  totalFiles: number;
  totalLines: number;
  totalFindings: number;
  findingsBySeverity: Record<string, number>;
  findingsByCategory: Record<string, number>;
  maintainabilityIndex: number;
}

export interface Plan {
  projectId: string;
  transforms: PlannedTransform[];
  summary: PlanSummary;
  timestamp: number;
}

export interface PlannedTransform {
  id: string;
  name: string;
  description: string;
  target: any;
  location: CodePointer;
  metadata: Record<string, any>;
  priority: number;
  timestamp: number;
}

export interface PlanSummary {
  totalTransforms: number;
  estimatedPayoff: number;
  estimatedRisk: number;
  estimatedCost: number;
  timestamp: number;
}

export interface ApplyResult {
  projectId: string;
  results: TransformResult[];
  failures: FailedTransform[];
  verification: VerificationResult;
  timestamp: number;
}

export interface TransformResult {
  transformId: string;
  changes: FileChange[];
  verification: VerificationResult;
  timestamp: number;
}

export interface FileChange {
  file: string;
  type: string;
  description: string;
  timestamp: number;
}

export interface FailedTransform {
  transformId: string;
  error: string;
  timestamp: number;
}

export interface VerificationResult {
  success: boolean;
  message: string;
  metrics: Record<string, any>;
}

export interface FileInfo {
  name: string;
  relativePath: string;
  type: 'SOURCE' | 'TEST' | 'RESOURCE' | 'CONFIG';
  metrics: {
    linesOfCode: number;
    cyclomaticComplexity: number;
    cognitiveComplexity: number;
    methodCount: number;
    classCount: number;
    commentLines: number;
    blankLines: number;
  };
  findings: number;
  lastModified: number;
}

// Code Analysis Types
export interface CodeAnalysisResult {
  workspaceId: string;
  analyzedFiles: number;
  totalSmells: number;
  totalTechnicalDebt: number;
  averageTechnicalDebt: number;
  smellDensity: number;
  overallHealth: string;
  priorityRecommendation: string;
  recommendations: string[];
  smellSummary: Record<string, number>;
  severitySummary: Record<string, number>;
  categorySummary: Record<string, number>;
  fileAnalyses: FileAnalysis[];
}

export interface SecurityVulnerability {
  type: string;
  category: string;
  severity: string;
  title: string;
  description: string;
  recommendation: string;
  startLine: number;
  endLine: number;
  remediationSteps: string[];
}

export interface FileSecurityAnalysis {
  filePath: string;
  vulnerabilities: SecurityVulnerability[];
  hasError: boolean;
  errorMessage?: string;
}

export interface SecurityAnalysisResult {
  workspaceId: string;
  fileAnalyses: FileSecurityAnalysis[];
  typeSummary: Record<string, number>;
  categorySummary: Record<string, number>;
  severitySummary: Record<string, number>;
  totalVulnerabilities: number;
  securityScore: number;
  overallSecurityStatus: string;
  recommendations: string[];
  analyzedFiles: number;
  priorityRecommendation: string;
}

export interface FileAnalysis {
  filePath: string;
  smells: CodeSmell[];
  metrics: Record<string, any>;
  technicalDebtScore: number;
  refactoringPlan: Record<string, string[]>;
  hasError: boolean;
  errorMessage?: string;
}

export interface CodeSmell {
  type: string;
  category: string;
  severity: string;
  title: string;
  description: string;
  recommendation: string;
  startLine: number;
  endLine: number;
  refactoringSuggestions: string[];
}

export interface FileMetrics {
  codeLines: number;
  fieldCount: number;
  commentRatio: number;
  classCount: number;
  totalLines: number;
  blankLines: number;
  commentLines: number;
  codeDensity: number;
  cognitiveComplexity: number;
  methodCount: number;
  cyclomaticComplexity: number;
}

// Enhanced Analysis Types
export interface EnhancedFileMetrics {
  linesOfCode: number;
  cyclomaticComplexity: number;
  cognitiveComplexity: number;
  methodCount: number;
  classCount: number;
  commentLines: number;
  blankLines: number;
  maintainabilityIndex: number;
  technicalDebtRatio: number;
  qualityGrade: string;
  codeSmells: number;
  criticalIssues: number;
  majorIssues: number;
  minorIssues: number;
  codeCoverage: number;
  documentationCoverage: number;
  hasTests: boolean;
  hasDocumentation: boolean;
  overallScore: number;
  qualityCategory: string;
  needsImmediateAttention: boolean;
  refactoringPriority: number;
}

export interface QualityInsights {
  overallScore: number;
  qualityCategory: string;
  needsAttention: boolean;
  refactoringPriority: number;
  specificInsights: Record<string, string>;
}

export interface RefactoringRecommendations {
  priority: number;
  estimatedEffort: number;
  actions: Record<string, string>;
}


export interface FileDependencyAnalysis {
  filePath: string;
  dependencies: string[];
  reverseDependencies: string[];
  outgoingDependencies: number;
  incomingDependencies: number;
}

export interface DependencyMetrics {
  totalFiles: number;
  totalDependencies: number;
  averageDependencies: number;
  mostCoupledFile: string;
  mostDependentFile: string;
  couplingDistribution: Record<number, number>;
}

export interface ProjectDependencyAnalysis {
  fileDependencies: Record<string, FileDependencyAnalysis>;
  dependencyGraph: Record<string, string[]>;
  reverseDependencyGraph: Record<string, string[]>;
  metrics: DependencyMetrics;
}

export interface DependencyGraphNode {
  id: string;
  label: string;
  path: string;
  type: 'java' | 'other';
  outgoingDependencies: number;
  incomingDependencies: number;
}

export interface DependencyGraphEdge {
  source: string;
  target: string;
  type: 'dependency';
}

export interface DependencyGraphData {
  nodes: DependencyGraphNode[];
  edges: DependencyGraphEdge[];
  metrics: DependencyMetrics;
}

export interface RippleEffectAnalysis {
  targetFile: string;
  affectedFiles: string[];
  impactCount: number;
  hasImpact: boolean;
}

export interface EnhancedAnalysisResult {
  success: boolean;
  metrics: EnhancedFileMetrics;
  filePath: string;
  workspaceId: string;
  qualityInsights: QualityInsights;
  recommendations: RefactoringRecommendations;
  codeSmells: CodeSmell[];
  timestamp: number;
}

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

class RefactAIClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    try {
      const response = await fetchWithRetry(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });

      return response.json();
    } catch (error) {
      // Convert fetch errors to ApiError
      if (error instanceof Error) {
        if (error.message.includes('HTTP')) {
          const statusMatch = error.message.match(/HTTP (\d+):/);
          const status = statusMatch ? parseInt(statusMatch[1]) : 500;
          throw new ApiError(status, error.message);
        }
        throw new ApiError(0, `Network error: ${error.message}`);
      }
      throw new ApiError(0, 'Unknown error occurred');
    }
  }

  // Health check
  async health(): Promise<{ status: string; timestamp: number; version: string }> {
    return this.request('/health');
  }

  // Workspace management
  async listWorkspaces(): Promise<Workspace[]> {
    return this.request('/workspaces');
  }

  async getWorkspace(id: string): Promise<Workspace> {
    return this.request(`/workspaces/${id}`);
  }

  async uploadProject(file: File): Promise<Workspace> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${this.baseUrl}/workspaces`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new ApiError(response.status, `Upload failed: ${response.statusText}`);
    }

    return response.json();
  }

  async cloneGitRepository(gitUrl: string, branch: string = 'main'): Promise<Workspace> {
    return this.request('/workspaces/git', {
      method: 'POST',
      body: JSON.stringify({ gitUrl, branch }),
    });
  }

  async deleteWorkspace(id: string): Promise<void> {
    await this.request(`/workspaces/${id}`, { method: 'DELETE' });
  }

  /**
   * Clear all workspaces for fresh start
   */
  async clearAllWorkspaces(): Promise<void> {
    return this.request('/workspaces/clear', { method: 'POST' });
  }

  // Assessment
  async assessProject(workspaceId: string): Promise<Assessment> {
    return this.request(`/workspaces/${workspaceId}/assess`, {
      method: 'POST',
      body: JSON.stringify({
        options: {},
        includeMetrics: true,
        includeDetails: true,
      }),
    });
  }

  async getAssessment(workspaceId: string): Promise<Assessment> {
    return this.request(`/workspaces/${workspaceId}/assessment`);
  }

  // Planning
  async generatePlan(workspaceId: string): Promise<Plan> {
    return this.request(`/workspaces/${workspaceId}/plan`, {
      method: 'POST',
      body: JSON.stringify({
        options: {},
        includePreview: true,
        includeConflicts: false,
      }),
    });
  }

  async getPlan(workspaceId: string): Promise<Plan> {
    return this.request(`/workspaces/${workspaceId}/plan`);
  }

  // Application
  async applyPlan(workspaceId: string, selectedTransforms: string[]): Promise<ApplyResult> {
    return this.request(`/workspaces/${workspaceId}/apply`, {
      method: 'POST',
      body: JSON.stringify({
        selectedTransforms,
        dryRun: false,
        verifyResults: true,
      }),
    });
  }

  // Artifacts
  async getArtifact(workspaceId: string, artifactName: string): Promise<string> {
    const response = await fetch(`${this.baseUrl}/workspaces/${workspaceId}/artifacts/${artifactName}`);
    
    if (!response.ok) {
      throw new ApiError(response.status, `Failed to get artifact: ${response.statusText}`);
    }

    return response.text();
  }

  // Get files in a workspace
  async getWorkspaceFiles(workspaceId: string): Promise<FileInfo[]> {
    return this.request(`/workspaces/${workspaceId}/files`);
  }

  async getFileContent(workspaceId: string, filePath: string): Promise<{ content: string; filePath: string; workspaceId: string }> {
    return this.request(`/workspaces/${workspaceId}/files/content?filePath=${encodeURIComponent(filePath)}`);
  }

  async analyzeFile(workspaceId: string, filePath: string): Promise<FileAnalysis> {
    return this.request(`/workspaces/${workspaceId}/files/analysis?filePath=${encodeURIComponent(filePath)}`);
  }

  async analyzeWorkspace(workspaceId: string): Promise<CodeAnalysisResult> {
    return this.request(`/workspaces/${workspaceId}/analyze`, {
      method: 'POST'
    });
  }
  
  async analyzeFileSecurity(workspaceId: string, filePath: string): Promise<FileSecurityAnalysis> {
    return this.request(`/workspaces/${workspaceId}/files/security?filePath=${encodeURIComponent(filePath)}`);
  }
  
  async analyzeWorkspaceSecurity(workspaceId: string): Promise<SecurityAnalysisResult> {
    return this.request(`/workspaces/${workspaceId}/security`, {
      method: 'POST'
    });
  }

  async analyzeFileEnhanced(workspaceId: string, filePath: string): Promise<EnhancedAnalysisResult> {
    return this.request(`/workspace-enhanced-analysis/analyze-file`, {
      method: 'POST',
      body: JSON.stringify({ workspaceId, filePath }),
    });
  }

  async analyzeFileLive(workspaceId: string, filePath: string, content: string): Promise<EnhancedAnalysisResult> {
    return this.request(`/workspace-enhanced-analysis/analyze-live`, {
      method: 'POST',
      body: JSON.stringify({ workspaceId, filePath, content }),
    });
  }

  // Dependency Analysis Methods
  async analyzeFileDependencies(workspaceId: string, filePath: string): Promise<FileDependencyAnalysis> {
    return this.request(`/workspaces/${workspaceId}/dependencies/file?filePath=${encodeURIComponent(filePath)}`);
  }

  async analyzeProjectDependencies(workspaceId: string): Promise<ProjectDependencyAnalysis> {
    return this.request(`/workspaces/${workspaceId}/dependencies/project`);
  }

  async getRippleEffectAnalysis(workspaceId: string, filePath: string): Promise<RippleEffectAnalysis> {
    return this.request(`/workspaces/${workspaceId}/dependencies/ripple-effect?filePath=${encodeURIComponent(filePath)}`);
  }

  async getDependencyGraph(workspaceId: string): Promise<DependencyGraphData> {
    return this.request(`/workspaces/${workspaceId}/dependencies/graph`);
  }

  // File pagination and summary
  async getWorkspaceFileSummary(workspaceId: string): Promise<{
    totalFiles: number;
    fileTypeCounts: Record<string, number>;
    sourceFiles: number;
    testFiles: number;
    configFiles: number;
    resourceFiles: number;
  }> {
    return this.request(`/workspaces/${workspaceId}/files/summary`);
  }

  async getWorkspaceFilesPaginated(
    workspaceId: string, 
    page: number = 0, 
    size: number = 50, 
    search?: string, 
    fileType?: string
  ): Promise<{
    files: FileInfo[];
    pagination: {
      currentPage: number;
      totalPages: number;
      totalFiles: number;
      pageSize: number;
      hasNext: boolean;
      hasPrevious: boolean;
    };
  }> {
    const params = new URLSearchParams({
      page: page.toString(),
      size: size.toString(),
    });
    
    if (search) params.append('search', search);
    if (fileType) params.append('fileType', fileType);
    
    return this.request(`/workspaces/${workspaceId}/files/paginated?${params.toString()}`);
  }
}

// Create and export the client instance
export const apiClient = new RefactAIClient();

// Export the client class for testing
export { RefactAIClient };
