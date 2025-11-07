package ai.refact.server;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.web.servlet.WebMvcAutoConfiguration;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Bean;
import ai.refact.engine.AssessmentEngine;
import ai.refact.server.service.ProjectService;
import ai.refact.engine.FileMetricsService;
import ai.refact.server.service.RefactoringService;
import ai.refact.server.service.ComprehensiveCodeSmellDetector;
import ai.refact.server.service.CodeAnalysisService;
import ai.refact.engine.EnhancedCodeAnalysisService;
import ai.refact.api.ReasonDetector;
import ai.refact.engine.detectors.LongMethodDetector;
import ai.refact.engine.detectors.CodeSmellDetector;
import ai.refact.engine.detectors.SecurityVulnerabilityDetector;
import ai.refact.engine.analysis.RippleImpactAnalyzer;
import java.util.List;
import java.util.Arrays;

/**
 * Main Spring Boot application for RefactAI Server.
 */
@SpringBootApplication
@ComponentScan(basePackages = {"ai.refact.server", "ai.refact.engine"})
@org.springframework.scheduling.annotation.EnableScheduling
public class RefactAIServerApplication {

    public static void main(String[] args) {
        SpringApplication.run(RefactAIServerApplication.class, args);
    }

    // AssessmentEngine is now created by component scanning with @Service annotation
    // All ReasonDetector components will be automatically discovered and injected

    @Bean
    public ProjectService projectService(FileMetricsService fileMetricsService, RefactoringService refactoringService, ComprehensiveCodeSmellDetector comprehensiveCodeSmellDetector) {
        return new ProjectService(fileMetricsService, refactoringService, comprehensiveCodeSmellDetector);
    }

    @Bean
    public RefactoringService refactoringService(AssessmentEngine assessmentEngine) {
        return new RefactoringService(assessmentEngine);
    }

    @Bean
    public CodeAnalysisService codeAnalysisService() {
        return new CodeAnalysisService();
    }

    @Bean
    public CodeSmellDetector codeSmellDetector() {
        return new CodeSmellDetector();
    }
    
    @Bean
    public SecurityVulnerabilityDetector securityVulnerabilityDetector() {
        return new SecurityVulnerabilityDetector();
    }
    
    @Bean
    public RippleImpactAnalyzer rippleImpactAnalyzer() {
        return new RippleImpactAnalyzer();
    }
    
    // Removed manual bean creation for EnhancedCodeAnalysisService and FileMetricsService
    // They are now created by component scanning with @Service annotation
}
