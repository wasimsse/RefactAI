package com.example;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.DisplayName;
import static org.junit.jupiter.api.Assertions.*;

/**
 * Tests for the Calculator class.
 */
@DisplayName("Calculator Tests")
class CalculatorTest {
    
    private Calculator calculator;
    
    @BeforeEach
    void setUp() {
        calculator = new Calculator();
    }
    
    @Test
    @DisplayName("Should add numbers correctly")
    void testAdd() {
        double result = calculator.calculate("add", 1.0, 2.0, 3.0, 4.0, 5.0, 
                                          false, false, false, "decimal", 2, "");
        assertEquals(15.0, result, 0.001);
    }
    
    @Test
    @DisplayName("Should subtract numbers correctly")
    void testSubtract() {
        double result = calculator.calculate("subtract", 10.0, 2.0, 1.0, 1.0, 1.0, 
                                          false, false, false, "decimal", 2, "");
        assertEquals(5.0, result, 0.001);
    }
    
    @Test
    @DisplayName("Should multiply numbers correctly")
    void testMultiply() {
        double result = calculator.calculate("multiply", 2.0, 3.0, 4.0, 1.0, 1.0, 
                                          false, false, false, "decimal", 2, "");
        assertEquals(24.0, result, 0.001);
    }
    
    @Test
    @DisplayName("Should divide numbers correctly")
    void testDivide() {
        double result = calculator.calculate("divide", 100.0, 2.0, 2.0, 5.0, 1.0, 
                                          false, false, false, "decimal", 2, "");
        assertEquals(5.0, result, 0.001);
    }
    
    @Test
    @DisplayName("Should handle division by zero")
    void testDivideByZero() {
        double result = calculator.calculate("divide", 10.0, 0.0, 1.0, 1.0, 1.0, 
                                          false, false, false, "decimal", 2, "");
        assertEquals(0.0, result, 0.001);
        assertEquals("Division by zero", calculator.getErrorMessage());
    }
    
    @Test
    @DisplayName("Should calculate power correctly")
    void testPower() {
        double result = calculator.calculate("power", 2.0, 3.0, 1.0, 1.0, 1.0, 
                                          false, false, false, "decimal", 2, "");
        assertEquals(8.0, result, 0.001);
    }
    
    @Test
    @DisplayName("Should calculate square root correctly")
    void testSqrt() {
        double result = calculator.calculate("sqrt", 16.0, 1.0, 1.0, 1.0, 1.0, 
                                          false, false, false, "decimal", 2, "");
        assertEquals(4.0, result, 0.001);
    }
    
    @Test
    @DisplayName("Should format result correctly")
    void testFormatResult() {
        String formatted = calculator.formatResult(3.14159, "decimal", 2, "rad");
        assertEquals("3.14 rad", formatted);
    }
    
    @Test
    @DisplayName("Should format scientific notation correctly")
    void testFormatScientific() {
        String formatted = calculator.formatResult(1234567.89, "scientific", 2, "");
        assertTrue(formatted.contains("e+"));
    }
    
    @Test
    @DisplayName("Should handle unknown operation")
    void testUnknownOperation() {
        double result = calculator.calculate("unknown", 1.0, 2.0, 3.0, 4.0, 5.0, 
                                          false, false, false, "decimal", 2, "");
        assertEquals(0.0, result, 0.001);
        assertEquals("Unknown operation: unknown", calculator.getErrorMessage());
    }
    
    @Test
    @DisplayName("Should update operation count")
    void testOperationCount() {
        assertEquals(0, calculator.getOperationCount());
        
        calculator.calculate("add", 1.0, 2.0, 3.0, 4.0, 5.0, 
                           false, false, false, "decimal", 2, "");
        
        assertEquals(1, calculator.getOperationCount());
    }
    
    @Test
    @DisplayName("Should save to history when requested")
    void testSaveToHistory() {
        calculator.calculate("add", 1.0, 2.0, 3.0, 4.0, 5.0, 
                           false, false, true, "decimal", 2, "");
        
        assertEquals(1, calculator.getHistory().size());
        assertEquals(15.0, calculator.getHistory().get(0), 0.001);
    }
    
    @Test
    @DisplayName("Should round result when requested")
    void testRoundResult() {
        double result = calculator.calculate("divide", 10.0, 3.0, 1.0, 1.0, 1.0, 
                                          false, true, false, "decimal", 2, "");
        assertEquals(3.33, result, 0.001);
    }
}
