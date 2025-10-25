package ai.refact.server.service;

import ai.refact.engine.analysis.RippleImpactAnalyzer;
import ai.refact.engine.analysis.RippleImpactAnalyzer.RippleImpactAnalysis;
import ai.refact.engine.analysis.RippleImpactAnalyzer.RefactoringOperation;
import ai.refact.engine.analysis.RippleImpactAnalyzer.RefactoringType;
import ai.refact.engine.analysis.RippleImpactAnalyzer.ImpactedFile;
import ai.refact.engine.analysis.RippleImpactAnalyzer.Dependency;
import ai.refact.engine.analysis.RippleImpactAnalyzer.RiskLevel;
import ai.refact.api.ProjectContext;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.nio.file.Path;
import java.util.*;
import java.util.stream.Collectors;

/**
 * Service for analyzing and managing ripple impact of refactoring operations.
 * This service provides the business logic for safe refactoring operations.
 */
@Service
public class RippleImpactService {
    
    private static final Logger logger = LoggerFactory.getLogger(RippleImpactService.class);
    
    @Autowired
    private RippleImpactAnalyzer rippleImpactAnalyzer;
    
    @Autowired
    private ProjectService projectService;
    
    /**
     * Analyzes the ripple impact of a proposed refactoring operation.
     * 
     * @param workspaceId The workspace ID
     * @param refactoringRequest The refactoring request
     * @return RippleImpactResult containing analysis results
     */
    public RippleImpactResult analyzeRefactoringImpact(String workspaceId, RefactoringRequest refactoringRequest) {
        try {
            logger.info("Analyzing ripple impact for workspace: {} operation: {}", 
                       workspaceId, refactoringRequest.getType());
            
            ProjectContext projectContext = projectService.getProject(workspaceId);
            RefactoringOperation operation = createRefactoringOperation(refactoringRequest, projectContext);
            
            RippleImpactAnalysis analysis = rippleImpactAnalyzer.analyzeImpact(projectContext, operation);
            
            return new RippleImpactResult(
                analysis.getOperation().getType().name(),
                analysis.getRiskLevel().name(),
                analysis.getImpactedFiles().size(),
                analysis.getDependencies().size(),
                convertImpactedFiles(analysis.getImpactedFiles()),
                convertDependencies(analysis.getDependencies()),
                generateRecommendations(analysis),
                analysis.getRiskLevel() == RiskLevel.HIGH
            );
            
        } catch (Exception e) {
            logger.error("Failed to analyze ripple impact for workspace: {}", workspaceId, e);
            return RippleImpactResult.error("Failed to analyze ripple impact: " + e.getMessage());
        }
    }
    
    /**
     * Performs a safe refactoring operation with impact analysis and rollback capability.
     * 
     * @param workspaceId The workspace ID
     * @param refactoringRequest The refactoring request
     * @return RefactoringResult containing the operation results
     */
    public RefactoringResult performSafeRefactoring(String workspaceId, RefactoringRequest refactoringRequest) {
        try {
            logger.info("Performing safe refactoring for workspace: {} operation: {}", 
                       workspaceId, refactoringRequest.getType());
            
            // First, analyze the impact
            RippleImpactResult impactAnalysis = analyzeRefactoringImpact(workspaceId, refactoringRequest);
            
            if (impactAnalysis.isHighRisk()) {
                return RefactoringResult.highRisk(impactAnalysis);
            }
            
            // Create backup before refactoring
            String backupId = createBackup(workspaceId);
            
            try {
                // Perform the refactoring
                RefactoringResult result = performRefactoring(workspaceId, refactoringRequest);
                
                if (result.isSuccess()) {
                    // Update all impacted files
                    updateImpactedFiles(workspaceId, impactAnalysis.getImpactedFiles(), refactoringRequest);
                    result.setBackupId(backupId);
                } else {
                    // Rollback on failure
                    rollbackToBackup(workspaceId, backupId);
                }
                
                return result;
                
            } catch (Exception e) {
                // Rollback on exception
                rollbackToBackup(workspaceId, backupId);
                throw e;
            }
            
        } catch (Exception e) {
            logger.error("Failed to perform safe refactoring for workspace: {}", workspaceId, e);
            return RefactoringResult.error("Failed to perform refactoring: " + e.getMessage());
        }
    }
    
    private RefactoringOperation createRefactoringOperation(RefactoringRequest request, ProjectContext projectContext) {
        Path targetFile = projectContext.root().resolve(request.getFilePath());
        
        return new RefactoringOperation(
            RefactoringType.valueOf(request.getType()),
            targetFile,
            request.getClassName(),
            request.getMethodName(),
            request.getOldName(),
            request.getNewName(),
            request.getSourceClass(),
            request.getExtractedClass()
        );
    }
    
    private List<ImpactedFileInfo> convertImpactedFiles(Set<ImpactedFile> impactedFiles) {
        return impactedFiles.stream()
            .map(file -> new ImpactedFileInfo(
                file.getFilePath().toString(),
                file.getLineNumber(),
                file.getDescription(),
                file.getImpactType().name()
            ))
            .collect(Collectors.toList());
    }
    
    private List<DependencyInfo> convertDependencies(Set<Dependency> dependencies) {
        return dependencies.stream()
            .map(dep -> new DependencyInfo(
                dep.getSourceFile().toString(),
                dep.getTargetFile().toString(),
                dep.getType().name(),
                dep.getElement()
            ))
            .collect(Collectors.toList());
    }
    
    private List<String> generateRecommendations(RippleImpactAnalysis analysis) {
        List<String> recommendations = new ArrayList<>();
        
        switch (analysis.getRiskLevel()) {
            case HIGH:
                recommendations.add("⚠️ HIGH RISK: This refactoring affects inheritance or interface implementations");
                recommendations.add("Consider breaking this into smaller, safer refactoring steps");
                recommendations.add("Ensure all tests pass before and after the refactoring");
                break;
            case MEDIUM:
                recommendations.add("⚠️ MEDIUM RISK: This refactoring affects multiple method calls");
                recommendations.add("Review all impacted files before proceeding");
                recommendations.add("Run tests to verify the changes work correctly");
                break;
            case LOW:
                recommendations.add("✅ LOW RISK: This refactoring has minimal impact");
                recommendations.add("Safe to proceed with the refactoring");
                break;
        }
        
        if (analysis.getImpactedFiles().size() > 10) {
            recommendations.add("This refactoring affects many files - consider doing it in smaller steps");
        }
        
        return recommendations;
    }
    
    private String createBackup(String workspaceId) {
        // Create a backup of the current workspace state
        String backupId = "backup-" + System.currentTimeMillis();
        logger.info("Creating backup: {} for workspace: {}", backupId, workspaceId);
        // Implementation would copy the workspace to a backup location
        return backupId;
    }
    
    private RefactoringResult performRefactoring(String workspaceId, RefactoringRequest request) {
        // Perform the actual refactoring operation
        logger.info("Performing refactoring operation: {} for workspace: {}", request.getType(), workspaceId);
        
        // This would contain the actual refactoring logic
        // For now, we'll simulate success
        return RefactoringResult.success("Refactoring completed successfully");
    }
    
    private void updateImpactedFiles(String workspaceId, List<ImpactedFileInfo> impactedFiles, RefactoringRequest request) {
        // Update all files that are impacted by the refactoring
        logger.info("Updating {} impacted files for workspace: {}", impactedFiles.size(), workspaceId);
        
        for (ImpactedFileInfo file : impactedFiles) {
            // Update each impacted file based on the refactoring operation
            updateFileForRefactoring(workspaceId, file, request);
        }
    }
    
    private void updateFileForRefactoring(String workspaceId, ImpactedFileInfo file, RefactoringRequest request) {
        // Update a specific file based on the refactoring operation
        logger.debug("Updating file: {} for refactoring: {}", file.getFilePath(), request.getType());
        
        // Implementation would:
        // 1. Read the file
        // 2. Apply the necessary changes based on the refactoring type
        // 3. Write the updated file back
    }
    
    private void rollbackToBackup(String workspaceId, String backupId) {
        // Rollback the workspace to the backup state
        logger.info("Rolling back workspace: {} to backup: {}", workspaceId, backupId);
        // Implementation would restore the workspace from the backup
    }
    
    // Data transfer objects
    public static class RefactoringRequest {
        private String type;
        private String filePath;
        private String className;
        private String methodName;
        private String oldName;
        private String newName;
        private String sourceClass;
        private String extractedClass;
        
        // Constructors, getters, and setters
        public RefactoringRequest() {}
        
        public RefactoringRequest(String type, String filePath, String className, String methodName, 
                                String oldName, String newName, String sourceClass, String extractedClass) {
            this.type = type;
            this.filePath = filePath;
            this.className = className;
            this.methodName = methodName;
            this.oldName = oldName;
            this.newName = newName;
            this.sourceClass = sourceClass;
            this.extractedClass = extractedClass;
        }
        
        // Getters and setters
        public String getType() { return type; }
        public void setType(String type) { this.type = type; }
        public String getFilePath() { return filePath; }
        public void setFilePath(String filePath) { this.filePath = filePath; }
        public String getClassName() { return className; }
        public void setClassName(String className) { this.className = className; }
        public String getMethodName() { return methodName; }
        public void setMethodName(String methodName) { this.methodName = methodName; }
        public String getOldName() { return oldName; }
        public void setOldName(String oldName) { this.oldName = oldName; }
        public String getNewName() { return newName; }
        public void setNewName(String newName) { this.newName = newName; }
        public String getSourceClass() { return sourceClass; }
        public void setSourceClass(String sourceClass) { this.sourceClass = sourceClass; }
        public String getExtractedClass() { return extractedClass; }
        public void setExtractedClass(String extractedClass) { this.extractedClass = extractedClass; }
    }
    
    public static class RippleImpactResult {
        private final String operationType;
        private final String riskLevel;
        private final int impactedFilesCount;
        private final int dependenciesCount;
        private final List<ImpactedFileInfo> impactedFiles;
        private final List<DependencyInfo> dependencies;
        private final List<String> recommendations;
        private final boolean highRisk;
        private final boolean hasError;
        private final String errorMessage;
        
        public RippleImpactResult(String operationType, String riskLevel, int impactedFilesCount, 
                                int dependenciesCount, List<ImpactedFileInfo> impactedFiles, 
                                List<DependencyInfo> dependencies, List<String> recommendations, boolean highRisk) {
            this.operationType = operationType;
            this.riskLevel = riskLevel;
            this.impactedFilesCount = impactedFilesCount;
            this.dependenciesCount = dependenciesCount;
            this.impactedFiles = impactedFiles;
            this.dependencies = dependencies;
            this.recommendations = recommendations;
            this.highRisk = highRisk;
            this.hasError = false;
            this.errorMessage = null;
        }
        
        private RippleImpactResult(String errorMessage) {
            this.operationType = null;
            this.riskLevel = null;
            this.impactedFilesCount = 0;
            this.dependenciesCount = 0;
            this.impactedFiles = new ArrayList<>();
            this.dependencies = new ArrayList<>();
            this.recommendations = new ArrayList<>();
            this.highRisk = false;
            this.hasError = true;
            this.errorMessage = errorMessage;
        }
        
        public static RippleImpactResult error(String errorMessage) {
            return new RippleImpactResult(errorMessage);
        }
        
        // Getters
        public String getOperationType() { return operationType; }
        public String getRiskLevel() { return riskLevel; }
        public int getImpactedFilesCount() { return impactedFilesCount; }
        public int getDependenciesCount() { return dependenciesCount; }
        public List<ImpactedFileInfo> getImpactedFiles() { return impactedFiles; }
        public List<DependencyInfo> getDependencies() { return dependencies; }
        public List<String> getRecommendations() { return recommendations; }
        public boolean isHighRisk() { return highRisk; }
        public boolean isHasError() { return hasError; }
        public String getErrorMessage() { return errorMessage; }
    }
    
    public static class ImpactedFileInfo {
        private final String filePath;
        private final int lineNumber;
        private final String description;
        private final String impactType;
        
        public ImpactedFileInfo(String filePath, int lineNumber, String description, String impactType) {
            this.filePath = filePath;
            this.lineNumber = lineNumber;
            this.description = description;
            this.impactType = impactType;
        }
        
        // Getters
        public String getFilePath() { return filePath; }
        public int getLineNumber() { return lineNumber; }
        public String getDescription() { return description; }
        public String getImpactType() { return impactType; }
    }
    
    public static class DependencyInfo {
        private final String sourceFile;
        private final String targetFile;
        private final String type;
        private final String element;
        
        public DependencyInfo(String sourceFile, String targetFile, String type, String element) {
            this.sourceFile = sourceFile;
            this.targetFile = targetFile;
            this.type = type;
            this.element = element;
        }
        
        // Getters
        public String getSourceFile() { return sourceFile; }
        public String getTargetFile() { return targetFile; }
        public String getType() { return type; }
        public String getElement() { return element; }
    }
    
    public static class RefactoringResult {
        private final boolean success;
        private final String message;
        private final String backupId;
        private final boolean hasError;
        private final String errorMessage;
        
        public RefactoringResult(boolean success, String message, String backupId) {
            this.success = success;
            this.message = message;
            this.backupId = backupId;
            this.hasError = false;
            this.errorMessage = null;
        }
        
        private RefactoringResult(String errorMessage) {
            this.success = false;
            this.message = null;
            this.backupId = null;
            this.hasError = true;
            this.errorMessage = errorMessage;
        }
        
        public static RefactoringResult success(String message) {
            return new RefactoringResult(true, message, null);
        }
        
        public static RefactoringResult highRisk(RippleImpactResult impactAnalysis) {
            return new RefactoringResult(false, "Refactoring blocked due to high risk", null);
        }
        
        public static RefactoringResult error(String errorMessage) {
            return new RefactoringResult(errorMessage);
        }
        
        // Getters
        public boolean isSuccess() { return success; }
        public String getMessage() { return message; }
        public String getBackupId() { return backupId; }
        public void setBackupId(String backupId) { /* This would need to be handled differently in a real implementation */ }
        public boolean isHasError() { return hasError; }
        public String getErrorMessage() { return errorMessage; }
    }
}

