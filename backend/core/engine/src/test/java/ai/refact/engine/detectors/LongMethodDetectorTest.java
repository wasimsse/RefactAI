package ai.refact.engine.detectors;

import ai.refact.api.ProjectContext;
import ai.refact.api.ReasonEvidence;
import ai.refact.api.ReasonCategory;
import ai.refact.api.Severity;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import static org.junit.jupiter.api.Assertions.*;

import java.nio.file.Path;
import java.util.Set;
import java.util.Map;
import java.util.List;
import java.util.stream.Collectors;

class LongMethodDetectorTest {
    
    private LongMethodDetector detector;
    private ProjectContext projectContext;
    
    @BeforeEach
    void setUp() {
        detector = new LongMethodDetector();
        projectContext = new ProjectContext(
            Path.of("/tmp/test-project"),
            Set.of(Path.of("src/main/java/Example.java")),
            Set.of(Path.of("src/test/java/ExampleTest.java")),
            Map.of(),
            null
        );
    }
    
    @Test
    void testDetectorId() {
        assertEquals("design.long-method", detector.id());
    }
    
    @Test
    void testDetectorCategory() {
        assertEquals(ReasonCategory.DESIGN, detector.category());
    }
    
    @Test
    void testIsApplicable() {
        assertTrue(detector.isApplicable(projectContext));
    }
    
    @Test
    void testDetect() {
        List<ReasonEvidence> evidences = detector.detect(projectContext)
            .collect(Collectors.toList());
        
        assertFalse(evidences.isEmpty(), "Should detect at least one long method");
        
        ReasonEvidence evidence = evidences.get(0);
        assertEquals("design.long-method", evidence.detectorId());
        assertEquals(Severity.MAJOR, evidence.severity());
        assertTrue(evidence.summary().contains("calculateTotal"));
        assertTrue(evidence.summary().contains("too long"));
        
        Map<String, Object> metrics = evidence.metrics();
        assertNotNull(metrics.get("lineCount"));
        assertNotNull(metrics.get("maxLines"));
    }
}
