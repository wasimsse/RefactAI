package ai.refact.server.controller;

import ai.refact.server.model.EnhancedAnalysisRequest;
import ai.refact.server.model.EnhancedAnalysisResponse;
import ai.refact.server.model.RefactoringPlan;
import ai.refact.server.model.RefactoringStep;
import ai.refact.server.model.DependencyNode;
import ai.refact.server.service.EnhancedAnalysisService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.List;
import java.util.ArrayList;
import java.util.Map;
import java.util.HashMap;

@RestController
@RequestMapping("/api/workspace-enhanced-analysis")
@CrossOrigin(origins = {"http://localhost:4000", "http://localhost:3000"})
public class EnhancedAnalysisController {
    
    private static final Logger logger = LoggerFactory.getLogger(EnhancedAnalysisController.class);
    
    @Autowired
    private EnhancedAnalysisService enhancedAnalysisService;
    
    @PostMapping("/analyze-file")
    public ResponseEntity<EnhancedAnalysisResponse> analyzeFile(@RequestBody EnhancedAnalysisRequest request) {
        try {
            logger.info("Received enhanced analysis request for file: {}", request.getFilePath());
            
            EnhancedAnalysisResponse response = enhancedAnalysisService.performEnhancedAnalysis(
                request.getWorkspaceId(), 
                request.getFilePath()
            );
            
            logger.info("Enhanced analysis completed successfully");
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            logger.error("Error performing enhanced analysis", e);
            return ResponseEntity.internalServerError().build();
        }
    }
    
    @PostMapping("/generate-refactoring-plan")
    public ResponseEntity<RefactoringPlan> generateRefactoringPlan(@RequestBody Map<String, Object> request) {
        try {
            String workspaceId = (String) request.get("workspaceId");
            String filePath = (String) request.get("filePath");
            List<Map<String, Object>> codeSmells = (List<Map<String, Object>>) request.get("codeSmells");
            
            logger.info("Generating refactoring plan for file: {}", filePath);
            
            RefactoringPlan plan = enhancedAnalysisService.generateRefactoringPlan(workspaceId, filePath, codeSmells);
            
            logger.info("Refactoring plan generated successfully with {} steps", plan.getSteps().size());
            return ResponseEntity.ok(plan);
            
        } catch (Exception e) {
            logger.error("Error generating refactoring plan", e);
            return ResponseEntity.internalServerError().build();
        }
    }
    
    @PostMapping("/analyze-dependencies")
    public ResponseEntity<List<DependencyNode>> analyzeDependencies(@RequestBody Map<String, Object> request) {
        try {
            String workspaceId = (String) request.get("workspaceId");
            String filePath = (String) request.get("filePath");
            
            logger.info("Analyzing dependencies for file: {}", filePath);
            
            List<DependencyNode> dependencies = enhancedAnalysisService.analyzeDependencies(workspaceId, filePath);
            
            logger.info("Dependency analysis completed with {} nodes", dependencies.size());
            return ResponseEntity.ok(dependencies);
            
        } catch (Exception e) {
            logger.error("Error analyzing dependencies", e);
            return ResponseEntity.internalServerError().build();
        }
    }
    
    @PostMapping("/execute-refactoring")
    public ResponseEntity<Map<String, Object>> executeRefactoring(@RequestBody Map<String, Object> request) {
        try {
            String workspaceId = (String) request.get("workspaceId");
            String filePath = (String) request.get("filePath");
            List<Map<String, Object>> steps = (List<Map<String, Object>>) request.get("steps");
            
            logger.info("Executing refactoring for file: {} with {} steps", filePath, steps.size());
            
            Map<String, Object> result = enhancedAnalysisService.executeRefactoring(workspaceId, filePath, steps);
            
            logger.info("Refactoring execution completed successfully");
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            logger.error("Error executing refactoring", e);
            return ResponseEntity.internalServerError().build();
        }
    }
}