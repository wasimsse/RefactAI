package ai.refact.server.service;

import ai.refact.api.ProjectContext;
import ai.refact.api.BuildSystemType;
import ai.refact.api.FileInfo;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.io.InputStream;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.stream.Collectors;
import java.util.stream.Stream;
import java.util.Comparator;
import ai.refact.api.Assessment;
import ai.refact.api.ReasonEvidence;
import ai.refact.engine.FileMetricsService;
import ai.refact.api.FileInfo.FileMetrics;
import ai.refact.server.service.ComprehensiveCodeSmellDetector;

/**
 * Service for managing project uploads, Git cloning, and project context creation.
 * Now implements complete session isolation and no auto-loading.
 */
@Service
public class ProjectService {
    
    private static final Logger logger = LoggerFactory.getLogger(ProjectService.class);
    private final Path workspaceDir;
    private final Map<String, ProjectContext> projects = new HashMap<>();
    private final FileMetricsService fileMetricsService;
    private final RefactoringService refactoringService;
    private final ComprehensiveCodeSmellDetector comprehensiveCodeSmellDetector;
    private final String sessionId;
    
    public ProjectService(FileMetricsService fileMetricsService, RefactoringService refactoringService, ComprehensiveCodeSmellDetector comprehensiveCodeSmellDetector) {
        this.fileMetricsService = fileMetricsService;
        this.refactoringService = refactoringService;
        this.comprehensiveCodeSmellDetector = comprehensiveCodeSmellDetector;
        this.sessionId = UUID.randomUUID().toString();
        this.workspaceDir = Paths.get(System.getProperty("java.io.tmpdir"), "refactai-workspace", sessionId);
        createWorkspaceIfNeeded();
        logger.info("ProjectService initialized with session {} - starting with completely empty workspace", sessionId);
    }
    
    /**
     * Get current session ID for isolation
     */
    public String getSessionId() {
        return sessionId;
    }
    
    /**
     * Get all current projects in this session
     */
    public List<ProjectContext> getAllProjects() {
        return new ArrayList<>(projects.values());
    }
    
    private void createWorkspaceIfNeeded() {
        try {
            if (!Files.exists(workspaceDir)) {
                Files.createDirectories(workspaceDir);
                logger.info("Created isolated workspace directory for session {}: {}", sessionId, workspaceDir);
            }
        } catch (IOException e) {
            logger.error("Failed to create workspace directory for session {}", sessionId, e);
            throw new RuntimeException("Failed to initialize workspace", e);
        }
    }
    
    /**
     * Clear all projects and workspace for fresh start.
     * This completely removes all files and resets the state.
     */
    public void clearAllProjects() {
        logger.info("Clearing all projects for session: {}", sessionId);
        projects.clear();
        
        try {
            // Delete the entire session workspace directory
            if (Files.exists(workspaceDir)) {
                deleteDirectoryRecursively(workspaceDir);
                logger.info("Deleted entire workspace directory for session: {}", sessionId);
            }
            
            // Recreate empty workspace
            createWorkspaceIfNeeded();
            logger.info("All projects cleared and workspace reset for session: {}", sessionId);
        } catch (IOException e) {
            logger.error("Failed to clear projects for session: {}", sessionId, e);
        }
    }
    
    /**
     * Recursively delete directory and all contents
     */
    private void deleteDirectoryRecursively(Path path) throws IOException {
        if (Files.exists(path)) {
            Files.walk(path)
                .sorted(Comparator.reverseOrder())
                .forEach(file -> {
                    try {
                        Files.delete(file);
                    } catch (IOException e) {
                        logger.warn("Failed to delete file: {}", file, e);
                    }
                });
        }
    }
    
    /**
     * Upload and extract a ZIP file containing a Java project.
     * No automatic analysis - only file processing.
     */
    public ProjectContext uploadProject(MultipartFile file) throws IOException {
        String projectId = generateProjectId();
        Path projectDir = workspaceDir.resolve(projectId);
        
        // Save uploaded file
        Path zipFile = projectDir.resolve("upload.zip");
        Files.createDirectories(projectDir);
        file.transferTo(zipFile.toFile());
        
        // Extract ZIP file
        extractZipFile(zipFile, projectDir);
        
        // Create project context
        ProjectContext context = createProjectContext(projectId, projectDir);
        projects.put(projectId, context);
        
        // NO AUTOMATIC ASSESSMENT - User must explicitly trigger
        logger.info("Uploaded project {} for session {} with {} source files - NO AUTO-ANALYSIS", 
                   projectId, sessionId, context.sourceFiles().size());
        
        return context;
    }
    
    /**
     * Clone a Git repository and create project context.
     * No automatic analysis - only repository cloning.
     */
    public ProjectContext cloneGitRepository(String gitUrl, String branch) throws IOException {
        String projectId = generateProjectId();
        Path projectDir = workspaceDir.resolve(projectId);
        
        // Clone repository
        cloneRepository(gitUrl, branch, projectDir);
        
        // Create project context
        ProjectContext context = createProjectContext(projectId, projectDir);
        projects.put(projectId, context);
        
        // NO AUTOMATIC ASSESSMENT - User must explicitly trigger
        logger.info("Cloned Git repository {} to project {} for session {} with {} source files - NO AUTO-ANALYSIS", 
                   gitUrl, projectId, sessionId, context.sourceFiles().size());
        
        return context;
    }
    
    /**
     * Create project context from local directory.
     * No automatic analysis - only file copying.
     */
    public ProjectContext createLocalProject(String localPath) throws IOException {
        String projectId = generateProjectId();
        Path projectDir = workspaceDir.resolve(projectId);
        
        // Copy local directory
        Path sourcePath = Paths.get(localPath);
        if (!Files.exists(sourcePath)) {
            throw new IllegalArgumentException("Local path does not exist: " + localPath);
        }
        
        copyDirectory(sourcePath, projectDir);
        
        // Create project context
        ProjectContext context = createProjectContext(projectId, projectDir);
        projects.put(projectId, context);
        
        // NO AUTOMATIC ASSESSMENT - User must explicitly trigger
        logger.info("Created local project {} for session {} from {} with {} source files - NO AUTO-ANALYSIS", 
                   projectId, sessionId, localPath, context.sourceFiles().size());
        
        return context;
    }
    
    /**
     * Get project context by ID.
     * Only returns projects from current session.
     */
    public ProjectContext getProject(String projectId) {
        ProjectContext context = projects.get(projectId);
        if (context == null) {
            logger.warn("Project {} not found in current session {}", projectId, sessionId);
            throw new IllegalArgumentException("Project not found in current session: " + projectId);
        }
        return context;
    }

    /**
     * Get project directory path by ID.
     */
    public Path getProjectDirectory(String projectId) {
        return workspaceDir.resolve(projectId);
    }
    
    /**
     * List all projects for current session only.
     */
    public List<ProjectContext> listProjects() {
        logger.info("Listing {} projects for session: {}", projects.size(), sessionId);
        return new ArrayList<>(projects.values());
    }
    
    /**
     * Delete project and clean up files.
     */
    public void deleteProject(String projectId) throws IOException {
        ProjectContext context = projects.remove(projectId);
        if (context != null) {
            Path projectDir = workspaceDir.resolve(projectId);
            deleteDirectoryRecursively(projectDir);
            logger.info("Deleted project {} for session: {}", projectId, sessionId);
        }
    }
    
    /**
     * Get file content with proper error handling for binary files.
     */
    public String getFileContent(String projectId, String filePath) throws IOException {
        ProjectContext context = getProject(projectId);
        Path fullPath = context.root().resolve(filePath);
        
        if (!Files.exists(fullPath)) {
            throw new IOException("File not found: " + filePath);
        }
        
        // Check if file is binary
        if (isBinaryFile(fullPath)) {
            logger.warn("Skipping binary file: {}", filePath);
            return "[Binary file - content not displayed]";
        }
        
        try {
            // Try to read with UTF-8 first
            return Files.readString(fullPath, StandardCharsets.UTF_8);
        } catch (Exception e) {
            logger.warn("Failed to read file with UTF-8, trying ISO-8859-1: {}", filePath);
            try {
                // Fallback to ISO-8859-1
                return Files.readString(fullPath, StandardCharsets.ISO_8859_1);
            } catch (Exception e2) {
                logger.error("Failed to read file with any charset: {}", filePath, e2);
                return "[File content could not be read - encoding issues]";
            }
        }
    }
    
    /**
     * Check if file is binary by examining both extension and content
     */
    private boolean isBinaryFile(Path filePath) throws IOException {
        String fileName = filePath.getFileName().toString().toLowerCase();
        
        // Common binary file extensions
        Set<String> binaryExtensions = Set.of(
            ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg",
            ".pdf", ".doc", ".docx", ".xls", ".xlsx",
            ".zip", ".rar", ".7z", ".tar", ".gz",
            ".exe", ".dll", ".so", ".dylib", ".jar", ".war",
            ".class", ".o", ".a", ".lib"
        );
        
        // Check by extension first
        if (binaryExtensions.stream().anyMatch(fileName::endsWith)) {
            return true;
        }
        
        // Check file size - skip very large files
        long fileSize = Files.size(filePath);
        if (fileSize > 10 * 1024 * 1024) { // 10MB limit
            return true;
        }
        
        // Check content for binary patterns
        try (InputStream is = Files.newInputStream(filePath)) {
            byte[] buffer = new byte[Math.min((int) fileSize, 1024)];
            int bytesRead = is.read(buffer);
            
            if (bytesRead > 0) {
                // Check for null bytes or high percentage of non-printable characters
                int nullBytes = 0;
                int nonPrintable = 0;
                
                for (int i = 0; i < bytesRead; i++) {
                    byte b = buffer[i];
                    if (b == 0) {
                        nullBytes++;
                    } else if (b < 32 && b != 9 && b != 10 && b != 13) { // Not tab, LF, or CR
                        nonPrintable++;
                    }
                }
                
                // If more than 5% null bytes or 30% non-printable, consider it binary
                return (nullBytes > bytesRead * 0.05) || (nonPrintable > bytesRead * 0.30);
            }
        } catch (IOException e) {
            logger.warn("Failed to check file content for binary detection: {}", filePath, e);
            return true; // Assume binary if we can't read it
        }
        
        return false;
    }
    
    /**
     * Get project files with proper error handling.
     */
    public List<FileInfo> getProjectFiles(String projectId) throws IOException {
        ProjectContext context = getProject(projectId);
        List<FileInfo> files = new ArrayList<>();
        
        try {
            Files.walk(context.root())
                .filter(Files::isRegularFile)
                .filter(path -> {
                    try {
                        return !isBinaryFile(path);
                    } catch (IOException e) {
                        logger.warn("Failed to check if file is binary: {}", path, e);
                        return false; // Skip files we can't check
                    }
                })
                .forEach(path -> {
                    try {
                        FileInfo fileInfo = createFileInfo(context.root(), path);
                        files.add(fileInfo);
                    } catch (Exception e) {
                        logger.warn("Failed to process file: {}", path, e);
                    }
                });
        } catch (IOException e) {
            logger.error("Failed to walk project directory for project: {}", projectId, e);
            throw e;
        }
        
        logger.info("Processed {} files for project {} in session {}", files.size(), projectId, sessionId);
        return files;
    }
    
    /**
     * Create FileInfo object for a file.
     */
    private FileInfo createFileInfo(Path projectRoot, Path filePath) throws IOException {
        String relativePath = projectRoot.relativize(filePath).toString();
        String fileName = filePath.getFileName().toString();
        
        // Determine file type
        String fileType = determineFileType(fileName);
        
        // Get basic file info
        long size = Files.size(filePath);
        long lastModified = Files.getLastModifiedTime(filePath).toMillis();
        
        // Create metrics using actual analysis
        FileMetrics metrics = createFileMetrics(filePath);
        
        // Get code smells count using enhanced analysis for Java files
        Integer codeSmellsCount = null;
        logger.debug("File: {}, Type: {}, isJava: {}", fileName, fileType, fileName.endsWith(".java"));
        if (fileType.equals("SOURCE") && fileName.endsWith(".java")) {
            try {
                logger.info("Analyzing code smells for Java file: {}", fileName);
                logger.info("ComprehensiveCodeSmellDetector is null: {}", comprehensiveCodeSmellDetector == null);
                // Use enhanced analysis to get code smells count
                codeSmellsCount = getCodeSmellsCount(filePath);
                logger.info("Found {} code smells for file: {}", codeSmellsCount, fileName);
            } catch (Exception e) {
                logger.warn("Failed to get code smells for file: {}", filePath, e);
            }
        }
        
        return new FileInfo(
            filePath.toString(), // path
            fileName, // name
            relativePath, // relativePath
            FileInfo.FileType.valueOf(fileType), // type
            metrics, // metrics
            0, // findings (int)
            codeSmellsCount, // codeSmells (Integer)
            lastModified // lastModified
        );
    }
    
    /**
     * Create file metrics using actual analysis
     */
    private FileMetrics createFileMetrics(Path filePath) throws IOException {
        try {
            // Skip binary files
            if (isBinaryFile(filePath)) {
                logger.debug("Skipping binary file: {}", filePath);
                return new FileMetrics(0, 1, 1, 0, 0, 0, 0);
            }
            
            // Try to read file with proper charset handling
            List<String> lines;
            String content;
            try {
                // First try UTF-8
                lines = Files.readAllLines(filePath, StandardCharsets.UTF_8);
                content = String.join("\n", lines);
            } catch (Exception e) {
                logger.warn("Failed to read file with UTF-8, trying ISO-8859-1: {}", filePath);
                try {
                    // Fallback to ISO-8859-1
                    lines = Files.readAllLines(filePath, StandardCharsets.ISO_8859_1);
                    content = String.join("\n", lines);
                } catch (Exception e2) {
                    logger.warn("Failed to read file with any charset, using defaults: {}", filePath);
                    // Return default metrics for unreadable files
                    return new FileMetrics(1, 1, 1, 0, 0, 1, 1);
                }
            }
            
            // Calculate actual metrics
            int totalLines = lines.size();
            int codeLines = countCodeLines(lines);
            int commentLines = countCommentLines(lines);
            int blankLines = countBlankLines(lines);
            
            // Check if this is a Java file
            boolean isJavaFile = filePath.toString().toLowerCase().endsWith(".java");
            
            int cyclomaticComplexity = isJavaFile ? calculateCyclomaticComplexity(content) : 1;
            int cognitiveComplexity = isJavaFile ? calculateCognitiveComplexity(content) : 1;
            int classCount = isJavaFile ? countClasses(content) : 0;
            int methodCount = isJavaFile ? countMethods(content) : 0;
            
            return new FileMetrics(
                totalLines,
                cyclomaticComplexity,
                cognitiveComplexity,
                methodCount,
                classCount,
                commentLines,
                blankLines
            );
        } catch (Exception e) {
            logger.warn("Failed to calculate metrics for file: {}, using defaults", filePath, e);
            // Return basic metrics if analysis fails (avoid reading file again)
            return new FileMetrics(
                0, // lines of code
                1, // cyclomatic complexity
                1, // cognitive complexity
                0, // method count
                0, // class count
                0, // comment lines
                0  // blank lines
            );
        }
    }
    
    // Helper methods for metric calculations (copied from CodeAnalysisService)
    private int countCodeLines(List<String> lines) {
        return (int) lines.stream()
            .map(String::trim)
            .filter(line -> !line.isEmpty() && !line.startsWith("//") && !line.startsWith("/*"))
            .count();
    }
    
    private int countCommentLines(List<String> lines) {
        return (int) lines.stream()
            .map(String::trim)
            .filter(line -> line.startsWith("//") || line.startsWith("/*") || line.startsWith("*"))
            .count();
    }
    
    private int countBlankLines(List<String> lines) {
        return (int) lines.stream()
            .map(String::trim)
            .filter(String::isEmpty)
            .count();
    }
    
    private int calculateCyclomaticComplexity(String content) {
        int complexity = 1; // Base complexity
        
        String[] complexityKeywords = {"if", "while", "for", "case", "catch", "&&", "||", "?"};
        for (String keyword : complexityKeywords) {
            complexity += countOccurrences(content, keyword);
        }
        
        return complexity;
    }
    
    private int calculateCognitiveComplexity(String content) {
        // Simplified cognitive complexity calculation
        return calculateCyclomaticComplexity(content);
    }
    
    private int countClasses(String content) {
        int classCount = 0;
        String[] lines = content.split("\n");
        for (String line : lines) {
            String trimmed = line.trim();
            if (trimmed.matches(".*\\b(public|private|protected|static|final|abstract)?\\s+class\\s+\\w+.*")) {
                classCount++;
            } else if (trimmed.matches(".*\\b(public|private|protected|static|final|abstract)?\\s+(interface|enum)\\s+\\w+.*")) {
                classCount++;
            }
        }
        return classCount;
    }
    
    private int countMethods(String content) {
        int methodCount = 0;
        String[] lines = content.split("\n");
        for (String line : lines) {
            String trimmed = line.trim();
            if (trimmed.matches(".*\\b(public|private|protected|static|final|abstract|synchronized)\\s+\\w+\\s+\\w+\\s*\\(.*")) {
                methodCount++;
            } else if (trimmed.matches(".*\\b(public|private|protected)\\s+\\w+\\s*\\(.*")) {
                if (!trimmed.contains("=") && !trimmed.contains(";") && !trimmed.contains("void") && 
                    !trimmed.contains("int") && !trimmed.contains("String") && !trimmed.contains("boolean") &&
                    !trimmed.contains("double") && !trimmed.contains("float") && !trimmed.contains("long") &&
                    !trimmed.contains("char") && !trimmed.contains("byte") && !trimmed.contains("short")) {
                    methodCount++;
                }
            }
        }
        return methodCount;
    }
    
    private int countOccurrences(String text, String pattern) {
        int count = 0;
        int index = 0;
        while ((index = text.indexOf(pattern, index)) != -1) {
            count++;
            index += pattern.length();
        }
        return count;
    }

    /**
     * Determine file type based on extension
     */
    private String determineFileType(String fileName) {
        String lowerName = fileName.toLowerCase();
        if (lowerName.endsWith(".java")) return "SOURCE";
        if (lowerName.endsWith(".xml") || lowerName.endsWith(".pom") || 
            lowerName.endsWith(".properties") || lowerName.endsWith(".yml") || 
            lowerName.endsWith(".yaml")) return "CONFIG";
        if (lowerName.endsWith(".md") || lowerName.endsWith(".txt") || 
            lowerName.endsWith(".sql") || lowerName.endsWith(".js") || 
            lowerName.endsWith(".ts") || lowerName.endsWith(".css") || 
            lowerName.endsWith(".scss")) return "RESOURCE";
        return "RESOURCE";
    }
    
    private String generateProjectId() {
        return "project-" + UUID.randomUUID().toString().substring(0, 8);
    }
    
    private void extractZipFile(Path zipFile, Path targetDir) throws IOException {
        logger.info("Extracting ZIP file: {} to directory: {}", zipFile, targetDir);
        
        try (var fs = FileSystems.newFileSystem(zipFile, (ClassLoader) null)) {
            Path root = fs.getPath("/");
            Files.createDirectories(targetDir);
            
            // Log the contents of the ZIP file
            try (Stream<Path> zipContents = Files.walk(root)) {
                List<String> zipFiles = zipContents
                    .map(Path::toString)
                    .collect(Collectors.toList());
                logger.info("ZIP contents: {}", zipFiles);
            }
            
            copyDirectoryFromZip(root, targetDir);
            logger.info("ZIP extraction completed to: {}", targetDir);
            
            // Log the extracted contents
            try (Stream<Path> extractedContents = Files.walk(targetDir)) {
                List<String> extractedFiles = extractedContents
                    .map(targetDir::relativize)
                    .map(Path::toString)
                    .collect(Collectors.toList());
                logger.info("Extracted contents: {}", extractedFiles);
            }
        }
    }
    
    private void copyDirectoryFromZip(Path source, Path target) throws IOException {
        if (Files.isDirectory(source)) {
            Files.createDirectories(target);
            try (Stream<Path> paths = Files.list(source)) {
                for (Path path : paths.collect(Collectors.toList())) {
                    String fileName = path.getFileName().toString();
                    copyDirectoryFromZip(path, target.resolve(fileName));
                }
            }
        } else {
            Files.copy(source, target, StandardCopyOption.REPLACE_EXISTING);
            
            // Check if this is a nested ZIP file and extract it
            String fileName = source.getFileName().toString().toLowerCase();
            if (fileName.endsWith(".zip") || fileName.endsWith(".jar")) {
                logger.info("Found nested archive: {}, extracting...", fileName);
                try {
                    extractZipFile(target, target.getParent());
                    // Delete the original ZIP file after extraction
                    Files.deleteIfExists(target);
                } catch (Exception e) {
                    logger.warn("Failed to extract nested archive {}: {}", fileName, e.getMessage());
                }
            }
        }
    }
    
    private void cloneRepository(String gitUrl, String branch, Path targetDir) throws IOException {
        // Ensure target directory exists
        Files.createDirectories(targetDir.getParent());
        
        // Build git clone command with better error handling
        ProcessBuilder pb = new ProcessBuilder("git", "clone", "--depth", "1", "-b", branch, gitUrl, targetDir.toString());
        pb.redirectErrorStream(true);
        
        Process process = pb.start();
        try {
            // Read output for debugging
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    logger.debug("Git clone output: {}", line);
                }
            }
            
            int exitCode = process.waitFor();
            if (exitCode != 0) {
                // Try without branch specification if branch-specific clone fails
                logger.warn("Git clone with branch {} failed (exit code: {}), trying without branch specification", branch, exitCode);
                
                // Clean up failed attempt
                if (Files.exists(targetDir)) {
                    deleteDirectory(targetDir);
                }
                
                // Try cloning without branch specification
                ProcessBuilder pb2 = new ProcessBuilder("git", "clone", "--depth", "1", gitUrl, targetDir.toString());
                pb2.redirectErrorStream(true);
                Process process2 = pb2.start();
                
                try (BufferedReader reader = new BufferedReader(new InputStreamReader(process2.getInputStream()))) {
                    String line;
                    while ((line = reader.readLine()) != null) {
                        logger.debug("Git clone (no branch) output: {}", line);
                    }
                }
                
                int exitCode2 = process2.waitFor();
                if (exitCode2 != 0) {
                    throw new IOException("Git clone failed with exit code: " + exitCode2 + ". Please check if the repository URL is correct and accessible.");
                }
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new IOException("Git clone interrupted", e);
        }
    }
    
    private void deleteDirectory(Path dir) throws IOException {
        if (Files.exists(dir)) {
            Files.walk(dir)
                .sorted(Comparator.reverseOrder())
                .forEach(path -> {
                    try {
                        Files.delete(path);
                    } catch (IOException e) {
                        logger.warn("Failed to delete file: {}", path, e);
                    }
                });
        }
    }
    
    private ProjectContext createProjectContext(String projectId, Path projectDir) throws IOException {
        // Try different possible project structures
        Set<Path> sourceFiles = findJavaFilesInProject(projectDir, "src/main/java");
        Set<Path> testFiles = findJavaFilesInProject(projectDir, "src/test/java");
        BuildSystemType buildSystem = detectBuildSystem(projectDir);
        
        logger.info("Project context created for {}: {} source files, {} test files, build system: {}", 
                   projectId, sourceFiles.size(), testFiles.size(), buildSystem);
        
        // Log some example file paths for debugging
        if (!sourceFiles.isEmpty()) {
            logger.info("Source files found: {}", sourceFiles.stream().limit(5).map(Path::toString).collect(Collectors.joining(", ")));
        }
        if (!testFiles.isEmpty()) {
            logger.info("Test files found: {}", testFiles.stream().limit(5).map(Path::toString).collect(Collectors.joining(", ")));
        }
        
        return new ProjectContext(
            projectDir,
            sourceFiles,
            testFiles,
            Map.of("projectId", projectId),
            buildSystem
        );
    }
    
    /**
     * Get code smells count for a Java file using enhanced analysis
     */
    private Integer getCodeSmellsCount(Path filePath) {
        try {
            logger.info("Starting code smell analysis for file: {}", filePath);
            // Use comprehensive code smell detector with Path
            List<ai.refact.engine.model.CodeSmell> smells = comprehensiveCodeSmellDetector.detectAllCodeSmells(filePath);
            logger.info("Analysis completed for file: {}, found {} smells", filePath, smells != null ? smells.size() : 0);
            
            return smells != null ? smells.size() : 0;
        } catch (Exception e) {
            logger.error("Failed to analyze code smells for file: {}", filePath, e);
            return 0;
        }
    }
    
    private Set<Path> findJavaFilesInProject(Path projectDir, String relativePath) throws IOException {
        Set<Path> javaFiles = new HashSet<>();
        
        // Try direct path first
        Path directPath = projectDir.resolve(relativePath);
        if (Files.exists(directPath)) {
            javaFiles.addAll(findJavaFiles(directPath));
        }
        
        // Try looking in subdirectories (for cases where ZIP contains a project folder)
        try (Stream<Path> subdirs = Files.list(projectDir)) {
            for (Path subdir : subdirs.collect(Collectors.toList())) {
                if (Files.isDirectory(subdir)) {
                    Path subdirPath = subdir.resolve(relativePath);
                    if (Files.exists(subdirPath)) {
                        javaFiles.addAll(findJavaFiles(subdirPath));
                    }
                }
            }
        }
        
        // If no Java files found in standard locations, search recursively in the entire project
        if (javaFiles.isEmpty()) {
            logger.info("No Java files found in standard locations, searching recursively in project: {}", projectDir);
            javaFiles.addAll(findJavaFilesRecursively(projectDir));
        }
        
        return javaFiles;
    }
    
    private Set<Path> findJavaFiles(Path directory) throws IOException {
        if (!Files.exists(directory)) {
            return Set.of();
        }
        
        try (Stream<Path> paths = Files.walk(directory)) {
            return paths
                .filter(Files::isRegularFile)
                .filter(path -> path.toString().endsWith(".java"))
                .collect(Collectors.toSet());
        }
    }
    
    private Set<Path> findJavaFilesRecursively(Path projectDir) throws IOException {
        if (!Files.exists(projectDir)) {
            return Set.of();
        }
        
        Set<Path> javaFiles = new HashSet<>();
        
        try (Stream<Path> paths = Files.walk(projectDir)) {
            paths.filter(Files::isRegularFile)
                 .filter(path -> {
                     String fileName = path.toString().toLowerCase();
                     return fileName.endsWith(".java") && 
                            !fileName.contains("/target/") && 
                            !fileName.contains("/build/") &&
                            !fileName.contains("/.git/") &&
                            !fileName.contains("/node_modules/");
                 })
                 .forEach(javaFiles::add);
        }
        
        logger.info("Found {} Java files recursively in project: {}", javaFiles.size(), projectDir);
        return javaFiles;
    }
    
    private BuildSystemType detectBuildSystem(Path projectDir) {
        // Try direct path first
        if (Files.exists(projectDir.resolve("pom.xml"))) {
            return BuildSystemType.MAVEN;
        } else if (Files.exists(projectDir.resolve("build.gradle"))) {
            return BuildSystemType.GRADLE;
        }
        
        // Try looking in subdirectories
        try (Stream<Path> subdirs = Files.list(projectDir)) {
            for (Path subdir : subdirs.collect(Collectors.toList())) {
                if (Files.isDirectory(subdir)) {
                    if (Files.exists(subdir.resolve("pom.xml"))) {
                        return BuildSystemType.MAVEN;
                    } else if (Files.exists(subdir.resolve("build.gradle"))) {
                        return BuildSystemType.GRADLE;
                    }
                }
            }
        } catch (IOException e) {
            logger.warn("Error detecting build system: {}", e.getMessage());
        }
        
        return BuildSystemType.UNKNOWN;
    }
    
    private void copyDirectory(Path source, Path target) throws IOException {
        if (Files.isDirectory(source)) {
            Files.createDirectories(target);
            try (Stream<Path> paths = Files.list(source)) {
                for (Path path : paths.collect(Collectors.toList())) {
                    String fileName = path.getFileName().toString();
                    copyDirectory(path, target.resolve(fileName));
                }
            }
        } else {
            Files.copy(source, target, StandardCopyOption.REPLACE_EXISTING);
        }
    }
}

