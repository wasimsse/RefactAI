package junit.extensions;

import junit.framework.Test;
import junit.framework.TestCase;
import junit.framework.TestSuite;
import java.util.List;
import java.util.ArrayList;
import java.util.Iterator;

/**
 * A TestSuite for active tests.
 * This class has several code smells that should be detected.
 */
public class ActiveTestSuite extends TestSuite {
    
    private static final int MAX_RETRIES = 3;
    private static final long TIMEOUT = 5000L;
    private static final String DEFAULT_NAME = "ActiveTestSuite";
    
    private List<Test> activeTests;
    private List<Test> failedTests;
    private boolean isRunning;
    private long startTime;
    private int retryCount;
    
    public ActiveTestSuite() {
        super();
        this.activeTests = new ArrayList<Test>();
        this.failedTests = new ArrayList<Test>();
        this.isRunning = false;
        this.startTime = 0L;
        this.retryCount = 0;
    }
    
    public ActiveTestSuite(String name) {
        super(name);
        this.activeTests = new ArrayList<Test>();
        this.failedTests = new ArrayList<Test>();
        this.isRunning = false;
        this.startTime = 0L;
        this.retryCount = 0;
    }
    
    public ActiveTestSuite(Class<? extends TestCase> theClass) {
        super(theClass);
        this.activeTests = new ArrayList<Test>();
        this.failedTests = new ArrayList<Test>();
        this.isRunning = false;
        this.startTime = 0L;
        this.retryCount = 0;
    }
    
    /**
     * This method is too long and has multiple responsibilities - CODE SMELL!
     */
    public void runActiveTests() {
        if (isRunning) {
            System.out.println("Test suite is already running");
            return;
        }
        
        isRunning = true;
        startTime = System.currentTimeMillis();
        
        // Initialize test lists
        activeTests.clear();
        failedTests.clear();
        
        // Add all tests to active list
        for (int i = 0; i < testCount(); i++) {
            Test test = testAt(i);
            if (test != null) {
                activeTests.add(test);
            }
        }
        
        // Run tests with retry logic
        while (!activeTests.isEmpty() && retryCount < MAX_RETRIES) {
            Iterator<Test> iterator = activeTests.iterator();
            while (iterator.hasNext()) {
                Test test = iterator.next();
                try {
                    long testStartTime = System.currentTimeMillis();
                    test.run(null);
                    long testEndTime = System.currentTimeMillis();
                    
                    if (testEndTime - testStartTime > TIMEOUT) {
                        System.out.println("Test " + test.toString() + " took too long");
                        failedTests.add(test);
                    }
                    
                    iterator.remove();
                } catch (Exception e) {
                    System.out.println("Test failed: " + test.toString() + " - " + e.getMessage());
                    failedTests.add(test);
                    iterator.remove();
                } catch (Error e) {
                    System.out.println("Test error: " + test.toString() + " - " + e.getMessage());
                    failedTests.add(test);
                    iterator.remove();
                }
            }
            
            if (!activeTests.isEmpty()) {
                retryCount++;
                System.out.println("Retrying failed tests, attempt " + retryCount);
                // Add failed tests back to active list for retry
                activeTests.addAll(failedTests);
                failedTests.clear();
            }
        }
        
        // Final cleanup and reporting
        long endTime = System.currentTimeMillis();
        long totalTime = endTime - startTime;
        
        System.out.println("Test execution completed in " + totalTime + "ms");
        System.out.println("Total tests: " + (activeTests.size() + failedTests.size()));
        System.out.println("Failed tests: " + failedTests.size());
        System.out.println("Retry attempts: " + retryCount);
        
        isRunning = false;
    }
    
    /**
     * This method has magic numbers and hardcoded values - CODE SMELL!
     */
    public boolean validateTestSuite() {
        if (testCount() == 0) {
            return false;
        }
        
        if (testCount() > 100) {
            System.out.println("Warning: Too many tests in suite");
            return false;
        }
        
        for (int i = 0; i < testCount(); i++) {
            Test test = testAt(i);
            if (test == null) {
                return false;
            }
            
            // Magic number: 50
            if (test.toString().length() > 50) {
                System.out.println("Test name too long: " + test.toString());
                return false;
            }
        }
        
        return true;
    }
    
    /**
     * This method has duplicate code - CODE SMELL!
     */
    public void setupTestEnvironment() {
        System.out.println("Setting up test environment...");
        System.out.println("Initializing test data...");
        System.out.println("Configuring test parameters...");
        System.out.println("Loading test fixtures...");
        System.out.println("Preparing test database...");
        System.out.println("Setting up mock objects...");
        System.out.println("Configuring test timeouts...");
        System.out.println("Initializing test listeners...");
        System.out.println("Setting up test isolation...");
        System.out.println("Preparing test cleanup...");
    }
    
    /**
     * This method also has duplicate code - CODE SMELL!
     */
    public void teardownTestEnvironment() {
        System.out.println("Tearing down test environment...");
        System.out.println("Cleaning up test data...");
        System.out.println("Resetting test parameters...");
        System.out.println("Removing test fixtures...");
        System.out.println("Cleaning test database...");
        System.out.println("Destroying mock objects...");
        System.out.println("Resetting test timeouts...");
        System.out.println("Removing test listeners...");
        System.out.println("Cleaning test isolation...");
        System.out.println("Finalizing test cleanup...");
    }
    
    /**
     * This method has too many parameters - CODE SMELL!
     */
    public void runTestWithOptions(String testName, boolean verbose, boolean parallel, 
                                  int timeout, int retries, boolean stopOnFailure, 
                                  boolean logResults, String outputFile) {
        System.out.println("Running test: " + testName);
        System.out.println("Verbose: " + verbose);
        System.out.println("Parallel: " + parallel);
        System.out.println("Timeout: " + timeout);
        System.out.println("Retries: " + retries);
        System.out.println("Stop on failure: " + stopOnFailure);
        System.out.println("Log results: " + logResults);
        System.out.println("Output file: " + outputFile);
    }
    
    /**
     * This method has a long parameter list and complex logic - CODE SMELL!
     */
    public void processTestResults(List<Test> tests, List<String> errors, 
                                  List<String> failures, int totalTests, 
                                  int passedTests, int failedTests, 
                                  long executionTime, boolean verbose) {
        if (tests == null || tests.isEmpty()) {
            System.out.println("No tests to process");
            return;
        }
        
        if (errors == null) {
            errors = new ArrayList<String>();
        }
        
        if (failures == null) {
            failures = new ArrayList<String>();
        }
        
        System.out.println("Processing " + totalTests + " test results");
        System.out.println("Passed: " + passedTests);
        System.out.println("Failed: " + failedTests);
        System.out.println("Execution time: " + executionTime + "ms");
        
        if (verbose) {
            System.out.println("Detailed results:");
            for (Test test : tests) {
                System.out.println("  Test: " + test.toString());
            }
            
            if (!errors.isEmpty()) {
                System.out.println("Errors:");
                for (String error : errors) {
                    System.out.println("  " + error);
                }
            }
            
            if (!failures.isEmpty()) {
                System.out.println("Failures:");
                for (String failure : failures) {
                    System.out.println("  " + failure);
                }
            }
        }
    }
    
    /**
     * This method has nested loops and complex logic - CODE SMELL!
     */
    public void analyzeTestCoverage(List<Test> tests, List<String> methods, 
                                   List<String> classes, boolean detailed) {
        if (tests == null || tests.isEmpty()) {
            return;
        }
        
        int totalMethods = 0;
        int coveredMethods = 0;
        int totalClasses = 0;
        int coveredClasses = 0;
        
        for (Test test : tests) {
            if (test instanceof TestCase) {
                TestCase testCase = (TestCase) test;
                String className = testCase.getClass().getName();
                
                if (classes.contains(className)) {
                    coveredClasses++;
                }
                totalClasses++;
                
                if (detailed) {
                    // This is a complex nested loop - CODE SMELL!
                    for (String method : methods) {
                        try {
                            testCase.getClass().getMethod(method);
                            totalMethods++;
                            
                            if (methods.contains(method)) {
                                coveredMethods++;
                            }
                        } catch (NoSuchMethodException e) {
                            // Method not found, continue
                        }
                    }
                }
            }
        }
        
        double classCoverage = totalClasses > 0 ? (double) coveredClasses / totalClasses : 0.0;
        double methodCoverage = totalMethods > 0 ? (double) coveredMethods / totalMethods : 0.0;
        
        System.out.println("Test Coverage Analysis:");
        System.out.println("Class Coverage: " + (classCoverage * 100) + "%");
        System.out.println("Method Coverage: " + (methodCoverage * 100) + "%");
    }
    
    /**
     * This method has too many responsibilities - CODE SMELL!
     */
    public void runComprehensiveTestSuite() {
        System.out.println("Starting comprehensive test suite execution...");
        
        // Setup phase
        setupTestEnvironment();
        
        // Validation phase
        if (!validateTestSuite()) {
            System.out.println("Test suite validation failed");
            return;
        }
        
        // Execution phase
        runActiveTests();
        
        // Analysis phase
        List<Test> allTests = new ArrayList<Test>();
        for (int i = 0; i < testCount(); i++) {
            allTests.add(testAt(i));
        }
        
        analyzeTestCoverage(allTests, new ArrayList<String>(), new ArrayList<String>(), true);
        
        // Cleanup phase
        teardownTestEnvironment();
        
        System.out.println("Comprehensive test suite execution completed");
    }
    
    // Getters and setters
    public List<Test> getActiveTests() {
        return activeTests;
    }
    
    public void setActiveTests(List<Test> activeTests) {
        this.activeTests = activeTests;
    }
    
    public List<Test> getFailedTests() {
        return failedTests;
    }
    
    public void setFailedTests(List<Test> failedTests) {
        this.failedTests = failedTests;
    }
    
    public boolean isRunning() {
        return isRunning;
    }
    
    public void setRunning(boolean running) {
        this.isRunning = running;
    }
    
    public long getStartTime() {
        return startTime;
    }
    
    public void setStartTime(long startTime) {
        this.startTime = startTime;
    }
    
    public int getRetryCount() {
        return retryCount;
    }
    
    public void setRetryCount(int retryCount) {
        this.retryCount = retryCount;
    }
}
