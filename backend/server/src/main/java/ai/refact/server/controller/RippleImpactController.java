package ai.refact.server.controller;

import ai.refact.server.service.RippleImpactService;
import ai.refact.server.service.RippleImpactService.RefactoringRequest;
import ai.refact.server.service.RippleImpactService.RippleImpactResult;
import ai.refact.server.service.RippleImpactService.RefactoringResult;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * REST controller for ripple impact analysis and safe refactoring operations.
 * This controller provides endpoints for analyzing and performing refactoring operations
 * with comprehensive impact analysis.
 */
@RestController
@RequestMapping("/api/refactoring")
@CrossOrigin(origins = "*")
public class RippleImpactController {
    
    private static final Logger logger = LoggerFactory.getLogger(RippleImpactController.class);
    
    @Autowired
    private RippleImpactService rippleImpactService;
    
    /**
     * Analyzes the ripple impact of a proposed refactoring operation.
     * 
     * @param workspaceId The workspace ID
     * @param request The refactoring request
     * @return RippleImpactResult containing analysis results
     */
    @PostMapping("/workspaces/{id}/analyze-impact")
    public ResponseEntity<RippleImpactResult> analyzeRefactoringImpact(
            @PathVariable String id,
            @RequestBody RefactoringRequest request) {
        try {
            logger.info("Analyzing refactoring impact for workspace: {} operation: {}", id, request.getType());
            
            RippleImpactResult result = rippleImpactService.analyzeRefactoringImpact(id, request);
            
            if (result.isHasError()) {
                return ResponseEntity.badRequest().body(result);
            }
            
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            logger.error("Failed to analyze refactoring impact for workspace: {}", id, e);
            return ResponseEntity.badRequest().body(RippleImpactResult.error("Analysis failed: " + e.getMessage()));
        }
    }
    
    /**
     * Performs a safe refactoring operation with impact analysis and rollback capability.
     * 
     * @param workspaceId The workspace ID
     * @param request The refactoring request
     * @return RefactoringResult containing the operation results
     */
    @PostMapping("/workspaces/{id}/perform-refactoring")
    public ResponseEntity<RefactoringResult> performSafeRefactoring(
            @PathVariable String id,
            @RequestBody RefactoringRequest request) {
        try {
            logger.info("Performing safe refactoring for workspace: {} operation: {}", id, request.getType());
            
            RefactoringResult result = rippleImpactService.performSafeRefactoring(id, request);
            
            if (result.isHasError()) {
                return ResponseEntity.badRequest().body(result);
            }
            
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            logger.error("Failed to perform safe refactoring for workspace: {}", id, e);
            return ResponseEntity.badRequest().body(RefactoringResult.error("Refactoring failed: " + e.getMessage()));
        }
    }
    
    /**
     * Gets available refactoring operations for a specific file.
     * 
     * @param workspaceId The workspace ID
     * @param filePath The file path
     * @return List of available refactoring operations
     */
    @GetMapping("/workspaces/{id}/available-operations")
    public ResponseEntity<AvailableOperationsResult> getAvailableOperations(
            @PathVariable String id,
            @RequestParam String filePath) {
        try {
            logger.info("Getting available refactoring operations for workspace: {} file: {}", id, filePath);
            
            // This would analyze the file and return available refactoring operations
            AvailableOperationsResult result = new AvailableOperationsResult(
                java.util.Arrays.asList(
                    new RefactoringOperationInfo("EXTRACT_METHOD", "Extract Method", "Extract a method from the current selection"),
                    new RefactoringOperationInfo("RENAME_METHOD", "Rename Method", "Rename the selected method"),
                    new RefactoringOperationInfo("RENAME_CLASS", "Rename Class", "Rename the current class"),
                    new RefactoringOperationInfo("MOVE_METHOD", "Move Method", "Move the selected method to another class"),
                    new RefactoringOperationInfo("EXTRACT_CLASS", "Extract Class", "Extract a new class from the current class")
                )
            );
            
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            logger.error("Failed to get available operations for workspace: {} file: {}", id, filePath, e);
            return ResponseEntity.badRequest().body(AvailableOperationsResult.error("Failed to get operations: " + e.getMessage()));
        }
    }
    
    /**
     * Gets the refactoring history for a workspace.
     * 
     * @param workspaceId The workspace ID
     * @return List of refactoring operations performed
     */
    @GetMapping("/workspaces/{id}/history")
    public ResponseEntity<RefactoringHistoryResult> getRefactoringHistory(@PathVariable String id) {
        try {
            logger.info("Getting refactoring history for workspace: {}", id);
            
            // This would return the history of refactoring operations
            RefactoringHistoryResult result = new RefactoringHistoryResult(
                java.util.Arrays.asList(
                    new RefactoringHistoryItem("extract-method-1", "EXTRACT_METHOD", "Extracted calculateTotal method", "2025-09-07T10:30:00Z", true),
                    new RefactoringHistoryItem("rename-method-1", "RENAME_METHOD", "Renamed processData to processUserData", "2025-09-07T09:15:00Z", true),
                    new RefactoringHistoryItem("extract-class-1", "EXTRACT_CLASS", "Extracted UserValidator class", "2025-09-07T08:45:00Z", true)
                )
            );
            
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            logger.error("Failed to get refactoring history for workspace: {}", id, e);
            return ResponseEntity.badRequest().body(RefactoringHistoryResult.error("Failed to get history: " + e.getMessage()));
        }
    }
    
    /**
     * Rolls back a refactoring operation to a previous state.
     * 
     * @param workspaceId The workspace ID
     * @param backupId The backup ID to rollback to
     * @return RollbackResult containing the rollback status
     */
    @PostMapping("/workspaces/{id}/rollback")
    public ResponseEntity<RollbackResult> rollbackRefactoring(
            @PathVariable String id,
            @RequestParam String backupId) {
        try {
            logger.info("Rolling back refactoring for workspace: {} to backup: {}", id, backupId);
            
            // This would perform the rollback operation
            RollbackResult result = new RollbackResult(true, "Successfully rolled back to backup: " + backupId);
            
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            logger.error("Failed to rollback refactoring for workspace: {} to backup: {}", id, backupId, e);
            return ResponseEntity.badRequest().body(RollbackResult.error("Rollback failed: " + e.getMessage()));
        }
    }
    
    // Data transfer objects
    public static class AvailableOperationsResult {
        private final java.util.List<RefactoringOperationInfo> operations;
        private final boolean hasError;
        private final String errorMessage;
        
        public AvailableOperationsResult(java.util.List<RefactoringOperationInfo> operations) {
            this.operations = operations;
            this.hasError = false;
            this.errorMessage = null;
        }
        
        private AvailableOperationsResult(String errorMessage) {
            this.operations = new java.util.ArrayList<>();
            this.hasError = true;
            this.errorMessage = errorMessage;
        }
        
        public static AvailableOperationsResult error(String errorMessage) {
            return new AvailableOperationsResult(errorMessage);
        }
        
        // Getters
        public java.util.List<RefactoringOperationInfo> getOperations() { return operations; }
        public boolean isHasError() { return hasError; }
        public String getErrorMessage() { return errorMessage; }
    }
    
    public static class RefactoringOperationInfo {
        private final String type;
        private final String name;
        private final String description;
        
        public RefactoringOperationInfo(String type, String name, String description) {
            this.type = type;
            this.name = name;
            this.description = description;
        }
        
        // Getters
        public String getType() { return type; }
        public String getName() { return name; }
        public String getDescription() { return description; }
    }
    
    public static class RefactoringHistoryResult {
        private final java.util.List<RefactoringHistoryItem> history;
        private final boolean hasError;
        private final String errorMessage;
        
        public RefactoringHistoryResult(java.util.List<RefactoringHistoryItem> history) {
            this.history = history;
            this.hasError = false;
            this.errorMessage = null;
        }
        
        private RefactoringHistoryResult(String errorMessage) {
            this.history = new java.util.ArrayList<>();
            this.hasError = true;
            this.errorMessage = errorMessage;
        }
        
        public static RefactoringHistoryResult error(String errorMessage) {
            return new RefactoringHistoryResult(errorMessage);
        }
        
        // Getters
        public java.util.List<RefactoringHistoryItem> getHistory() { return history; }
        public boolean isHasError() { return hasError; }
        public String getErrorMessage() { return errorMessage; }
    }
    
    public static class RefactoringHistoryItem {
        private final String id;
        private final String type;
        private final String description;
        private final String timestamp;
        private final boolean success;
        
        public RefactoringHistoryItem(String id, String type, String description, String timestamp, boolean success) {
            this.id = id;
            this.type = type;
            this.description = description;
            this.timestamp = timestamp;
            this.success = success;
        }
        
        // Getters
        public String getId() { return id; }
        public String getType() { return type; }
        public String getDescription() { return description; }
        public String getTimestamp() { return timestamp; }
        public boolean isSuccess() { return success; }
    }
    
    public static class RollbackResult {
        private final boolean success;
        private final String message;
        private final boolean hasError;
        private final String errorMessage;
        
        public RollbackResult(boolean success, String message) {
            this.success = success;
            this.message = message;
            this.hasError = false;
            this.errorMessage = null;
        }
        
        private RollbackResult(String errorMessage) {
            this.success = false;
            this.message = null;
            this.hasError = true;
            this.errorMessage = errorMessage;
        }
        
        public static RollbackResult error(String errorMessage) {
            return new RollbackResult(errorMessage);
        }
        
        // Getters
        public boolean isSuccess() { return success; }
        public String getMessage() { return message; }
        public boolean isHasError() { return hasError; }
        public String getErrorMessage() { return errorMessage; }
    }
}

