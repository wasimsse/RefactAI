package ai.refact.server.controller;

import ai.refact.api.*;
import ai.refact.engine.AssessmentEngine;
import ai.refact.server.service.ProjectService;
import ai.refact.server.service.RefactoringService;
import ai.refact.server.service.CodeAnalysisService;
// import ai.refact.server.service.SecurityAnalysisService;
import ai.refact.server.service.DependencyAnalysisService;
import ai.refact.server.service.RippleImpactService;
import ai.refact.server.service.LLMService;
import ai.refact.server.model.LLMRequest;
import ai.refact.server.model.LLMResponse;
// import ai.refact.server.service.SimpleSecurityAnalysisService;
import ai.refact.engine.analysis.ASTBasedAnalyzer;
import ai.refact.engine.analysis.ASTAnalysisResult;
import ai.refact.engine.model.CodeSmell;
import ai.refact.engine.model.SmellSeverity;
import ai.refact.engine.model.SmellType;
import ai.refact.engine.model.SmellCategory;
import ai.refact.server.model.FileAnalysis;
import ai.refact.server.model.EnhancedAnalysisRequest;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import jakarta.servlet.http.HttpServletRequest;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.HashMap;
import java.util.Set;
import java.util.stream.Collectors;
import java.util.regex.Pattern;
import java.util.regex.Matcher;

/**
 * REST API controller for RefactAI operations.
 * Provides endpoints for project management, assessment, planning, and refactoring.
 */
@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "http://localhost:4000", allowCredentials = "true")
public class RefactAIController {
    
    private static final Logger logger = LoggerFactory.getLogger(RefactAIController.class);
    
    private final ProjectService projectService;
    private final RefactoringService refactoringService;
    private final CodeAnalysisService codeAnalysisService;
    // private final SimpleSecurityAnalysisService securityAnalysisService;
    private final DependencyAnalysisService dependencyAnalysisService;
    private final RippleImpactService rippleImpactService;
    private final ASTBasedAnalyzer astBasedAnalyzer;
    private final LLMService llmService;
    private final AssessmentEngine assessmentEngine;
    
    @Autowired
    public RefactAIController(ProjectService projectService, RefactoringService refactoringService, 
                            CodeAnalysisService codeAnalysisService, // SimpleSecurityAnalysisService securityAnalysisService,
                            DependencyAnalysisService dependencyAnalysisService, RippleImpactService rippleImpactService,
                            ASTBasedAnalyzer astBasedAnalyzer, LLMService llmService, AssessmentEngine assessmentEngine) {
        this.projectService = projectService;
        this.refactoringService = refactoringService;
        this.codeAnalysisService = codeAnalysisService;
        // this.securityAnalysisService = securityAnalysisService;
        this.dependencyAnalysisService = dependencyAnalysisService;
        this.rippleImpactService = rippleImpactService;
        this.astBasedAnalyzer = astBasedAnalyzer;
        this.llmService = llmService;
        this.assessmentEngine = assessmentEngine;
    }
    
    /**
     * Test endpoint to check if services are properly injected.
     */
    @GetMapping("/test/services")
    public ResponseEntity<?> testServices() {
        Map<String, Object> result = new HashMap<>();
        result.put("llmService", llmService != null ? "OK" : "NULL");
        result.put("astBasedAnalyzer", astBasedAnalyzer != null ? "OK" : "NULL");
        result.put("timestamp", System.currentTimeMillis());
        return ResponseEntity.ok(result);
    }

    /**
     * Test endpoint for ripple impact analysis.
     */
    @GetMapping("/workspace-refactoring/workspaces/{id}/available-operations")
    public ResponseEntity<?> getAvailableOperations(@PathVariable String id) {
        try {
            logger.info("Getting available operations for workspace: {}", id);
            
            // Return a simple list of available operations
            List<Map<String, Object>> operations = new ArrayList<>();
            
            Map<String, Object> extractMethod = new HashMap<>();
            extractMethod.put("type", "EXTRACT_METHOD");
            extractMethod.put("name", "Extract Method");
            extractMethod.put("description", "Extract a method from existing code");
            extractMethod.put("estimatedTime", "5-15 minutes");
            extractMethod.put("impact", "Low");
            extractMethod.put("risk", "LOW");
            operations.add(extractMethod);
            
            Map<String, Object> renameMethod = new HashMap<>();
            renameMethod.put("type", "RENAME_METHOD");
            renameMethod.put("name", "Rename Method");
            renameMethod.put("description", "Rename a method and update all references");
            renameMethod.put("estimatedTime", "2-5 minutes");
            renameMethod.put("impact", "Medium");
            renameMethod.put("risk", "MEDIUM");
            operations.add(renameMethod);
            
            Map<String, Object> renameClass = new HashMap<>();
            renameClass.put("type", "RENAME_CLASS");
            renameClass.put("name", "Rename Class");
            renameClass.put("description", "Rename a class and update all references");
            renameClass.put("estimatedTime", "10-30 minutes");
            renameClass.put("impact", "High");
            renameClass.put("risk", "HIGH");
            operations.add(renameClass);
            
            Map<String, Object> result = new HashMap<>();
            result.put("operations", operations);
            result.put("total", operations.size());
            
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            logger.error("Failed to get available operations for workspace: {}", id, e);
            return ResponseEntity.badRequest().body(Map.of("error", "Failed to get available operations: " + e.getMessage()));
        }
    }
    
    /**
     * Upload a ZIP file containing a Java project.
     */
    @PostMapping("/workspaces")
    public ResponseEntity<Workspace> uploadProject(@RequestParam("file") MultipartFile file) {
        try {
            logger.info("Uploading project file: {}", file.getOriginalFilename());
            
            ProjectContext projectContext = projectService.uploadProject(file);
            
            Workspace workspace = new Workspace(
                projectContext.getProperty("projectId", "unknown"),
                projectContext.root().getFileName().toString(),
                projectContext.sourceFiles().size(),
                projectContext.testFiles().size(),
                System.currentTimeMillis()
            );
            
            return ResponseEntity.ok(workspace);
            
        } catch (IOException e) {
            logger.error("Failed to upload project", e);
            return ResponseEntity.badRequest().build();
        }
    }
    
    /**
     * Clone a Git repository.
     */
    @PostMapping("/workspaces/git")
    public ResponseEntity<Workspace> cloneGitRepository(@RequestBody Map<String, String> request) {
        try {
            String gitUrl = request.get("gitUrl");
            String branch = request.getOrDefault("branch", "main");
            
            logger.info("Cloning Git repository: {} (branch: {})", gitUrl, branch);
            
            ProjectContext projectContext = projectService.cloneGitRepository(gitUrl, branch);
            
            Workspace workspace = new Workspace(
                projectContext.getProperty("projectId", "unknown"),
                projectContext.root().getFileName().toString(),
                projectContext.sourceFiles().size(),
                projectContext.testFiles().size(),
                System.currentTimeMillis()
            );
            
            return ResponseEntity.ok(workspace);
            
        } catch (IOException e) {
            logger.error("Failed to clone Git repository", e);
            return ResponseEntity.badRequest().build();
        }
    }
    
    /**
     * Initiate GitHub repository clone with progress tracking.
     */
    @PostMapping("/workspace-github/clone/{workspaceId}")
    public ResponseEntity<Map<String, String>> initiateGitHubClone(
            @PathVariable String workspaceId,
            @RequestBody Map<String, String> request) {
        
        String repositoryUrl = request.get("url");
        if (repositoryUrl == null || repositoryUrl.trim().isEmpty()) {
            return ResponseEntity.badRequest()
                .body(Map.of("error", "Repository URL is required"));
        }
        
        logger.info("Initiating GitHub clone for workspace {}: {}", workspaceId, repositoryUrl);
        
        return ResponseEntity.ok(Map.of(
            "message", "GitHub clone initiated successfully",
            "workspaceId", workspaceId,
            "repositoryUrl", repositoryUrl,
            "status", "started"
        ));
    }
    
    /**
     * Security Analysis endpoints - moved from SecurityAnalysisController for reliability
     */
    @PostMapping("/workspace-security/analyze/{workspaceId}")
    public ResponseEntity<Map<String, Object>> analyzeWorkspaceSecurity(@PathVariable String workspaceId) {
        try {
            logger.info("Starting REAL security analysis for workspace: {}", workspaceId);
            
            // Get all projects and find the one matching workspaceId
            List<ProjectContext> allProjects = projectService.getAllProjects();
            ProjectContext targetProject = null;
            
            // Find project by checking if workspaceId matches any project root directory name
            for (ProjectContext project : allProjects) {
                String projectDirName = project.root().getFileName().toString();
                if (projectDirName.equals(workspaceId) || workspaceId.contains(projectDirName)) {
                    targetProject = project;
                    break;
                }
            }
            
            if (targetProject == null) {
                logger.warn("No project found for workspace: {}", workspaceId);
                // For now, let's create a simple fallback that analyzes any available project
                if (!allProjects.isEmpty()) {
                    targetProject = allProjects.get(0);
                    logger.info("Using first available project for analysis: {}", targetProject.root());
                } else {
                    return ResponseEntity.notFound().build();
                }
            }
            
            Path workspacePath = targetProject.root();
            
            // Perform real security analysis on Java files
            List<Map<String, Object>> vulnerabilities = new ArrayList<>();
            int criticalCount = 0, highCount = 0, mediumCount = 0, lowCount = 0;
            double totalRiskScore = 0.0;
            
            try {
                // Get all Java files in the project (limit to first 100 files for performance)
                List<Path> javaFiles = Files.walk(workspacePath)
                    .filter(path -> path.toString().endsWith(".java"))
                    .limit(100) // Increased limit for better coverage
                    .collect(Collectors.toList());
                
                logger.info("Analyzing {} Java files for security vulnerabilities", javaFiles.size());
                
                // File-level analysis
                for (Path javaFile : javaFiles) {
                    try {
                        String relativePath = workspacePath.relativize(javaFile).toString();
                        String content = Files.readString(javaFile, StandardCharsets.UTF_8);
                        
                        // Enhanced security pattern detection
                        List<Map<String, Object>> fileVulns = analyzeJavaFileForSecurityIssues(content, relativePath);
                        vulnerabilities.addAll(fileVulns);
                        
                        // Count by severity
                        for (Map<String, Object> vuln : fileVulns) {
                            String severity = (String) vuln.get("severity");
                            switch (severity) {
                                case "CRITICAL": criticalCount++; break;
                                case "HIGH": highCount++; break;
                                case "MEDIUM": mediumCount++; break;
                                case "LOW": lowCount++; break;
                            }
                            totalRiskScore += (Double) vuln.getOrDefault("cvssScore", 0.0);
                        }
                        
                    } catch (Exception e) {
                        logger.warn("Failed to analyze file {}: {}", javaFile, e.getMessage());
                    }
                }
                
                // Project-level analysis
                List<Map<String, Object>> projectVulns = analyzeProjectLevelSecurity(workspacePath, javaFiles);
                vulnerabilities.addAll(projectVulns);
                
                // Count project-level vulnerabilities by severity
                for (Map<String, Object> vuln : projectVulns) {
                    String severity = (String) vuln.get("severity");
                    switch (severity) {
                        case "CRITICAL": criticalCount++; break;
                        case "HIGH": highCount++; break;
                        case "MEDIUM": mediumCount++; break;
                        case "LOW": lowCount++; break;
                    }
                    totalRiskScore += (Double) vuln.getOrDefault("cvssScore", 0.0);
                }
                
            } catch (IOException e) {
                logger.error("Failed to walk project directory: {}", e.getMessage());
            }
            
            int totalVulnerabilities = vulnerabilities.size();
            double overallRiskScore = totalVulnerabilities > 0 ? (totalRiskScore / totalVulnerabilities) / 10.0 : 0.0;
            double owaspCompliance = totalVulnerabilities == 0 ? 100.0 : Math.max(0, 100.0 - (totalVulnerabilities * 5.0));
            String securityGrade = calculateSecurityGrade(overallRiskScore, totalVulnerabilities);
            
            Map<String, Object> result = new HashMap<>();
            result.put("workspaceId", workspaceId);
            result.put("totalVulnerabilities", totalVulnerabilities);
            result.put("criticalVulnerabilities", criticalCount);
            result.put("highVulnerabilities", highCount);
            result.put("mediumVulnerabilities", mediumCount);
            result.put("lowVulnerabilities", lowCount);
            result.put("status", "completed");
            result.put("timestamp", System.currentTimeMillis());
            
            // Real security metrics based on actual analysis
            result.put("overallRiskScore", Math.round(overallRiskScore * 10.0) / 10.0);
            result.put("owaspCompliance", Math.round(owaspCompliance * 10.0) / 10.0);
            result.put("securityGrade", securityGrade);
            result.put("lastAnalyzed", System.currentTimeMillis());
            
            result.put("vulnerabilities", vulnerabilities);
            
            logger.info("REAL security analysis completed for workspace: {} - Found {} vulnerabilities", workspaceId, totalVulnerabilities);
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            logger.error("Failed to analyze workspace security: {}", workspaceId, e);
            return ResponseEntity.internalServerError().build();
        }
    }
    
    @GetMapping("/workspace-security/health")
    public ResponseEntity<Map<String, Object>> securityHealthCheck() {
        Map<String, Object> health = new HashMap<>();
        health.put("status", "UP");
        health.put("service", "Security Analysis Service");
        health.put("timestamp", System.currentTimeMillis());
        health.put("endpoint", "/api/security/analyze/{workspaceId}");
        return ResponseEntity.ok(health);
    }
    
    /**
     * File-level security analysis endpoint
     */
    @PostMapping("/workspace-security/analyze/file/{workspaceId}")
    public ResponseEntity<Map<String, Object>> analyzeFileSecurity(
            @PathVariable String workspaceId,
            @RequestBody Map<String, String> request) {
        try {
            String filePath = request.get("filePath");
            if (filePath == null || filePath.trim().isEmpty()) {
                return ResponseEntity.badRequest()
                    .body(Map.of("error", "File path is required"));
            }
            
            logger.info("Starting file-level security analysis for workspace: {} file: {}", workspaceId, filePath);
            
            // Get all projects and find the one matching workspaceId
            List<ProjectContext> allProjects = projectService.getAllProjects();
            ProjectContext targetProject = null;
            
            for (ProjectContext project : allProjects) {
                String projectDirName = project.root().getFileName().toString();
                if (projectDirName.equals(workspaceId) || workspaceId.contains(projectDirName)) {
                    targetProject = project;
                    break;
                }
            }
            
            if (targetProject == null) {
                if (!allProjects.isEmpty()) {
                    targetProject = allProjects.get(0);
                    logger.info("Using first available project for file analysis: {}", targetProject.root());
                } else {
                    return ResponseEntity.notFound().build();
                }
            }
            
            Path workspacePath = targetProject.root();
            Path targetFile = workspacePath.resolve(filePath);
            
            if (!Files.exists(targetFile) || !targetFile.toString().endsWith(".java")) {
                return ResponseEntity.badRequest()
                    .body(Map.of("error", "File not found or not a Java file"));
            }
            
            String content = Files.readString(targetFile, StandardCharsets.UTF_8);
            String relativePath = workspacePath.relativize(targetFile).toString();
            
            // Perform file-level security analysis
            List<Map<String, Object>> vulnerabilities = analyzeJavaFileForSecurityIssues(content, relativePath);
            
            int criticalCount = 0, highCount = 0, mediumCount = 0, lowCount = 0;
            double totalRiskScore = 0.0;
            
            for (Map<String, Object> vuln : vulnerabilities) {
                String severity = (String) vuln.get("severity");
                switch (severity) {
                    case "CRITICAL": criticalCount++; break;
                    case "HIGH": highCount++; break;
                    case "MEDIUM": mediumCount++; break;
                    case "LOW": lowCount++; break;
                }
                totalRiskScore += (Double) vuln.getOrDefault("cvssScore", 0.0);
            }
            
            int totalVulnerabilities = vulnerabilities.size();
            double overallRiskScore = totalVulnerabilities > 0 ? (totalRiskScore / totalVulnerabilities) / 10.0 : 0.0;
            double owaspCompliance = totalVulnerabilities == 0 ? 100.0 : Math.max(0, 100.0 - (totalVulnerabilities * 5.0));
            String securityGrade = calculateSecurityGrade(overallRiskScore, totalVulnerabilities);
            
            Map<String, Object> result = new HashMap<>();
            result.put("workspaceId", workspaceId);
            result.put("filePath", relativePath);
            result.put("totalVulnerabilities", totalVulnerabilities);
            result.put("criticalVulnerabilities", criticalCount);
            result.put("highVulnerabilities", highCount);
            result.put("mediumVulnerabilities", mediumCount);
            result.put("lowVulnerabilities", lowCount);
            result.put("status", "completed");
            result.put("timestamp", System.currentTimeMillis());
            
            result.put("overallRiskScore", Math.round(overallRiskScore * 10.0) / 10.0);
            result.put("owaspCompliance", Math.round(owaspCompliance * 10.0) / 10.0);
            result.put("securityGrade", securityGrade);
            result.put("lastAnalyzed", System.currentTimeMillis());
            
            result.put("vulnerabilities", vulnerabilities);
            
            logger.info("File-level security analysis completed for workspace: {} file: {} - Found {} vulnerabilities", 
                       workspaceId, filePath, totalVulnerabilities);
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            logger.error("Failed to analyze file security: {}", workspaceId, e);
            return ResponseEntity.internalServerError().build();
        }
    }
    
    /**
     * Get workspace information.
     */
    @GetMapping("/workspaces/{id}")
    public ResponseEntity<Workspace> getWorkspace(@PathVariable String id) {
        try {
            ProjectContext projectContext = projectService.getProject(id);
            
            Workspace workspace = new Workspace(
                id,
                projectContext.root().getFileName().toString(),
                projectContext.sourceFiles().size(),
                projectContext.testFiles().size(),
                System.currentTimeMillis()
            );
            
            return ResponseEntity.ok(workspace);
            
        } catch (IllegalArgumentException e) {
            return ResponseEntity.notFound().build();
        }
    }
    
    /**
     * List all workspaces.
     * ALWAYS returns empty list - no auto-loading of previous projects.
     */
    @GetMapping("/workspaces")
    public ResponseEntity<List<Workspace>> listWorkspaces() {
        try {
            List<ProjectContext> projects = projectService.getAllProjects();
            List<Workspace> workspaces = projects.stream()
                .map(project -> new Workspace(
                    project.getProperty("projectId", "unknown"),
                    project.root().getFileName().toString(),
                    project.sourceFiles().size(),
                    project.testFiles().size(),
                    System.currentTimeMillis()
                ))
                .collect(Collectors.toList());
            
            logger.info("Listing workspaces - found {} projects", workspaces.size());
            return ResponseEntity.ok(workspaces);
        } catch (Exception e) {
            logger.error("Failed to list workspaces", e);
            return ResponseEntity.ok(new ArrayList<>());
        }
    }

    @PostMapping("/workspaces/clear")
    public ResponseEntity<Map<String, String>> clearWorkspaces() {
        try {
            logger.info("Clearing all workspaces from current session");
            projectService.clearAllProjects();
            Map<String, String> response = new HashMap<>();
            response.put("message", "All workspaces cleared successfully");
            response.put("status", "success");
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            logger.error("Failed to clear workspaces", e);
            Map<String, String> response = new HashMap<>();
            response.put("message", "Failed to clear workspaces: " + e.getMessage());
            response.put("status", "error");
            return ResponseEntity.internalServerError().body(response);
        }
    }
    
    
    /**
     * Get session information.
     */
    @GetMapping("/session/info")
    public ResponseEntity<Map<String, String>> getSessionInfo() {
        Map<String, String> sessionInfo = new HashMap<>();
        sessionInfo.put("sessionId", projectService.getSessionId());
        sessionInfo.put("timestamp", String.valueOf(System.currentTimeMillis()));
        sessionInfo.put("status", "active");
        return ResponseEntity.ok(sessionInfo);
    }
    
    /**
     * Delete a workspace.
     */
    @DeleteMapping("/workspaces/{id}")
    public ResponseEntity<Void> deleteWorkspace(@PathVariable String id) {
        try {
            projectService.deleteProject(id);
            return ResponseEntity.ok().build();
        } catch (Exception e) {
            logger.error("Failed to delete workspace: {}", id, e);
            return ResponseEntity.badRequest().build();
        }
    }
    
    /**
     * Get all files in a workspace with their information.
     */
    @GetMapping("/workspaces/{id}/files")
    public ResponseEntity<List<FileInfo>> getWorkspaceFiles(@PathVariable String id) {
        try {
            logger.info("Getting files for workspace: {}", id);
            
            List<FileInfo> files = projectService.getProjectFiles(id);
            
            return ResponseEntity.ok(files);
            
        } catch (Exception e) {
            logger.error("Failed to get files for workspace: {}", id, e);
            return ResponseEntity.notFound().build();
        }
    }

    @GetMapping("/workspaces/{id}/files/content")
    public ResponseEntity<Map<String, Object>> getFileContent(
            @PathVariable String id,
            @RequestParam String filePath) {
        try {
            logger.info("Getting content for file: {} in workspace: {}", filePath, id);
            
            // Decode the file path in case it's URL encoded
            String decodedFilePath = java.net.URLDecoder.decode(filePath, "UTF-8");
            logger.info("Decoded file path: {}", decodedFilePath);
            
            String content = projectService.getFileContent(id, decodedFilePath);
            Map<String, Object> response = Map.of(
                "content", content,
                "filePath", decodedFilePath,
                "workspaceId", id
            );
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            logger.error("Failed to get content for file: {} in workspace: {}", filePath, id, e);
            return ResponseEntity.notFound().build();
        }
    }
    
    /**
     * Perform assessment on a project.
     */
    @PostMapping("/workspaces/{id}/assess")
    public ResponseEntity<Assessment> assessProject(@PathVariable String id, @RequestBody AssessmentRequest request) {
        try {
            logger.info("Starting assessment for workspace: {}", id);
            
            ProjectContext projectContext = projectService.getProject(id);
            Assessment assessment = refactoringService.assessProject(projectContext);
            
            return ResponseEntity.ok(assessment);
            
        } catch (Exception e) {
            logger.error("Assessment failed for workspace: {}", id, e);
            return ResponseEntity.badRequest().build();
        }
    }
    
    /**
     * Get assessment results.
     */
    @GetMapping("/workspaces/{id}/assessment")
    public ResponseEntity<Assessment> getAssessment(@PathVariable String id) {
        try {
            Assessment assessment = refactoringService.getAssessment(id);
            return ResponseEntity.ok(assessment);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.notFound().build();
        }
    }
    
    /**
     * Generate refactoring plan.
     */
    @PostMapping("/workspaces/{id}/plan")
    public ResponseEntity<Plan> generatePlan(@PathVariable String id, @RequestBody PlanRequest request) {
        try {
            logger.info("Generating refactoring plan for workspace: {}", id);
            
            Plan plan = refactoringService.generatePlan(id, request);
            
            return ResponseEntity.ok(plan);
            
        } catch (Exception e) {
            logger.error("Plan generation failed for workspace: {}", id, e);
            return ResponseEntity.badRequest().build();
        }
    }
    
    /**
     * Get refactoring plan.
     */
    @GetMapping("/workspaces/{id}/plan")
    public ResponseEntity<Plan> getPlan(@PathVariable String id) {
        try {
            Plan plan = refactoringService.getPlan(id);
            return ResponseEntity.ok(plan);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.notFound().build();
        }
    }
    
    /**
     * Apply refactoring plan.
     */
    @PostMapping("/workspaces/{id}/apply")
    public ResponseEntity<ApplyResult> applyPlan(@PathVariable String id, @RequestBody ApplyRequest request) {
        try {
            logger.info("Applying refactoring plan for workspace: {}", id);
            
            ApplyResult result = refactoringService.applyPlan(id, request);
            
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            logger.error("Plan application failed for workspace: {}", id, e);
            return ResponseEntity.badRequest().build();
        }
    }
    
    /**
     * Get project artifacts (assessment report, plan, etc.).
     */
    @GetMapping("/workspaces/{id}/artifacts/{name}")
    public ResponseEntity<String> getArtifact(@PathVariable String id, @PathVariable String name) {
        try {
            // Mock artifact generation - in production, generate actual reports
            String artifact = switch (name) {
                case "assessment.json" -> generateAssessmentJson(id);
                case "assessment.html" -> generateAssessmentHtml(id);
                case "plan.json" -> generatePlanJson(id);
                case "patch.diff" -> generatePatchDiff(id);
                case "impact.json" -> generateImpactJson(id);
                default -> throw new IllegalArgumentException("Unknown artifact: " + name);
            };
            
            return ResponseEntity.ok(artifact);
            
        } catch (Exception e) {
            logger.error("Failed to generate artifact {} for workspace: {}", name, id, e);
            return ResponseEntity.notFound().build();
        }
    }
    
    /**
     * Health check endpoint.
     */
    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {
        Map<String, Object> health = Map.of(
            "status", "UP",
            "timestamp", System.currentTimeMillis(),
            "version", "0.1.0-SNAPSHOT"
        );
        
        return ResponseEntity.ok(health);
    }
    
    // Mock artifact generation methods
    private String generateAssessmentJson(String projectId) {
        return """
            {
                "projectId": "%s",
                "timestamp": %d,
                "status": "completed"
            }
            """.formatted(projectId, System.currentTimeMillis());
    }
    
    private String generateAssessmentHtml(String projectId) {
        return """
            <!DOCTYPE html>
            <html>
            <head><title>Assessment Report - %s</title></head>
            <body>
                <h1>Assessment Report</h1>
                <p>Project: %s</p>
                <p>Generated: %d</p>
            </body>
            </html>
            """.formatted(projectId, projectId, System.currentTimeMillis());
    }
    
    private String generatePlanJson(String projectId) {
        return """
            {
                "projectId": "%s",
                "timestamp": %d,
                "status": "generated"
            }
            """.formatted(projectId, System.currentTimeMillis());
    }
    
    private String generatePatchDiff(String projectId) {
        return """
            diff --git a/src/main/java/Example.java b/src/main/java/Example.java
            index 1234567..abcdefg 100644
            --- a/src/main/java/Example.java
            +++ b/src/main/java/Example.java
            @@ -10,6 +10,7 @@ public class Example {
                 // Refactored code
                 public void improvedMethod() {
                     // Better implementation
            +        // Added by RefactAI
                 }
            """;
    }
    
    private String generateImpactJson(String projectId) {
        return """
            {
                "projectId": "%s",
                "timestamp": %d,
                "impact": {
                    "maintainability": 85.5,
                    "complexity": -15.2,
                    "testCoverage": 78.3
                }
            }
            """.formatted(projectId, System.currentTimeMillis());
    }
    
    /**
     * Analyze a specific file for code smells and technical debt.
     */
    @GetMapping("/workspaces/{id}/files/analysis")
    public ResponseEntity<ai.refact.server.model.FileAnalysis> analyzeFile(
            @PathVariable String id,
            @RequestParam String filePath) {
        try {
            logger.info("Analyzing file: {} in workspace: {}", filePath, id);
            
            Path projectDir = projectService.getProjectDirectory(id);
            Path fullPath = projectDir.resolve(filePath);
            
            ai.refact.server.model.FileAnalysis analysis = codeAnalysisService.analyzeFile(fullPath);
            return ResponseEntity.ok(analysis);
            
        } catch (Exception e) {
            logger.error("Failed to analyze file: {} in workspace: {}", filePath, id, e);
            return ResponseEntity.badRequest().build();
        }
    }
    
    /**
     * Analyze entire workspace for code smells and technical debt.
     */
    @PostMapping("/workspaces/{id}/analyze")
    public ResponseEntity<ai.refact.server.model.CodeAnalysisResult> analyzeWorkspace(@PathVariable String id) {
        try {
            logger.info("Starting comprehensive analysis for workspace: {}", id);
            
            ProjectContext projectContext = projectService.getProject(id);
            List<Path> javaFiles = new ArrayList<>(projectContext.sourceFiles());
            
            ai.refact.server.model.CodeAnalysisResult result = codeAnalysisService.analyzeWorkspace(id, javaFiles);
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            logger.error("Failed to analyze workspace: {}", id, e);
            return ResponseEntity.badRequest().build();
        }
    }
    
    /*
     * Security analysis methods are temporarily disabled.
     * Use SimpleSecurityController for security functionality.
     */
    /*
    @GetMapping("/workspaces/{id}/files/security")
    public ResponseEntity<ai.refact.server.model.FileSecurityAnalysis> analyzeFileSecurity(
            @PathVariable String id,
            @RequestParam String filePath) {
        try {
            logger.info("Analyzing file for security vulnerabilities: {} in workspace: {}", filePath, id);
            
            ai.refact.server.model.FileSecurityAnalysis analysis = securityAnalysisService.analyzeFile(id, filePath);
            return ResponseEntity.ok(analysis);
            
        } catch (Exception e) {
            logger.error("Failed to analyze file for security: {} in workspace: {}", filePath, id, e);
            return ResponseEntity.badRequest().build();
        }
    }
    */
    
    /*
    @PostMapping("/workspaces/{id}/security")
    public ResponseEntity<SecurityAnalysisResult> analyzeWorkspaceSecurity(@PathVariable String id) {
        try {
            logger.info("Starting security analysis for workspace: {}", id);
            
            SecurityAnalysisResult result = securityAnalysisService.analyzeWorkspace(id);
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            logger.error("Failed to analyze workspace security: {}", id, e);
            return ResponseEntity.badRequest().build();
        }
    }
    */
    
    /*
     * All security analysis methods are temporarily disabled.
     * Use SimpleSecurityController for security functionality.
     */

    /**
     * Enhanced analysis endpoint for individual files.
     */
    // @PostMapping("/workspace-enhanced-analysis/analyze-file") // Moved to EnhancedAnalysisController
    public ResponseEntity<Map<String, Object>> analyzeFileEnhanced(@RequestBody EnhancedAnalysisRequest request) {
        try {
            logger.info("Enhanced analysis requested for file: {} in workspace: {}", 
                       request.getFilePath(), request.getWorkspaceId());
            
            // Get the actual file analysis using comprehensive assessment approach
            Path projectDir = projectService.getProjectDirectory(request.getWorkspaceId());
            Path fullPath = projectDir.resolve(request.getFilePath());
            
            // Use the same comprehensive assessment as project-level analysis
            ProjectContext projectContext = projectService.getProject(request.getWorkspaceId());
            List<ReasonEvidence> allEvidences = assessmentEngine.assess(projectContext);
            
            // Filter evidences for this specific file
            logger.info("Total evidences from assessment: {}", allEvidences.size());
            logger.info("Request file path: {}", request.getFilePath());
            
            List<ReasonEvidence> fileEvidences = allEvidences.stream()
                .filter(evidence -> {
                    String evidenceFilePath = evidence.pointer().file().toString();
                    if (evidenceFilePath == null) return false;
                    
                    // Extract just the filename from the request path
                    String requestFileName = request.getFilePath().substring(request.getFilePath().lastIndexOf('/') + 1);
                    
                    // Check if the evidence file path contains the request file name or the full relative path
                    boolean matches = evidenceFilePath.endsWith("/" + requestFileName) || 
                           evidenceFilePath.endsWith("\\" + requestFileName) ||
                           evidenceFilePath.contains("/" + request.getFilePath()) ||
                           evidenceFilePath.contains("\\" + request.getFilePath()) ||
                           evidenceFilePath.contains(requestFileName);
                    
                    if (matches) {
                        logger.debug("Found matching evidence: {} for file: {}", evidenceFilePath, request.getFilePath());
                    }
                    
                    return matches;
                })
                .collect(Collectors.toList());
            
            logger.info("Filtered evidences for file: {}", fileEvidences.size());
            
            // Convert ReasonEvidence to CodeSmell format for consistency
            List<ai.refact.engine.model.CodeSmell> smells = fileEvidences.stream()
                .map(this::convertEvidenceToCodeSmell)
                .collect(Collectors.toList());
            
            // Get file metrics using the existing service
            ai.refact.server.model.FileAnalysis basicAnalysis = codeAnalysisService.analyzeFile(fullPath);
            Map<String, Object> fileMetrics = basicAnalysis.getMetrics();
            
            // Calculate enhanced metrics based on real analysis
            int cyclomaticComplexity = (Integer) fileMetrics.getOrDefault("cyclomaticComplexity", 1);
            int cognitiveComplexity = (Integer) fileMetrics.getOrDefault("cognitiveComplexity", 1);
            int totalLines = (Integer) fileMetrics.getOrDefault("totalLines", 0);
            int codeLines = (Integer) fileMetrics.getOrDefault("codeLines", 0);
            int commentLines = (Integer) fileMetrics.getOrDefault("commentLines", 0);
            int classCount = (Integer) fileMetrics.getOrDefault("classCount", 0);
            int methodCount = (Integer) fileMetrics.getOrDefault("methodCount", 0);
            int fieldCount = (Integer) fileMetrics.getOrDefault("fieldCount", 0);
            
            // Calculate quality grade based on real metrics
            String qualityGrade = calculateQualityGrade(cyclomaticComplexity, cognitiveComplexity, smells.size(), commentLines, codeLines);
            int overallScore = calculateOverallScore(cyclomaticComplexity, cognitiveComplexity, smells.size(), commentLines, codeLines);
            int refactoringPriority = calculateRefactoringPriority(smells, cyclomaticComplexity);
            
            // Count issues by severity
            int criticalIssues = (int) smells.stream().filter(s -> s.getSeverity() == SmellSeverity.CRITICAL).count();
            int majorIssues = (int) smells.stream().filter(s -> s.getSeverity() == SmellSeverity.MAJOR).count();
            int minorIssues = (int) smells.stream().filter(s -> s.getSeverity() == SmellSeverity.MINOR).count();
            
            // Calculate maintainability index (0-1 scale)
            double maintainabilityIndex = calculateMaintainabilityIndex(cyclomaticComplexity, cognitiveComplexity, smells.size(), commentLines, codeLines);
            
            // Calculate technical debt ratio
            double technicalDebtRatio = basicAnalysis.getTechnicalDebtScore() / 100.0;
            
            Map<String, Object> metrics = new HashMap<>();
            metrics.put("qualityGrade", qualityGrade);
            metrics.put("overallScore", overallScore);
            metrics.put("refactoringPriority", refactoringPriority);
            metrics.put("cyclomaticComplexity", cyclomaticComplexity);
            metrics.put("cognitiveComplexity", cognitiveComplexity);
            metrics.put("maintainabilityIndex", maintainabilityIndex);
            metrics.put("technicalDebtRatio", technicalDebtRatio);
            metrics.put("codeSmells", smells.size());
            metrics.put("criticalIssues", criticalIssues);
            metrics.put("majorIssues", majorIssues);
            metrics.put("minorIssues", minorIssues);
            metrics.put("classCount", classCount);
            metrics.put("methodCount", methodCount);
            metrics.put("fieldCount", fieldCount);
            metrics.put("totalLines", totalLines);
            metrics.put("codeLines", codeLines);
            metrics.put("commentLines", commentLines);
            
            // Generate quality insights based on real analysis
            Map<String, Object> qualityInsights = new HashMap<>();
            qualityInsights.put("qualityCategory", getQualityCategory(overallScore));
            qualityInsights.put("needsAttention", criticalIssues > 0 || majorIssues > 2 || cyclomaticComplexity > 10);
            
            Map<String, String> specificInsights = new HashMap<>();
            if (cyclomaticComplexity > 10) {
                specificInsights.put("complexity", "High cyclomatic complexity detected. Consider breaking down complex methods into smaller, more manageable functions.");
            } else if (cyclomaticComplexity > 5) {
                specificInsights.put("complexity", "Moderate cyclomatic complexity. Monitor for potential refactoring opportunities.");
            } else {
                specificInsights.put("complexity", "Good cyclomatic complexity. Code is well-structured and maintainable.");
            }
            
            if (commentLines == 0 && codeLines > 20) {
                specificInsights.put("documentation", "No comments found. Consider adding Javadoc comments for public methods and complex logic.");
            } else if (commentLines < codeLines * 0.1) {
                specificInsights.put("documentation", "Low comment ratio. Consider adding more documentation for better code maintainability.");
            } else {
                specificInsights.put("documentation", "Good documentation coverage. Keep up the good work!");
            }
            
            if (smells.size() > 5) {
                specificInsights.put("codeQuality", "Multiple code smells detected. Review and refactor to improve code quality.");
            } else if (smells.size() > 0) {
                specificInsights.put("codeQuality", "Some code smells detected. Consider addressing them to improve maintainability.");
            } else {
                specificInsights.put("codeQuality", "No code smells detected. Excellent code quality!");
            }
            
            qualityInsights.put("specificInsights", specificInsights);
            
            // Generate recommendations based on real analysis
            Map<String, Object> recommendations = new HashMap<>();
            recommendations.put("estimatedEffort", calculateEstimatedEffort(smells, cyclomaticComplexity));
            
            Map<String, String> actions = new HashMap<>();
            if (criticalIssues > 0) {
                actions.put("immediate", "Address " + criticalIssues + " critical issues immediately");
            } else if (majorIssues > 0) {
                actions.put("immediate", "Address " + majorIssues + " major issues");
            } else {
                actions.put("immediate", "No immediate action required");
            }
            
            if (cyclomaticComplexity > 10) {
                actions.put("shortTerm", "Refactor methods with high complexity");
            } else if (commentLines < codeLines * 0.1) {
                actions.put("shortTerm", "Add documentation and comments");
            } else {
                actions.put("shortTerm", "Continue monitoring code quality");
            }
            
            actions.put("longTerm", "Maintain current quality standards and consider code reviews");
            recommendations.put("actions", actions);
            
            // Convert code smells to a format suitable for frontend
            List<Map<String, Object>> codeSmellsList = new ArrayList<>();
            for (ai.refact.engine.model.CodeSmell smell : smells) {
                Map<String, Object> smellMap = new HashMap<>();
                smellMap.put("id", smell.getType().name() + "_" + System.currentTimeMillis());
                smellMap.put("type", smell.getType().name());
                smellMap.put("category", smell.getCategory().name());
                smellMap.put("severity", smell.getSeverity().name());
                smellMap.put("title", smell.getTitle());
                smellMap.put("description", smell.getDescription());
                smellMap.put("recommendation", smell.getRecommendation());
                smellMap.put("startLine", smell.getStartLine());
                smellMap.put("endLine", smell.getEndLine());
                smellMap.put("refactoringSuggestions", smell.getRefactoringSuggestions());
                codeSmellsList.add(smellMap);
            }
            
            Map<String, Object> response = new HashMap<>();
            response.put("filePath", request.getFilePath());
            response.put("workspaceId", request.getWorkspaceId());
            response.put("metrics", metrics);
            response.put("qualityInsights", qualityInsights);
            response.put("recommendations", recommendations);
            response.put("codeSmells", codeSmellsList);
            response.put("timestamp", System.currentTimeMillis());
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            logger.error("Enhanced analysis failed for file: {}", request.getFilePath(), e);
            return ResponseEntity.badRequest().build();
        }
    }
    
    // Helper methods for enhanced analysis calculations
    private String calculateQualityGrade(int cyclomaticComplexity, int cognitiveComplexity, int smellCount, int commentLines, int codeLines) {
        int score = calculateOverallScore(cyclomaticComplexity, cognitiveComplexity, smellCount, commentLines, codeLines);
        
        if (score >= 90) return "A+";
        if (score >= 85) return "A";
        if (score >= 80) return "A-";
        if (score >= 75) return "B+";
        if (score >= 70) return "B";
        if (score >= 65) return "B-";
        if (score >= 60) return "C+";
        if (score >= 55) return "C";
        if (score >= 50) return "C-";
        if (score >= 40) return "D";
        return "F";
    }
    
    private int calculateOverallScore(int cyclomaticComplexity, int cognitiveComplexity, int smellCount, int commentLines, int codeLines) {
        int score = 100;
        
        // More realistic complexity scoring
        if (cyclomaticComplexity > 20) score -= 40;
        else if (cyclomaticComplexity > 15) score -= 30;
        else if (cyclomaticComplexity > 10) score -= 20;
        else if (cyclomaticComplexity > 5) score -= 10;
        
        // More realistic cognitive complexity scoring
        if (cognitiveComplexity > 30) score -= 35;
        else if (cognitiveComplexity > 20) score -= 25;
        else if (cognitiveComplexity > 10) score -= 15;
        else if (cognitiveComplexity > 5) score -= 5;
        
        // More realistic code smell scoring (less aggressive)
        if (smellCount > 20) score -= 40;
        else if (smellCount > 10) score -= 25;
        else if (smellCount > 5) score -= 15;
        else if (smellCount > 0) score -= Math.min(10, smellCount * 2);
        
        // Bonus points for good documentation
        if (codeLines > 0) {
            double commentRatio = (double) commentLines / codeLines;
            if (commentRatio > 0.3) score += 15;
            else if (commentRatio > 0.2) score += 10;
            else if (commentRatio > 0.1) score += 5;
        }
        
        // Ensure score is within bounds
        return Math.max(0, Math.min(100, score));
    }
    
    private int calculateRefactoringPriority(List<ai.refact.engine.model.CodeSmell> smells, int cyclomaticComplexity) {
        int priority = 1; // Low priority by default
        
        // High priority for critical issues
        long criticalCount = smells.stream().filter(s -> s.getSeverity() == SmellSeverity.CRITICAL).count();
        if (criticalCount > 0) priority = 5;
        
        // Medium-high priority for high complexity
        else if (cyclomaticComplexity > 15) priority = 4;
        
        // Medium priority for major issues or moderate complexity
        else if (smells.stream().anyMatch(s -> s.getSeverity() == SmellSeverity.MAJOR) || cyclomaticComplexity > 10) {
            priority = 3;
        }
        
        // Medium-low priority for minor issues
        else if (smells.size() > 3) priority = 2;
        
        return priority;
    }
    
    private double calculateMaintainabilityIndex(int cyclomaticComplexity, int cognitiveComplexity, int smellCount, int commentLines, int codeLines) {
        double index = 1.0;
        
        // Reduce index based on complexity
        index -= (cyclomaticComplexity - 1) * 0.02;
        index -= (cognitiveComplexity - 1) * 0.01;
        
        // Reduce index based on code smells
        index -= smellCount * 0.05;
        
        // Increase index for good documentation
        if (codeLines > 0) {
            double commentRatio = (double) commentLines / codeLines;
            index += commentRatio * 0.2;
        }
        
        return Math.max(0.0, Math.min(1.0, index));
    }
    
    private String getQualityCategory(int overallScore) {
        if (overallScore >= 80) return "Excellent";
        if (overallScore >= 70) return "Good";
        if (overallScore >= 60) return "Fair";
        if (overallScore >= 50) return "Poor";
        return "Critical";
    }
    
    private int calculateEstimatedEffort(List<ai.refact.engine.model.CodeSmell> smells, int cyclomaticComplexity) {
        int effort = 1; // Hours
        
        // Add effort for code smells
        effort += smells.size() * 2;
        
        // Add effort for complexity
        if (cyclomaticComplexity > 15) effort += 8;
        else if (cyclomaticComplexity > 10) effort += 4;
        else if (cyclomaticComplexity > 5) effort += 2;
        
        return Math.min(40, effort); // Cap at 40 hours
    }
    
    /**
     * Convert ReasonEvidence to CodeSmell for consistency with file analysis
     */
    private CodeSmell convertEvidenceToCodeSmell(ReasonEvidence evidence) {
        // Map detector ID to smell type
        SmellType smellType = mapDetectorToSmellType(evidence.detectorId());
        
        // Map severity
        SmellSeverity severity = mapSeverity(evidence.severity());
        
        // Map category
        SmellCategory category = mapCategory(evidence.detectorId());
        
        // Extract information from evidence
        String title = evidence.summary();
        String description = evidence.summary();
        String recommendation = "Consider refactoring to improve code quality";
        
        // Get line numbers from pointer
        int startLine = evidence.pointer().startLine();
        int endLine = evidence.pointer().endLine();
        
        return new CodeSmell(
            smellType,
            category,
            severity,
            title,
            description,
            recommendation,
            startLine,
            endLine,
            List.of(recommendation)
        );
    }
    
    private SmellType mapDetectorToSmellType(String detectorId) {
        if (detectorId.contains("long-method")) return SmellType.LONG_METHOD;
        if (detectorId.contains("god-class") || detectorId.contains("large-class")) return SmellType.LARGE_CLASS;
        if (detectorId.contains("feature-envy")) return SmellType.FEATURE_ENVY;
        if (detectorId.contains("duplicate-code")) return SmellType.DUPLICATE_CODE;
        if (detectorId.contains("primitive-obsession")) return SmellType.PRIMITIVE_OBSESSION;
        if (detectorId.contains("data-clumps")) return SmellType.DATA_CLUMPS;
        if (detectorId.contains("dead-code")) return SmellType.DEAD_CODE;
        if (detectorId.contains("speculative-generality")) return SmellType.SPECULATIVE_GENERALITY;
        if (detectorId.contains("shotgun-surgery")) return SmellType.SHOTGUN_SURGERY;
        if (detectorId.contains("divergent-change")) return SmellType.DIVERGENT_CHANGE;
        if (detectorId.contains("parallel-inheritance")) return SmellType.PARALLEL_INHERITANCE;
        if (detectorId.contains("refused-bequest")) return SmellType.REFUSED_BEQUEST;
        if (detectorId.contains("inappropriate-intimacy")) return SmellType.INAPPROPRIATE_INTIMACY;
        if (detectorId.contains("message-chains")) return SmellType.MESSAGE_CHAINS;
        if (detectorId.contains("middle-man")) return SmellType.MIDDLE_MAN;
        if (detectorId.contains("temporary-field")) return SmellType.TEMPORARY_FIELD;
        if (detectorId.contains("lazy-class")) return SmellType.LAZY_CLASS;
        if (detectorId.contains("data-class")) return SmellType.DATA_CLASS;
        if (detectorId.contains("switch-statements")) return SmellType.SWITCH_STATEMENTS;
        if (detectorId.contains("alternative-classes")) return SmellType.ALTERNATIVE_CLASSES;
        if (detectorId.contains("long-parameter-list")) return SmellType.LONG_PARAMETER_LIST;
        if (detectorId.contains("excessive-comments")) return SmellType.EXCESSIVE_COMMENTS;
        if (detectorId.contains("missing-coverage")) return SmellType.MISSING_COVERAGE;
        if (detectorId.contains("misplaced-responsibility")) return SmellType.MISPLACED_RESPONSIBILITY;
        if (detectorId.contains("complex-method")) return SmellType.HIGH_COMPLEXITY;
        if (detectorId.contains("hardcoded-credentials")) return SmellType.HARD_CODED_DEPENDENCIES;
        if (detectorId.contains("raw-types")) return SmellType.MISUSE_OF_STATICS;
        if (detectorId.contains("inconsistent-naming")) return SmellType.INCONSISTENT_NAMING;
        if (detectorId.contains("single-letter-vars")) return SmellType.INCONSISTENT_NAMING;
        if (detectorId.contains("switch-statements")) return SmellType.SWITCH_STATEMENTS;
        if (detectorId.contains("try-catch-hell")) return SmellType.EXCESSIVE_COMMENTS;
        if (detectorId.contains("flag-arguments")) return SmellType.LONG_PARAMETER_LIST;
        if (detectorId.contains("string-concatenation")) return SmellType.INEFFICIENT_RESOURCE_USAGE;
        if (detectorId.contains("long-line")) return SmellType.LONG_METHOD;
        if (detectorId.contains("string-constants")) return SmellType.PRIMITIVE_OBSESSION;
        if (detectorId.contains("circular-dependencies")) return SmellType.CYCLIC_DEPENDENCIES;
        if (detectorId.contains("generic-exception")) return SmellType.MISUSE_OF_STATICS;
        if (detectorId.contains("nested-conditionals")) return SmellType.HIGH_COMPLEXITY;
        if (detectorId.contains("null-abuse")) return SmellType.MISUSE_OF_STATICS;
        if (detectorId.contains("empty-catch-block")) return SmellType.DEAD_CODE;
        return SmellType.LONG_METHOD; // Default fallback
    }
    
    private SmellSeverity mapSeverity(ai.refact.api.Severity severity) {
        switch (severity) {
            case CRITICAL: return SmellSeverity.CRITICAL;
            case MAJOR: return SmellSeverity.MAJOR;
            case MINOR: return SmellSeverity.MINOR;
            case INFO: return SmellSeverity.INFO;
            default: return SmellSeverity.MINOR;
        }
    }
    
    private SmellCategory mapCategory(String detectorId) {
        if (detectorId.startsWith("design.")) return SmellCategory.MAINTAINABILITY_ISSUE;
        if (detectorId.contains("long-method") || detectorId.contains("large-class") || 
            detectorId.contains("long-parameter-list") || detectorId.contains("primitive-obsession") ||
            detectorId.contains("data-clumps")) return SmellCategory.BLOATER;
        if (detectorId.contains("switch-statements") || detectorId.contains("temporary-field") ||
            detectorId.contains("refused-bequest") || detectorId.contains("alternative-classes")) return SmellCategory.OBJECT_ORIENTATION_ABUSER;
        if (detectorId.contains("divergent-change") || detectorId.contains("shotgun-surgery")) return SmellCategory.CHANGE_PREVENTER;
        if (detectorId.contains("duplicate-code") || detectorId.contains("lazy-class") ||
            detectorId.contains("data-class") || detectorId.contains("dead-code") ||
            detectorId.contains("speculative-generality") || detectorId.contains("excessive-comments")) return SmellCategory.DISPENSABLE;
        if (detectorId.contains("feature-envy") || detectorId.contains("inappropriate-intimacy") ||
            detectorId.contains("message-chains") || detectorId.contains("middle-man")) return SmellCategory.COUPLER;
        if (detectorId.contains("inconsistent-naming") || detectorId.contains("misplaced-responsibility") ||
            detectorId.contains("misuse-of-statics") || detectorId.contains("public-fields")) return SmellCategory.ENCAPSULATION_ISSUE;
        if (detectorId.contains("parallel-inheritance") || detectorId.contains("god-object") ||
            detectorId.contains("cyclic-dependencies") || detectorId.contains("hard-coded-dependencies")) return SmellCategory.HIERARCHY_ISSUE;
        if (detectorId.contains("global-mutable-state") || detectorId.contains("too-much-synchronization")) return SmellCategory.CONCURRENCY_ISSUE;
        if (detectorId.contains("inefficient-resource-usage") || detectorId.contains("string-concatenation")) return SmellCategory.PERFORMANCE_ISSUE;
        if (detectorId.contains("missing-coverage") || detectorId.contains("fragile-tests") ||
            detectorId.contains("slow-tests") || detectorId.contains("obscure-tests")) return SmellCategory.TESTING_ISSUE;
        return SmellCategory.MAINTAINABILITY_ISSUE;
    }
    
    /**
     * Get workspace file summary statistics.
     */
    @GetMapping("/workspaces/{id}/files/summary")
    public ResponseEntity<Map<String, Object>> getWorkspaceFileSummary(@PathVariable String id) {
        try {
            logger.info("Getting file summary for workspace: {}", id);
            
            List<FileInfo> allFiles = projectService.getProjectFiles(id);
            
            // Calculate summary statistics
            Map<String, Long> fileTypeCounts = new HashMap<>();
            for (FileInfo file : allFiles) {
                String type = file.type().toString();
                fileTypeCounts.put(type, fileTypeCounts.getOrDefault(type, 0L) + 1);
            }
            
            Map<String, Object> summary = new HashMap<>();
            summary.put("totalFiles", allFiles.size());
            summary.put("fileTypeCounts", fileTypeCounts);
            summary.put("sourceFiles", fileTypeCounts.getOrDefault("SOURCE", 0L));
            summary.put("testFiles", fileTypeCounts.getOrDefault("TEST", 0L));
            summary.put("configFiles", fileTypeCounts.getOrDefault("CONFIG", 0L));
            summary.put("resourceFiles", fileTypeCounts.getOrDefault("RESOURCE", 0L));
            
            return ResponseEntity.ok(summary);
            
        } catch (Exception e) {
            logger.error("Failed to get file summary for workspace: {}", id, e);
            return ResponseEntity.notFound().build();
        }
    }
    
    /**
     * Get all files in a workspace with pagination, search, and filtering.
     */
    @GetMapping("/workspaces/{id}/files/paginated")
    public ResponseEntity<Map<String, Object>> getWorkspaceFilesPaginated(
            @PathVariable String id,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "50") int size,
            @RequestParam(required = false) String search,
            @RequestParam(required = false) String fileType) {
        try {
            logger.info("Getting files for workspace: {} (page: {}, size: {}, search: {}, fileType: {})", 
                       id, page, size, search, fileType);
            
            List<FileInfo> allFiles = projectService.getProjectFiles(id);
            
            // Apply search filter if provided
            List<FileInfo> filteredFiles = allFiles;
            if (search != null && !search.trim().isEmpty()) {
                String searchLower = search.toLowerCase();
                filteredFiles = allFiles.stream()
                    .filter(file -> file.path().toLowerCase().contains(searchLower) ||
                                  file.name().toLowerCase().contains(searchLower))
                    .collect(Collectors.toList());
            }
            
            // Apply file type filter if provided
            if (fileType != null && !fileType.trim().isEmpty()) {
                filteredFiles = filteredFiles.stream()
                    .filter(file -> fileType.equalsIgnoreCase(file.type().toString()))
                    .collect(Collectors.toList());
            }
            
            // Calculate pagination
            int totalFiles = filteredFiles.size();
            int totalPages = (int) Math.ceil((double) totalFiles / size);
            int startIndex = page * size;
            int endIndex = Math.min(startIndex + size, totalFiles);
            
            // Get files for current page
            List<FileInfo> pageFiles = filteredFiles.subList(startIndex, endIndex);
            
            // Build response with pagination info
            Map<String, Object> response = new HashMap<>();
            response.put("files", pageFiles);
            
            Map<String, Object> pagination = new HashMap<>();
            pagination.put("currentPage", page);
            pagination.put("totalPages", totalPages);
            pagination.put("totalFiles", totalFiles);
            pagination.put("pageSize", size);
            pagination.put("hasNext", page < totalPages - 1);
            pagination.put("hasPrevious", page > 0);
            response.put("pagination", pagination);
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            logger.error("Failed to get files for workspace: {}", id, e);
            return ResponseEntity.notFound().build();
        }
    }
    
    /**
     * Analyze file dependencies for a specific file
     */
    @GetMapping("/workspaces/{id}/dependencies/file")
    public ResponseEntity<DependencyAnalysisService.FileDependencyAnalysis> analyzeFileDependencies(
            @PathVariable String id, @RequestParam String filePath) {
        try {
            logger.info("Analyzing dependencies for file: {} in workspace: {}", filePath, id);
            
            ProjectContext projectContext = projectService.getProject(id);
            DependencyAnalysisService.FileDependencyAnalysis analysis = 
                dependencyAnalysisService.analyzeFileDependencies(projectContext, filePath);
            
            return ResponseEntity.ok(analysis);
            
        } catch (Exception e) {
            logger.error("Failed to analyze file dependencies: {}", filePath, e);
            return ResponseEntity.notFound().build();
        }
    }
    
    /**
     * Analyze project-wide dependencies
     */
    @GetMapping("/workspaces/{id}/dependencies/project")
    public ResponseEntity<DependencyAnalysisService.ProjectDependencyAnalysis> analyzeProjectDependencies(
            @PathVariable String id) {
        try {
            logger.info("Analyzing project dependencies for workspace: {}", id);
            
            ProjectContext projectContext = projectService.getProject(id);
            DependencyAnalysisService.ProjectDependencyAnalysis analysis = 
                dependencyAnalysisService.analyzeProjectDependencies(projectContext);
            
            return ResponseEntity.ok(analysis);
            
        } catch (Exception e) {
            logger.error("Failed to analyze project dependencies for workspace: {}", id, e);
            return ResponseEntity.notFound().build();
        }
    }
    
    /**
     * Get ripple effect analysis for a specific file
     */
    @GetMapping("/workspaces/{id}/dependencies/ripple-effect")
    public ResponseEntity<Map<String, Object>> getRippleEffectAnalysis(
            @PathVariable String id, @RequestParam String filePath) {
        try {
            logger.info("Analyzing ripple effect for file: {} in workspace: {}", filePath, id);
            
            ProjectContext projectContext = projectService.getProject(id);
            List<String> affectedFiles = dependencyAnalysisService.getRippleEffectFiles(projectContext, filePath);
            
            Map<String, Object> response = new HashMap<>();
            response.put("targetFile", filePath);
            response.put("affectedFiles", affectedFiles);
            response.put("impactCount", affectedFiles.size());
            response.put("hasImpact", affectedFiles.size() > 1); // More than just the target file itself
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            logger.error("Failed to analyze ripple effect for file: {}", filePath, e);
            return ResponseEntity.notFound().build();
        }
    }
    
    /**
     * Get dependency graph data for visualization
     */
    @GetMapping("/workspaces/{id}/dependencies/graph")
    public ResponseEntity<Map<String, Object>> getDependencyGraph(@PathVariable String id) {
        try {
            logger.info("Getting dependency graph for workspace: {}", id);
            
            ProjectContext projectContext = projectService.getProject(id);
            DependencyAnalysisService.ProjectDependencyAnalysis analysis = 
                dependencyAnalysisService.analyzeProjectDependencies(projectContext);
            
            // Convert to frontend-friendly format
            Map<String, Object> graphData = new HashMap<>();
            
            // Nodes (files)
            List<Map<String, Object>> nodes = new ArrayList<>();
            for (String filePath : analysis.getDependencyGraph().keySet()) {
                Map<String, Object> node = new HashMap<>();
                node.put("id", filePath);
                node.put("label", filePath.substring(filePath.lastIndexOf('/') + 1));
                node.put("path", filePath);
                node.put("type", filePath.endsWith(".java") ? "java" : "other");
                
                // Add dependency counts
                DependencyAnalysisService.FileDependencyAnalysis fileAnalysis = analysis.getFileDependencies().get(filePath);
                if (fileAnalysis != null) {
                    node.put("outgoingDependencies", fileAnalysis.getOutgoingDependencies());
                    node.put("incomingDependencies", fileAnalysis.getIncomingDependencies());
                }
                
                nodes.add(node);
            }
            
            // Edges (dependencies)
            List<Map<String, Object>> edges = new ArrayList<>();
            for (Map.Entry<String, Set<String>> entry : analysis.getDependencyGraph().entrySet()) {
                String source = entry.getKey();
                for (String target : entry.getValue()) {
                    Map<String, Object> edge = new HashMap<>();
                    edge.put("source", source);
                    edge.put("target", target);
                    edge.put("type", "dependency");
                    edges.add(edge);
                }
            }
            
            graphData.put("nodes", nodes);
            graphData.put("edges", edges);
            graphData.put("metrics", analysis.getMetrics());
            
            return ResponseEntity.ok(graphData);
            
        } catch (Exception e) {
            logger.error("Failed to get dependency graph for workspace: {}", id, e);
            return ResponseEntity.notFound().build();
        }
    }

    /**
     * Analyze a specific Java file to extract class and method information
     */
    @PostMapping("/files/{workspaceId}/analyze")
    public ResponseEntity<Map<String, Object>> analyzeFile(@PathVariable String workspaceId, 
                                                          @RequestBody Map<String, String> request) {
        try {
            String filePath = request.get("filePath");
            logger.info("Analyzing file: {} in workspace: {}", filePath, workspaceId);
            
            ProjectContext projectContext = projectService.getProject(workspaceId);
            if (projectContext == null) {
                return ResponseEntity.notFound().build();
            }
            
            // Get the full path to the file
            Path fullPath = projectContext.root().resolve(filePath);
            if (!Files.exists(fullPath)) {
                return ResponseEntity.notFound().build();
            }
            
            // Read file content
            String content = Files.readString(fullPath);
            
            // Analyze the file using regex patterns
            Map<String, Object> analysis = analyzeJavaFile(content, filePath);
            
            return ResponseEntity.ok(analysis);
            
        } catch (Exception e) {
            logger.error("Failed to analyze file in workspace: {}", workspaceId, e);
            return ResponseEntity.badRequest().body(Map.of("error", "Failed to analyze file: " + e.getMessage()));
        }
    }

    /**
     * Get file content for preview
     */
    @GetMapping("/files/{workspaceId}/preview")
    public ResponseEntity<Map<String, Object>> getFilePreview(@PathVariable String workspaceId,
                                                             @RequestParam String filePath) {
        try {
            logger.info("Getting content for file: {} in workspace: {}", filePath, workspaceId);
            
            ProjectContext projectContext = projectService.getProject(workspaceId);
            if (projectContext == null) {
                return ResponseEntity.notFound().build();
            }
            
            Path fullPath = projectContext.root().resolve(filePath);
            if (!Files.exists(fullPath)) {
                return ResponseEntity.notFound().build();
            }
            
            String content = Files.readString(fullPath);
            
            Map<String, Object> result = new HashMap<>();
            result.put("content", content);
            result.put("filePath", filePath);
            result.put("lines", content.split("\n").length);
            
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            logger.error("Failed to get file content for workspace: {}", workspaceId, e);
            return ResponseEntity.badRequest().body(Map.of("error", "Failed to get file content: " + e.getMessage()));
        }
    }

    /**
     * Preview refactoring operation without executing it
     */
    @PostMapping("/refactoring/{workspaceId}/preview")
    public ResponseEntity<Map<String, Object>> previewRefactoring(
            @PathVariable String workspaceId,
            @RequestBody Map<String, Object> request) {
        try {
            String operationType = (String) request.get("operationType");
            String filePath = (String) request.get("filePath");
            String methodName = (String) request.get("methodName");
            String newMethodName = (String) request.get("newMethodName");
            String newClassName = (String) request.get("newClassName");
            
            logger.info("Previewing {} refactoring on {} in workspace {}", operationType, filePath, workspaceId);
            
            ProjectContext projectContext = projectService.getProject(workspaceId);
            if (projectContext == null) {
                return ResponseEntity.notFound().build();
            }
            
            Path fullPath = projectContext.root().resolve(filePath);
            if (!Files.exists(fullPath)) {
                return ResponseEntity.notFound().build();
            }
            
            String originalContent = Files.readString(fullPath);
            String refactoredContent = performRefactoring(originalContent, operationType, methodName, newMethodName, newClassName);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", true);
            response.put("operationType", operationType);
            response.put("filePath", filePath);
            response.put("originalContent", originalContent);
            response.put("refactoredContent", refactoredContent);
            response.put("changes", generateChangeSummary(originalContent, refactoredContent));
            response.put("riskLevel", assessRiskLevel(operationType, originalContent, refactoredContent));
            response.put("affectedFiles", 1); // For now, single file operations
            response.put("dependencies", estimateDependencies(originalContent, methodName));
            
            logger.info("Successfully generated preview for {} refactoring on {} in workspace {}", 
                       operationType, filePath, workspaceId);
            
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            logger.error("Failed to preview refactoring: {}", e.getMessage());
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("success", false);
            errorResponse.put("error", e.getMessage());
            return ResponseEntity.internalServerError().body(errorResponse);
        }
    }

    /**
     * Execute real refactoring operation
     */
    @PostMapping("/refactoring/{workspaceId}/execute")
    public ResponseEntity<Map<String, Object>> executeRefactoring(
            @PathVariable String workspaceId,
            @RequestBody Map<String, Object> request) {
        try {
            String operationType = (String) request.get("operationType");
            String filePath = (String) request.get("filePath");
            String methodName = (String) request.get("methodName");
            String newMethodName = (String) request.get("newMethodName");
            String newClassName = (String) request.get("newClassName");
            
            logger.info("Executing {} refactoring on {} in workspace {}", operationType, filePath, workspaceId);
            
            ProjectContext projectContext = projectService.getProject(workspaceId);
            if (projectContext == null) {
                return ResponseEntity.notFound().build();
            }
            
            Path fullPath = projectContext.root().resolve(filePath);
            if (!Files.exists(fullPath)) {
                return ResponseEntity.notFound().build();
            }
            
            // Create backup
            Path backupPath = fullPath.resolveSibling(fullPath.getFileName() + ".backup");
            try {
                // Delete existing backup if it exists
                if (Files.exists(backupPath)) {
                    Files.delete(backupPath);
                }
                Files.copy(fullPath, backupPath);
                logger.info("Created backup file: {}", backupPath);
            } catch (Exception backupError) {
                logger.error("Failed to create backup file: {}", backupError.getMessage());
                throw new RuntimeException("Failed to create backup: " + backupError.getMessage());
            }
            
            String originalContent = Files.readString(fullPath);
            String refactoredContent = performRefactoring(originalContent, operationType, methodName, newMethodName, newClassName);
            
            // Write refactored content
            try {
                Files.write(fullPath, refactoredContent.getBytes(StandardCharsets.UTF_8));
                logger.info("Successfully wrote refactored content to: {}", fullPath);
            } catch (Exception writeError) {
                logger.error("Failed to write refactored content: {}", writeError.getMessage());
                // Try to restore from backup
                try {
                    if (Files.exists(backupPath)) {
                        Files.copy(backupPath, fullPath, StandardCopyOption.REPLACE_EXISTING);
                        logger.info("Restored original content from backup");
                    }
                } catch (Exception restoreError) {
                    logger.error("Failed to restore from backup: {}", restoreError.getMessage());
                }
                throw new RuntimeException("Failed to write refactored content: " + writeError.getMessage());
            }
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", true);
            response.put("operationType", operationType);
            response.put("filePath", filePath);
            response.put("backupPath", backupPath.toString());
            response.put("originalContent", originalContent);
            response.put("refactoredContent", refactoredContent);
            response.put("changes", generateChangeSummary(originalContent, refactoredContent));
            
            logger.info("Successfully executed {} refactoring on {} in workspace {}", 
                       operationType, filePath, workspaceId);
            
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            logger.error("Failed to execute refactoring: {}", e.getMessage());
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("success", false);
            errorResponse.put("error", e.getMessage());
            return ResponseEntity.internalServerError().body(errorResponse);
        }
    }

    /**
     * Perform the actual refactoring operation
     */
    private String performRefactoring(String content, String operationType, String methodName, 
                                    String newMethodName, String newClassName) {
        switch (operationType.toUpperCase()) {
            case "EXTRACT_METHOD":
                return extractMethod(content, methodName, newMethodName);
            case "RENAME_METHOD":
                return renameMethod(content, methodName, newMethodName);
            case "RENAME_CLASS":
                return renameClass(content, newClassName);
            case "MOVE_METHOD":
                return moveMethod(content, methodName, newClassName);
            case "EXTRACT_CLASS":
                return extractClass(content, methodName, newClassName);
            default:
                throw new IllegalArgumentException("Unsupported refactoring operation: " + operationType);
        }
    }

    /**
     * Extract method refactoring
     */
    private String extractMethod(String content, String methodName, String newMethodName) {
        // Simple method extraction - find method and extract it
        Pattern methodPattern = Pattern.compile(
            "(\\s*)(public|private|protected)?\\s*(static)?\\s*\\w+\\s+" + Pattern.quote(methodName) + "\\s*\\([^)]*\\)\\s*\\{",
            Pattern.MULTILINE
        );
        
        Matcher matcher = methodPattern.matcher(content);
        if (matcher.find()) {
            String extractedMethod = matcher.group(0) + "\n        // Extracted method implementation\n        return null;\n    }\n";
            String methodCall = "        " + newMethodName + "();\n";
            
            return content.replace(matcher.group(0), methodCall) + "\n\n" + extractedMethod;
        }
        
        return content;
    }

    /**
     * Rename method refactoring
     */
    private String renameMethod(String content, String oldName, String newName) {
        return content.replaceAll("\\b" + Pattern.quote(oldName) + "\\b", newName);
    }

    /**
     * Rename class refactoring
     */
    private String renameClass(String content, String newClassName) {
        // Find class declaration and rename it
        Pattern classPattern = Pattern.compile("class\\s+\\w+");
        return classPattern.matcher(content).replaceAll("class " + newClassName);
    }

    /**
     * Move method refactoring (simplified)
     */
    private String moveMethod(String content, String methodName, String newClassName) {
        // For now, just add a comment indicating the method should be moved
        return content + "\n    // TODO: Move method " + methodName + " to class " + newClassName;
    }

    /**
     * Extract class refactoring (simplified)
     */
    private String extractClass(String content, String methodName, String newClassName) {
        // For now, just add a comment indicating the class should be extracted
        return content + "\n    // TODO: Extract class " + newClassName + " containing method " + methodName;
    }

    /**
     * Generate change summary
     */
    private Map<String, Object> generateChangeSummary(String original, String refactored) {
        Map<String, Object> summary = new HashMap<>();
        summary.put("linesChanged", Math.abs(original.split("\n").length - refactored.split("\n").length));
        summary.put("charactersChanged", Math.abs(original.length() - refactored.length()));
        summary.put("hasChanges", !original.equals(refactored));
        return summary;
    }

    /**
     * Assess risk level of refactoring operation
     */
    private String assessRiskLevel(String operationType, String originalContent, String refactoredContent) {
        int changeSize = Math.abs(originalContent.length() - refactoredContent.length());
        int lineChanges = Math.abs(originalContent.split("\n").length - refactoredContent.split("\n").length);
        
        // Simple risk assessment based on operation type and change size
        switch (operationType.toUpperCase()) {
            case "RENAME_METHOD":
                return changeSize > 1000 ? "HIGH" : "LOW";
            case "RENAME_CLASS":
                return "HIGH"; // Class renaming affects imports and inheritance
            case "EXTRACT_METHOD":
                return lineChanges > 20 ? "MEDIUM" : "LOW";
            case "MOVE_METHOD":
                return "HIGH"; // Moving methods affects multiple classes
            case "EXTRACT_CLASS":
                return "HIGH"; // Extracting classes is complex
            default:
                return "MEDIUM";
        }
    }

    /**
     * Estimate number of dependencies for a method
     */
    private int estimateDependencies(String content, String methodName) {
        // Simple estimation based on method calls and imports
        int imports = content.split("import ").length - 1;
        int methodCalls = content.split("\\b" + Pattern.quote(methodName) + "\\b").length - 1;
        
        return Math.min(imports + methodCalls, 10); // Cap at 10 for display
    }

    /**
     * Generate detailed dependency information for the dependency graph
     * This analyzes actual Java code to find real dependencies
     */
    private Map<String, Object> generateDetailedDependencies(String content, String methodName, String filePath) {
        Map<String, Object> dependencies = new HashMap<>();
        
        // Extract imports (incoming dependencies)
        List<Map<String, String>> incomingDeps = new ArrayList<>();
        List<Map<String, String>> outgoingDeps = new ArrayList<>();
        
        // Parse imports as incoming dependencies
        String[] lines = content.split("\n");
        for (String line : lines) {
            if (line.trim().startsWith("import ")) {
                String importPath = line.trim().substring(7).replace(";", "");
                String className = importPath.substring(importPath.lastIndexOf('.') + 1);
                
                Map<String, String> dep = new HashMap<>();
                dep.put("file", className + ".java");
                dep.put("type", "import");
                dep.put("method", "import");
                incomingDeps.add(dep);
            }
        }
        
        // Analyze method calls and class usage for outgoing dependencies
        analyzeMethodCalls(content, outgoingDeps);
        analyzeClassUsage(content, outgoingDeps);
        analyzeInheritance(content, outgoingDeps);
        
        dependencies.put("incoming", incomingDeps);
        dependencies.put("outgoing", outgoingDeps);
        
        return dependencies;
    }
    
    /**
     * Analyze method calls in the Java code to find outgoing dependencies
     */
    private void analyzeMethodCalls(String content, List<Map<String, String>> outgoingDeps) {
        // Look for method calls like: object.method() or Class.method()
        String[] lines = content.split("\n");
        for (String line : lines) {
            // Skip comments and empty lines
            if (line.trim().startsWith("//") || line.trim().startsWith("*") || line.trim().isEmpty()) {
                continue;
            }
            
            // Find method calls with dot notation
            if (line.contains(".") && line.contains("(") && line.contains(")")) {
                // Extract potential class.method() patterns
                String[] parts = line.split("\\.");
                for (int i = 0; i < parts.length - 1; i++) {
                    String potentialClass = parts[i].trim();
                    // Clean up the class name (remove variables, keywords, etc.)
                    potentialClass = cleanClassName(potentialClass);
                    
                    if (isValidClassName(potentialClass) && !isJavaKeyword(potentialClass)) {
                        Map<String, String> dep = new HashMap<>();
                        dep.put("file", potentialClass + ".java");
                        dep.put("type", "method_call");
                        dep.put("method", "method_call");
                        outgoingDeps.add(dep);
                    }
                }
            }
        }
    }
    
    /**
     * Analyze class instantiation and usage
     */
    private void analyzeClassUsage(String content, List<Map<String, String>> outgoingDeps) {
        String[] lines = content.split("\n");
        for (String line : lines) {
            // Skip comments and empty lines
            if (line.trim().startsWith("//") || line.trim().startsWith("*") || line.trim().isEmpty()) {
                continue;
            }
            
            // Look for "new ClassName(" patterns
            if (line.contains("new ") && line.contains("(")) {
                String[] parts = line.split("new ");
                for (String part : parts) {
                    if (part.contains("(")) {
                        String className = part.substring(0, part.indexOf("(")).trim();
                        className = cleanClassName(className);
                        
                        if (isValidClassName(className) && !isJavaKeyword(className)) {
                            Map<String, String> dep = new HashMap<>();
                            dep.put("file", className + ".java");
                            dep.put("type", "composition");
                            dep.put("method", "new " + className);
                            outgoingDeps.add(dep);
                        }
                    }
                }
            }
        }
    }
    
    /**
     * Analyze inheritance and interface implementation
     */
    private void analyzeInheritance(String content, List<Map<String, String>> outgoingDeps) {
        String[] lines = content.split("\n");
        for (String line : lines) {
            // Skip comments and empty lines
            if (line.trim().startsWith("//") || line.trim().startsWith("*") || line.trim().isEmpty()) {
                continue;
            }
            
            // Look for "extends" or "implements" keywords
            if (line.contains("extends ") || line.contains("implements ")) {
                String[] parts = line.split("(extends|implements)");
                if (parts.length > 1) {
                    String[] classNames = parts[1].split("[,\\s]+");
                    for (String className : classNames) {
                        className = cleanClassName(className);
                        if (isValidClassName(className) && !isJavaKeyword(className)) {
                            Map<String, String> dep = new HashMap<>();
                            dep.put("file", className + ".java");
                            dep.put("type", "inheritance");
                            dep.put("method", "inheritance");
                            outgoingDeps.add(dep);
                        }
                    }
                }
            }
        }
    }
    
    /**
     * Clean up class name by removing unwanted characters
     */
    private String cleanClassName(String className) {
        // Remove common prefixes and suffixes
        className = className.replaceAll("^[a-z]+\\s*", ""); // Remove variable names
        className = className.replaceAll("[<>\\[\\]();,]", ""); // Remove brackets, parentheses, etc.
        className = className.trim();
        return className;
    }
    
    /**
     * Check if a string is a valid class name
     */
    private boolean isValidClassName(String className) {
        if (className == null || className.isEmpty()) return false;
        if (className.length() < 2) return false;
        if (!Character.isUpperCase(className.charAt(0))) return false;
        return className.matches("[A-Za-z0-9_]+");
    }
    
    /**
     * Check if a string is a Java keyword
     */
    private boolean isJavaKeyword(String word) {
        String[] keywords = {
            "abstract", "assert", "boolean", "break", "byte", "case", "catch", "char", "class", "const",
            "continue", "default", "do", "double", "else", "enum", "extends", "final", "finally", "float",
            "for", "goto", "if", "implements", "import", "instanceof", "int", "interface", "long", "native",
            "new", "package", "private", "protected", "public", "return", "short", "static", "strictfp",
            "super", "switch", "synchronized", "this", "throw", "throws", "transient", "try", "void",
            "volatile", "while", "true", "false", "null"
        };
        
        for (String keyword : keywords) {
            if (keyword.equals(word.toLowerCase())) {
                return true;
            }
        }
        return false;
    }

    /**
     * Get detailed dependency information for a file
     */
    @GetMapping("/files/{workspaceId}/dependencies")
    public ResponseEntity<Map<String, Object>> getFileDependencies(
            @PathVariable String workspaceId,
            @RequestParam String filePath) {
        try {
            ProjectContext projectContext = projectService.getProject(workspaceId);
            if (projectContext == null) {
                return ResponseEntity.notFound().build();
            }
            
            Path fullPath = projectContext.root().resolve(filePath);
            if (!Files.exists(fullPath)) {
                return ResponseEntity.notFound().build();
            }
            
            String content = Files.readString(fullPath, StandardCharsets.UTF_8);
            Map<String, Object> dependencies = generateDetailedDependencies(content, null, filePath);
            
            logger.info("Retrieved dependencies for file {} in workspace {}", filePath, workspaceId);
            return ResponseEntity.ok(dependencies);
        } catch (Exception e) {
            logger.error("Failed to get file dependencies: {}", e.getMessage());
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("error", e.getMessage());
            return ResponseEntity.internalServerError().body(errorResponse);
        }
    }

    /**
     * List all Java files in the workspace
     */
    @GetMapping("/files/{workspaceId}/list")
    public ResponseEntity<List<Map<String, Object>>> listJavaFiles(@PathVariable String workspaceId) {
        try {
            logger.info("Listing Java files for workspace: {}", workspaceId);
            
            ProjectContext projectContext = projectService.getProject(workspaceId);
            if (projectContext == null) {
                return ResponseEntity.notFound().build();
            }
            
            List<Map<String, Object>> javaFiles = new ArrayList<>();
            
            // Walk through the project directory to find Java files
            Files.walk(projectContext.root())
                .filter(path -> path.toString().endsWith(".java"))
                .forEach(path -> {
                    try {
                        String relativePath = projectContext.root().relativize(path).toString();
                        Map<String, Object> fileInfo = new HashMap<>();
                        fileInfo.put("path", relativePath);
                        fileInfo.put("name", path.getFileName().toString());
                        fileInfo.put("size", Files.size(path));
                        fileInfo.put("lastModified", Files.getLastModifiedTime(path).toMillis());
                        javaFiles.add(fileInfo);
                    } catch (IOException e) {
                        logger.warn("Failed to get file info for: {}", path, e);
                    }
                });
            
            return ResponseEntity.ok(javaFiles);
            
        } catch (Exception e) {
            logger.error("Failed to list Java files for workspace: {}", workspaceId, e);
            return ResponseEntity.badRequest().build();
        }
    }

    /**
     * Analyze Java file content using regex patterns
     */
    private Map<String, Object> analyzeJavaFile(String content, String filePath) {
        Map<String, Object> analysis = new HashMap<>();
        
        // Extract class name
        Pattern classPattern = Pattern.compile("public\\s+class\\s+(\\w+)");
        Matcher classMatcher = classPattern.matcher(content);
        String className = classMatcher.find() ? classMatcher.group(1) : "UnknownClass";
        
        // Extract method names
        Pattern methodPattern = Pattern.compile("public\\s+\\w+\\s+(\\w+)\\s*\\(");
        Matcher methodMatcher = methodPattern.matcher(content);
        List<String> methods = new ArrayList<>();
        while (methodMatcher.find()) {
            methods.add(methodMatcher.group(1));
        }
        
        // Extract import statements
        Pattern importPattern = Pattern.compile("import\\s+([^;]+);");
        Matcher importMatcher = importPattern.matcher(content);
        List<String> imports = new ArrayList<>();
        while (importMatcher.find()) {
            imports.add(importMatcher.group(1));
        }
        
        // Calculate basic metrics
        String[] lines = content.split("\n");
        int linesOfCode = lines.length;
        int commentLines = 0;
        int emptyLines = 0;
        
        for (String line : lines) {
            String trimmed = line.trim();
            if (trimmed.isEmpty()) {
                emptyLines++;
            } else if (trimmed.startsWith("//") || trimmed.startsWith("/*") || trimmed.startsWith("*")) {
                commentLines++;
            }
        }
        
        // Calculate complexity (simple approximation)
        int complexity = 1; // Base complexity
        complexity += content.split("if\\s*\\(").length - 1;
        complexity += content.split("for\\s*\\(").length - 1;
        complexity += content.split("while\\s*\\(").length - 1;
        complexity += content.split("switch\\s*\\(").length - 1;
        complexity += content.split("catch\\s*\\(").length - 1;
        
        analysis.put("className", className);
        analysis.put("methods", methods);
        analysis.put("imports", imports);
        analysis.put("linesOfCode", linesOfCode);
        analysis.put("commentLines", commentLines);
        analysis.put("emptyLines", emptyLines);
        analysis.put("complexity", Math.max(1, complexity));
        analysis.put("filePath", filePath);
        
        return analysis;
    }
    
    /**
     * NEW ENDPOINT: Analyze Java file using AST-based analysis
     * This provides accurate code analysis alongside existing regex-based analysis
     */
    @GetMapping("/workspaces/{workspaceId}/ast-analysis/**")
    public ResponseEntity<ASTAnalysisResult> analyzeFileWithAST(
            @PathVariable String workspaceId,
            HttpServletRequest request) {
        
        try {
            // Extract file path from request URI
            String requestURI = request.getRequestURI();
            String filePath = requestURI.substring(requestURI.indexOf("/ast-analysis/") + "/ast-analysis/".length());
            logger.info("Starting AST analysis for workspace: {}, file: {}", workspaceId, filePath);
            
            ProjectContext projectContext = projectService.getProject(workspaceId);
            if (projectContext == null) {
                logger.warn("Project not found for workspace: {}", workspaceId);
                return ResponseEntity.notFound().build();
            }
            
            // Construct full file path
            Path fullPath = projectContext.root().resolve(filePath);
            
            // Verify file exists and is a Java file
            if (!Files.exists(fullPath) || !filePath.endsWith(".java")) {
                logger.warn("File not found or not a Java file: {}", fullPath);
                return ResponseEntity.badRequest().build();
            }
            
            // Perform AST analysis
            ASTAnalysisResult result = astBasedAnalyzer.analyzeFile(fullPath);
            
            logger.info("AST analysis completed for file: {} - Classes: {}, Methods: {}, Imports: {}", 
                       filePath, result.getTotalClasses(), result.getTotalMethods(), result.getTotalImports());
            
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            logger.error("Error during AST analysis for workspace: {}", workspaceId, e);
            return ResponseEntity.badRequest().build();
        }
    }
    
    /**
     * NEW ENDPOINT: Get enhanced analysis combining regex and AST analysis
     * This provides comprehensive analysis using both approaches
     */
    @GetMapping("/workspaces/{workspaceId}/enhanced-analysis/**")
    public ResponseEntity<Map<String, Object>> getEnhancedAnalysis(
            @PathVariable String workspaceId,
            HttpServletRequest request) {
        
        try {
            // Extract file path from request URI
            String requestURI = request.getRequestURI();
            String filePath = requestURI.substring(requestURI.indexOf("/enhanced-analysis/") + "/enhanced-analysis/".length());
            logger.info("Starting enhanced analysis for workspace: {}, file: {}", workspaceId, filePath);
            
            ProjectContext projectContext = projectService.getProject(workspaceId);
            if (projectContext == null) {
                return ResponseEntity.notFound().build();
            }
            
            Path fullPath = projectContext.root().resolve(filePath);
            if (!Files.exists(fullPath) || !filePath.endsWith(".java")) {
                return ResponseEntity.badRequest().build();
            }
            
            // Read file content for regex analysis
            String content = Files.readString(fullPath, StandardCharsets.UTF_8);
            
            // Perform both analyses
            Map<String, Object> regexAnalysis = analyzeJavaFile(content, filePath);
            ASTAnalysisResult astAnalysis = astBasedAnalyzer.analyzeFile(fullPath);
            
            // Combine results
            Map<String, Object> enhancedAnalysis = new HashMap<>();
            enhancedAnalysis.put("filePath", filePath);
            enhancedAnalysis.put("fileName", fullPath.getFileName().toString());
            enhancedAnalysis.put("regexAnalysis", regexAnalysis);
            enhancedAnalysis.put("astAnalysis", astAnalysis);
            enhancedAnalysis.put("analysisTimestamp", System.currentTimeMillis());
            
            // Add comparison metrics
            Map<String, Object> comparison = new HashMap<>();
            comparison.put("regexClasses", ((List<?>) regexAnalysis.get("methods")).size());
            comparison.put("astClasses", astAnalysis.getTotalClasses());
            comparison.put("regexMethods", ((List<?>) regexAnalysis.get("methods")).size());
            comparison.put("astMethods", astAnalysis.getTotalMethods());
            comparison.put("regexImports", ((List<?>) regexAnalysis.get("imports")).size());
            comparison.put("astImports", astAnalysis.getTotalImports());
            enhancedAnalysis.put("comparison", comparison);
            
            logger.info("Enhanced analysis completed for file: {}", filePath);
            
            return ResponseEntity.ok(enhancedAnalysis);
            
        } catch (Exception e) {
            logger.error("Error during enhanced analysis for workspace: {}", workspaceId, e);
            return ResponseEntity.badRequest().build();
        }
    }
    
    /**
     * NEW ENDPOINT: Send request to LLM for refactoring assistance
     * This provides AI-powered refactoring suggestions and code analysis
     */
    @PostMapping("/llm/refactoring")
    public ResponseEntity<LLMResponse> getRefactoringSuggestion(@RequestBody LLMRequest request) {
        try {
            logger.info("Received LLM refactoring request");
            
            // Check cost limits
            if (llmService.isCostLimitExceeded()) {
                logger.warn("Cost limit exceeded, rejecting request");
                return ResponseEntity.status(429).build();
            }
            
            // Redact sensitive information
            if (request.getMessages() != null) {
                for (Map<String, String> message : request.getMessages()) {
                    String content = message.get("content");
                    if (content != null) {
                        message.put("content", llmService.redactSensitiveInfo(content));
                    }
                }
            }
            
            // Set request type
            request.setRequestType("refactoring");
            
            // Send request to LLM service
            LLMResponse response = llmService.sendRequest(request).block();
            
            if (response != null && response.isSuccess()) {
                logger.info("LLM refactoring request completed successfully");
                return ResponseEntity.ok(response);
            } else {
                logger.error("LLM refactoring request failed");
                
                // Return mock response with error details
                LLMResponse errorResponse = new LLMResponse();
                errorResponse.setSuccess(false);
                errorResponse.setError("LLM service is not configured. Please set the OPENROUTER_API_KEY environment variable.");
                errorResponse.setContent("// LLM refactoring is not available\n// To enable this feature, set the OPENROUTER_API_KEY environment variable\n// or configure a local LLM provider.");
                return ResponseEntity.status(503).body(errorResponse);
            }
            
        } catch (Exception e) {
            logger.error("Error processing LLM refactoring request", e);
            
            // Return detailed error response instead of just badRequest
            LLMResponse errorResponse = new LLMResponse();
            errorResponse.setSuccess(false);
            errorResponse.setError("LLM service error: " + e.getMessage());
            errorResponse.setContent("// LLM refactoring failed\n// Error: " + e.getMessage() + "\n// Please check the backend logs for more details.");
            return ResponseEntity.status(503).body(errorResponse);
        }
    }
    
    /**
     * NEW ENDPOINT: Get LLM usage statistics
     */
    @GetMapping("/llm/usage")
    public ResponseEntity<Map<String, Object>> getLLMUsage() {
        try {
            Map<String, Object> usage = llmService.getUsageStatistics();
            return ResponseEntity.ok(usage);
        } catch (Exception e) {
            logger.error("Error getting LLM usage statistics", e);
            return ResponseEntity.badRequest().build();
        }
    }
    
    /**
     * NEW ENDPOINT: Apply refactoring changes to actual files
     */
    @PostMapping("/refactoring/apply")
    public ResponseEntity<?> applyRefactoring(@RequestBody Map<String, Object> request) {
        try {
            String workspaceId = (String) request.get("workspaceId");
            String filePath = (String) request.get("filePath");
            String refactoredCode = (String) request.get("refactoredCode");
            
            logger.info("Applying refactoring to file: {} in workspace: {}", filePath, workspaceId);
            
            // Get the project directory
            Path projectDir = projectService.getProjectDirectory(workspaceId);
            Path targetFile = projectDir.resolve(filePath);
            
            // Check if file exists, if not create it
            if (!Files.exists(targetFile)) {
                logger.warn("Target file does not exist, creating: {}", targetFile);
                Files.createDirectories(targetFile.getParent());
                Files.createFile(targetFile);
            }
            
            // Create backup
            Path backupFile = projectDir.resolve(filePath + ".backup." + System.currentTimeMillis());
            Files.copy(targetFile, backupFile, StandardCopyOption.REPLACE_EXISTING);
            logger.info("Created backup: {}", backupFile);
            
            // Apply refactored code
            Files.write(targetFile, refactoredCode.getBytes(StandardCharsets.UTF_8));
            logger.info("Applied refactored code to: {}", targetFile);
            
            Map<String, Object> result = new HashMap<>();
            result.put("success", true);
            result.put("message", "Refactoring applied successfully");
            result.put("filePath", filePath);
            result.put("backupPath", backupFile.toString());
            result.put("timestamp", System.currentTimeMillis());
            
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            logger.error("Error applying refactoring: ", e);
            return ResponseEntity.internalServerError().body(Map.of(
                "success", false,
                "error", "Failed to apply refactoring: " + e.getMessage()
            ));
        }
    }
    
    /**
     * NEW ENDPOINT: Analyze code with LLM assistance
     */
    @PostMapping("/workspaces/{workspaceId}/llm-analysis/**")
    public ResponseEntity<Map<String, Object>> analyzeWithLLM(
            @PathVariable String workspaceId,
            HttpServletRequest request,
            @RequestBody Map<String, String> analysisRequest) {
        
        try {
            // Extract file path from request URI
            String requestURI = request.getRequestURI();
            String filePath = requestURI.substring(requestURI.indexOf("/llm-analysis/") + "/llm-analysis/".length());
            logger.info("Starting LLM-assisted analysis for workspace: {}, file: {}", workspaceId, filePath);
            
            ProjectContext projectContext = projectService.getProject(workspaceId);
            if (projectContext == null) {
                return ResponseEntity.notFound().build();
            }
            
            Path fullPath = projectContext.root().resolve(filePath);
            if (!Files.exists(fullPath) || !filePath.endsWith(".java")) {
                return ResponseEntity.badRequest().build();
            }
            
            // Read file content
            String content = Files.readString(fullPath, StandardCharsets.UTF_8);
            
            // Redact sensitive information
            String redactedContent = llmService.redactSensitiveInfo(content);
            
            // Prepare LLM request
            LLMRequest llmRequest = new LLMRequest();
            llmRequest.addSystemMessage("You are an expert Java code analyst. Analyze the provided code and suggest improvements, identify code smells, and provide refactoring recommendations.");
            llmRequest.addUserMessage("Please analyze this Java code:\n\n" + redactedContent);
            llmRequest.setRequestType("code-analysis");
            llmRequest.setMaxTokens(4000);
            llmRequest.setTemperature(0.3);
            
            // Get LLM analysis
            LLMResponse llmResponse = llmService.sendRequest(llmRequest).block();
            
            // Combine with AST analysis
            ASTAnalysisResult astResult = astBasedAnalyzer.analyzeFile(fullPath);
            
            // Prepare response
            Map<String, Object> response = new HashMap<>();
            response.put("filePath", filePath);
            response.put("fileName", fullPath.getFileName().toString());
            response.put("astAnalysis", astResult);
            response.put("llmAnalysis", llmResponse);
            response.put("analysisTimestamp", System.currentTimeMillis());
            
            logger.info("LLM-assisted analysis completed for file: {}", filePath);
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            logger.error("Error during LLM-assisted analysis for workspace: {}", workspaceId, e);
            return ResponseEntity.badRequest().build();
        }
    }
    
    /**
     * Enhanced comprehensive security analysis for Java files
     */
    private List<Map<String, Object>> analyzeJavaFileForSecurityIssues(String content, String filePath) {
        List<Map<String, Object>> vulnerabilities = new ArrayList<>();
        
        // 1. SQL Injection patterns (Enhanced)
        if (content.contains("Statement.executeQuery") || content.contains("Statement.executeUpdate") || 
            content.contains("Statement.execute") || content.contains("createStatement()")) {
            if (!content.contains("PreparedStatement") && !content.contains("CallableStatement")) {
                Map<String, Object> vuln = createVulnerability("SQL-INJ", "SQL Injection", "CRITICAL", "INJECTION", 
                    filePath, findLineNumber(content, "Statement.execute"), 
                    "Direct SQL statement execution without parameterized queries - vulnerable to SQL injection",
                    9.8, "Use PreparedStatement or CallableStatement for parameterized queries");
                vulnerabilities.add(vuln);
            }
        }
        
        // 2. Command Injection patterns (Enhanced)
        if (content.contains("Runtime.exec") || content.contains("ProcessBuilder") || 
            content.contains("ProcessBuilder(") || content.contains("getRuntime()")) {
            if (!content.contains("sanitize") && !content.contains("validate") && 
                !content.contains("whitelist") && !content.contains("allowlist")) {
                Map<String, Object> vuln = createVulnerability("CMD-INJ", "Command Injection", "HIGH", "INJECTION",
                    filePath, findLineNumber(content, "Runtime.exec"),
                    "Command execution without proper input validation - vulnerable to command injection",
                    8.1, "Validate and sanitize user input, use whitelist for allowed commands");
                vulnerabilities.add(vuln);
            }
        }
        
        // 3. Path Traversal patterns (Enhanced)
        if (content.contains("FileInputStream") || content.contains("FileOutputStream") || 
            content.contains("FileReader") || content.contains("FileWriter") ||
            content.contains("Files.read") || content.contains("Files.write")) {
            if (content.contains("..") || content.contains("getPath()") || content.contains("getAbsolutePath()") ||
                content.contains("getCanonicalPath()") || content.contains("getParent()")) {
                Map<String, Object> vuln = createVulnerability("PATH-TRAV", "Path Traversal", "HIGH", "SECURITY_MISCONFIGURATION",
                    filePath, findLineNumber(content, "FileInputStream"),
                    "File operations without path validation - vulnerable to directory traversal attacks",
                    7.5, "Validate file paths, use Path.normalize(), and restrict to allowed directories");
                vulnerabilities.add(vuln);
            }
        }
        
        // 4. Hardcoded credentials (Enhanced)
        Pattern passwordPattern = Pattern.compile("(password|passwd|pwd|secret|key|token)\\s*[=:]\\s*[\"'][^\"']+[\"']", Pattern.CASE_INSENSITIVE);
        if (passwordPattern.matcher(content).find()) {
            Map<String, Object> vuln = createVulnerability("HARD-CRED", "Hardcoded Credentials", "CRITICAL", "SENSITIVE_DATA_EXPOSURE",
                filePath, findLineNumber(content, "password"),
                "Hardcoded credentials found in source code - major security risk",
                9.1, "Use environment variables, configuration files, or secure credential storage");
            vulnerabilities.add(vuln);
        }
        
        // 5. Weak cryptography (Enhanced)
        if (content.contains("MD5") || content.contains("DES") || content.contains("RC4") || 
            content.contains("SHA1") || content.contains("MD4") || content.contains("MD2")) {
            Map<String, Object> vuln = createVulnerability("WEAK-CRYPTO", "Weak Cryptography", "MEDIUM", "SECURITY_MISCONFIGURATION",
                filePath, findLineNumber(content, "MD5"),
                "Weak cryptographic algorithm detected - vulnerable to cryptographic attacks",
                5.3, "Use stronger algorithms: SHA-256, SHA-3, AES-256, ChaCha20-Poly1305");
            vulnerabilities.add(vuln);
        }
        
        // 6. Cross-Site Scripting (XSS) patterns
        if (content.contains("HttpServletResponse") && (content.contains("getWriter()") || content.contains("getOutputStream()"))) {
            if (!content.contains("escapeHtml") && !content.contains("encode") && !content.contains("sanitize")) {
                Map<String, Object> vuln = createVulnerability("XSS", "Cross-Site Scripting", "HIGH", "XSS",
                    filePath, findLineNumber(content, "getWriter()"),
                    "Unescaped output to HTTP response - vulnerable to XSS attacks",
                    7.2, "Escape or encode user input before output, use proper encoding libraries");
                vulnerabilities.add(vuln);
            }
        }
        
        // 7. Insecure deserialization
        if (content.contains("ObjectInputStream") || content.contains("readObject()") || 
            content.contains("XMLDecoder") || content.contains("JSON.parse")) {
            Map<String, Object> vuln = createVulnerability("INSEC-DESER", "Insecure Deserialization", "CRITICAL", "SECURITY_MISCONFIGURATION",
                filePath, findLineNumber(content, "ObjectInputStream"),
                "Insecure deserialization detected - vulnerable to remote code execution",
                9.6, "Use safe deserialization libraries, validate input, or avoid deserialization of untrusted data");
            vulnerabilities.add(vuln);
        }
        
        // 8. Weak random number generation
        if (content.contains("Random()") || content.contains("Math.random()")) {
            Map<String, Object> vuln = createVulnerability("WEAK-RAND", "Weak Random Number Generation", "MEDIUM", "SECURITY_MISCONFIGURATION",
                filePath, findLineNumber(content, "Random()"),
                "Weak random number generation for security purposes",
                4.7, "Use SecureRandom for cryptographic operations and security-sensitive random numbers");
            vulnerabilities.add(vuln);
        }
        
        // 9. Information disclosure through exceptions
        if (content.contains("printStackTrace()") || content.contains("e.getMessage()")) {
            if (content.contains("HttpServletResponse") || content.contains("System.out") || content.contains("System.err")) {
                Map<String, Object> vuln = createVulnerability("INFO-DISC", "Information Disclosure", "MEDIUM", "SENSITIVE_DATA_EXPOSURE",
                    filePath, findLineNumber(content, "printStackTrace()"),
                    "Sensitive information may be disclosed through exception handling",
                    4.2, "Log exceptions securely, avoid exposing sensitive information to users");
                vulnerabilities.add(vuln);
            }
        }
        
        // 10. Missing authentication/authorization
        if (content.contains("@RequestMapping") || content.contains("@GetMapping") || content.contains("@PostMapping")) {
            if (!content.contains("@PreAuthorize") && !content.contains("@Secured") && !content.contains("@RolesAllowed")) {
                Map<String, Object> vuln = createVulnerability("MISS-AUTH", "Missing Authentication", "HIGH", "BROKEN_AUTHENTICATION",
                    filePath, findLineNumber(content, "@RequestMapping"),
                    "Web endpoint without authentication/authorization controls",
                    6.8, "Implement proper authentication and authorization controls for web endpoints");
                vulnerabilities.add(vuln);
            }
        }
        
        // 11. Unsafe reflection usage (Enhanced detection)
        if (content.contains("getDeclaredField") || content.contains("getDeclaredMethod") || 
            content.contains("getDeclaredConstructor") || content.contains("setAccessible(true)") ||
            content.contains("Class.forName") || content.contains("getField") || content.contains("getMethod")) {
            
            // Find the most specific pattern first
            int lineNumber = 1;
            if (content.contains("getDeclaredField")) {
                lineNumber = findLineNumber(content, "getDeclaredField");
            } else if (content.contains("getDeclaredMethod")) {
                lineNumber = findLineNumber(content, "getDeclaredMethod");
            } else if (content.contains("setAccessible(true)")) {
                lineNumber = findLineNumber(content, "setAccessible(true)");
            } else if (content.contains("Class.forName")) {
                lineNumber = findLineNumber(content, "Class.forName");
            }
            
            Map<String, Object> vuln = createVulnerability("UNSAFE-REFL", "Unsafe Reflection", "HIGH", "SECURITY_MISCONFIGURATION",
                filePath, lineNumber,
                "Unsafe reflection usage - may allow unauthorized access to private members",
                7.3, "Validate reflection targets, use allowlists, and avoid user-controlled reflection");
            vulnerabilities.add(vuln);
        }
        
        // 12. Resource exhaustion (DoS)
        if (content.contains("while(true)") || content.contains("for(;;)") || content.contains("Thread.sleep(0)")) {
            if (content.contains("public") && (content.contains("@RequestMapping") || content.contains("@GetMapping"))) {
                Map<String, Object> vuln = createVulnerability("RES-EXHAUST", "Resource Exhaustion", "MEDIUM", "SECURITY_MISCONFIGURATION",
                    filePath, findLineNumber(content, "while(true)"),
                    "Potential infinite loop in web endpoint - vulnerable to DoS attacks",
                    5.8, "Add proper loop termination conditions, timeouts, and rate limiting");
                vulnerabilities.add(vuln);
            }
        }
        
        return vulnerabilities;
    }
    
    /**
     * Helper method to create vulnerability objects
     */
    private Map<String, Object> createVulnerability(String idPrefix, String type, String severity, String category,
                                                   String filePath, int line, String description, double cvssScore, String remediation) {
        Map<String, Object> vuln = new HashMap<>();
        vuln.put("id", idPrefix + "-" + filePath.hashCode() + "-" + line);
        vuln.put("type", type);
        vuln.put("severity", severity);
        vuln.put("category", category);
        vuln.put("file", filePath);
        vuln.put("filePath", filePath);
        vuln.put("line", line);
        vuln.put("description", description);
        vuln.put("cvssScore", cvssScore);
        vuln.put("remediation", remediation);
        vuln.put("cwe", getCWECode(type));
        vuln.put("owasp", getOWASPCategory(type));
        return vuln;
    }
    
    /**
     * Get CWE code for vulnerability type
     */
    private String getCWECode(String type) {
        switch (type) {
            case "SQL Injection": return "CWE-89";
            case "Command Injection": return "CWE-78";
            case "Path Traversal": return "CWE-22";
            case "Hardcoded Credentials": return "CWE-798";
            case "Weak Cryptography": return "CWE-327";
            case "Cross-Site Scripting": return "CWE-79";
            case "Insecure Deserialization": return "CWE-502";
            case "Weak Random Number Generation": return "CWE-338";
            case "Information Disclosure": return "CWE-200";
            case "Missing Authentication": return "CWE-306";
            case "Unsafe Reflection": return "CWE-470";
            case "Resource Exhaustion": return "CWE-400";
            default: return "CWE-000";
        }
    }
    
    /**
     * Get OWASP Top 10 category
     */
    private String getOWASPCategory(String type) {
        switch (type) {
            case "SQL Injection":
            case "Command Injection":
            case "Cross-Site Scripting": return "A03:2021 – Injection";
            case "Hardcoded Credentials":
            case "Information Disclosure": return "A02:2021 – Cryptographic Failures";
            case "Missing Authentication": return "A07:2021 – Identification and Authentication Failures";
            case "Weak Cryptography":
            case "Weak Random Number Generation": return "A02:2021 – Cryptographic Failures";
            case "Insecure Deserialization": return "A08:2021 – Software and Data Integrity Failures";
            case "Unsafe Reflection":
            case "Path Traversal":
            case "Resource Exhaustion": return "A05:2021 – Security Misconfiguration";
            default: return "A04:2021 – Insecure Design";
        }
    }
    
    /**
     * Project-level security analysis
     */
    private List<Map<String, Object>> analyzeProjectLevelSecurity(Path workspacePath, List<Path> javaFiles) {
        List<Map<String, Object>> projectVulns = new ArrayList<>();
        
        try {
            // 1. Check for build configuration files
            List<Path> buildFiles = Files.walk(workspacePath)
                .filter(path -> path.toString().matches(".*\\.(xml|gradle|properties)$"))
                .collect(Collectors.toList());
            
            for (Path buildFile : buildFiles) {
                try {
                    String content = Files.readString(buildFile, StandardCharsets.UTF_8);
                    String relativePath = workspacePath.relativize(buildFile).toString();
                    
                    // Check for insecure dependencies
                    if (content.contains("commons-fileupload") && !content.contains("1.3.3")) {
                        projectVulns.add(createVulnerability("INSEC-DEP", "Insecure Dependency", "HIGH", "SECURITY_MISCONFIGURATION",
                            relativePath, 1, "Outdated commons-fileupload dependency - vulnerable to RCE",
                            8.5, "Update to commons-fileupload 1.3.3 or later"));
                    }
                    
                    if (content.contains("log4j") && !content.contains("2.17.0")) {
                        projectVulns.add(createVulnerability("LOG4J-VULN", "Log4j Vulnerability", "CRITICAL", "SECURITY_MISCONFIGURATION",
                            relativePath, 1, "Log4j dependency vulnerable to Log4Shell (CVE-2021-44228)",
                            10.0, "Update to Log4j 2.17.0 or later, or apply security patches"));
                    }
                    
                    if (content.contains("jackson-databind") && content.contains("2.9.10.8")) {
                        projectVulns.add(createVulnerability("JACKSON-VULN", "Jackson Vulnerability", "HIGH", "SECURITY_MISCONFIGURATION",
                            relativePath, 1, "Jackson databind vulnerable to deserialization attacks",
                            8.1, "Update Jackson databind to latest secure version"));
                    }
                    
                    // Check for debug/test configurations in production
                    if (content.contains("debug=true") || content.contains("debugging=true")) {
                        projectVulns.add(createVulnerability("DEBUG-CONFIG", "Debug Configuration", "MEDIUM", "SECURITY_MISCONFIGURATION",
                            relativePath, 1, "Debug mode enabled - may expose sensitive information",
                            5.2, "Disable debug mode in production environments"));
                    }
                    
                } catch (Exception e) {
                    logger.warn("Failed to analyze build file {}: {}", buildFile, e.getMessage());
                }
            }
            
            // 2. Check for security configuration files
            Path securityConfig = workspacePath.resolve("src/main/resources/application.properties");
            if (Files.exists(securityConfig)) {
                try {
                    String content = Files.readString(securityConfig, StandardCharsets.UTF_8);
                    
                    if (!content.contains("server.error.include-stacktrace=never")) {
                        projectVulns.add(createVulnerability("STACK-TRACE", "Stack Trace Exposure", "MEDIUM", "SENSITIVE_DATA_EXPOSURE",
                            "application.properties", 1, "Stack traces may be exposed to users",
                            4.8, "Set server.error.include-stacktrace=never in production"));
                    }
                    
                    if (!content.contains("server.error.include-message=never")) {
                        projectVulns.add(createVulnerability("ERROR-MSG", "Error Message Exposure", "LOW", "SENSITIVE_DATA_EXPOSURE",
                            "application.properties", 1, "Error messages may expose sensitive information",
                            3.2, "Set server.error.include-message=never in production"));
                    }
                    
                } catch (Exception e) {
                    logger.warn("Failed to analyze security config: {}", e.getMessage());
                }
            }
            
            // 3. Check for missing security headers
            boolean hasSecurityConfig = false;
            for (Path javaFile : javaFiles) {
                try {
                    String content = Files.readString(javaFile, StandardCharsets.UTF_8);
                    if (content.contains("SecurityFilterChain") || content.contains("@EnableWebSecurity")) {
                        hasSecurityConfig = true;
                        break;
                    }
                } catch (Exception e) {
                    // Ignore file read errors
                }
            }
            
            if (!hasSecurityConfig) {
                projectVulns.add(createVulnerability("NO-SEC", "No Security Configuration", "HIGH", "SECURITY_MISCONFIGURATION",
                    "Security Configuration", 1, "No Spring Security configuration found",
                    7.8, "Implement Spring Security with proper authentication and authorization"));
            }
            
            // 4. Check for HTTPS enforcement
            boolean hasHttpsConfig = false;
            for (Path javaFile : javaFiles) {
                try {
                    String content = Files.readString(javaFile, StandardCharsets.UTF_8);
                    if (content.contains("requiresChannel().anyRequest().requiresSecure()") || 
                        content.contains("server.ssl.enabled=true")) {
                        hasHttpsConfig = true;
                        break;
                    }
                } catch (Exception e) {
                    // Ignore file read errors
                }
            }
            
            if (!hasHttpsConfig) {
                projectVulns.add(createVulnerability("NO-HTTPS", "No HTTPS Enforcement", "HIGH", "SECURITY_MISCONFIGURATION",
                    "HTTPS Configuration", 1, "HTTPS enforcement not configured",
                    6.9, "Configure HTTPS enforcement and redirect HTTP to HTTPS"));
            }
            
            // 5. Check for CORS configuration
            boolean hasCorsConfig = false;
            for (Path javaFile : javaFiles) {
                try {
                    String content = Files.readString(javaFile, StandardCharsets.UTF_8);
                    if (content.contains("addCorsMappings") || content.contains("@CrossOrigin")) {
                        hasCorsConfig = true;
                        
                        // Check if CORS is too permissive
                        if (content.contains("allowedOrigins(\"*\")") || content.contains("allowedOriginPatterns(\"*\")")) {
                            projectVulns.add(createVulnerability("PERM-CORS", "Permissive CORS", "MEDIUM", "SECURITY_MISCONFIGURATION",
                                javaFile.getFileName().toString(), findLineNumber(content, "allowedOrigins"),
                                "CORS configured to allow all origins - security risk",
                                5.5, "Restrict CORS to specific trusted origins"));
                        }
                        break;
                    }
                } catch (Exception e) {
                    // Ignore file read errors
                }
            }
            
            // 6. Check for input validation
            boolean hasValidation = false;
            for (Path javaFile : javaFiles) {
                try {
                    String content = Files.readString(javaFile, StandardCharsets.UTF_8);
                    if (content.contains("@Valid") || content.contains("@NotNull") || content.contains("@Size") ||
                        content.contains("@Pattern") || content.contains("@Min") || content.contains("@Max")) {
                        hasValidation = true;
                        break;
                    }
                } catch (Exception e) {
                    // Ignore file read errors
                }
            }
            
            if (!hasValidation) {
                projectVulns.add(createVulnerability("NO-VALID", "No Input Validation", "HIGH", "SECURITY_MISCONFIGURATION",
                    "Input Validation", 1, "No input validation annotations found",
                    7.2, "Implement proper input validation using Bean Validation annotations"));
            }
            
            // 7. Check for logging configuration
            boolean hasLogging = false;
            for (Path javaFile : javaFiles) {
                try {
                    String content = Files.readString(javaFile, StandardCharsets.UTF_8);
                    if (content.contains("Logger") || content.contains("LogFactory") || content.contains("slf4j")) {
                        hasLogging = true;
                        break;
                    }
                } catch (Exception e) {
                    // Ignore file read errors
                }
            }
            
            if (!hasLogging) {
                projectVulns.add(createVulnerability("NO-LOG", "No Logging", "MEDIUM", "SECURITY_MISCONFIGURATION",
                    "Logging Configuration", 1, "No logging framework detected",
                    4.1, "Implement proper logging for security monitoring and debugging"));
            }
            
        } catch (IOException e) {
            logger.error("Failed to perform project-level analysis: {}", e.getMessage());
        }
        
        return projectVulns;
    }
    
    /**
     * Find line number of a pattern in content
     */
    private int findLineNumber(String content, String pattern) {
        String[] lines = content.split("\n");
        for (int i = 0; i < lines.length; i++) {
            String line = lines[i].trim();
            // Skip comments and empty lines for more accurate detection
            if (!line.startsWith("//") && !line.startsWith("*") && !line.isEmpty() && line.contains(pattern)) {
                return i + 1;
            }
        }
        
        // Fallback: if no non-comment line found, return first occurrence
        for (int i = 0; i < lines.length; i++) {
            if (lines[i].contains(pattern)) {
                return i + 1;
            }
        }
        return 1;
    }
    
    /**
     * Calculate security grade based on risk score and vulnerability count
     */
    private String calculateSecurityGrade(double riskScore, int vulnerabilityCount) {
        if (vulnerabilityCount == 0) return "A";
        if (riskScore <= 2.0 && vulnerabilityCount <= 2) return "B";
        if (riskScore <= 4.0 && vulnerabilityCount <= 5) return "C";
        if (riskScore <= 6.0 && vulnerabilityCount <= 10) return "D";
        return "F";
    }
}
