package com.example;

import java.util.List;
import java.util.ArrayList;
import java.util.Map;
import java.util.HashMap;

/**
 * A calculator class with some code smells for testing refactoring tools.
 * This class demonstrates several issues:
 * - Long method (calculate method)
 * - God class (too many responsibilities)
 * - Feature envy (some methods use other objects more than their own)
 * - Data clumps (repeated parameter groups)
 */
public class Calculator {
    
    // Too many fields - potential god class smell
    private double result;
    private List<Double> history;
    private Map<String, Double> variables;
    private String lastOperation;
    private int operationCount;
    private double totalSum;
    private double totalProduct;
    private double average;
    private double minValue;
    private double maxValue;
    private boolean isEnabled;
    private String displayFormat;
    private int precision;
    private String unit;
    private boolean scientificMode;
    private double memory;
    private String errorMessage;
    private long lastCalculationTime;
    
    public Calculator() {
        this.history = new ArrayList<>();
        this.variables = new HashMap<>();
        this.isEnabled = true;
        this.displayFormat = "decimal";
        this.precision = 2;
        this.unit = "";
        this.scientificMode = false;
        this.memory = 0.0;
        this.errorMessage = "";
        this.lastCalculationTime = System.currentTimeMillis();
    }
    
    /**
     * Long method - violates single responsibility principle
     * This method does too many things and should be refactored
     */
    public double calculate(String operation, double a, double b, double c, double d, double e, 
                          boolean useScientific, boolean roundResult, boolean saveToHistory,
                          String format, int precision, String unit) {
        
        if (!isEnabled) {
            throw new IllegalStateException("Calculator is disabled");
        }
        
        double result = 0.0;
        
        // Complex calculation logic that should be extracted
        switch (operation.toLowerCase()) {
            case "add":
                result = a + b + c + d + e;
                if (useScientific) {
                    result = Math.pow(result, 2);
                }
                break;
            case "subtract":
                result = a - b - c - d - e;
                if (useScientific) {
                    result = Math.sqrt(Math.abs(result));
                }
                break;
            case "multiply":
                result = a * b * c * d * e;
                if (useScientific) {
                    result = Math.log(result);
                }
                break;
            case "divide":
                if (b == 0 || c == 0 || d == 0 || e == 0) {
                    errorMessage = "Division by zero";
                    return 0.0;
                }
                result = a / b / c / d / e;
                if (useScientific) {
                    result = Math.exp(result);
                }
                break;
            case "power":
                result = Math.pow(a, b);
                if (useScientific) {
                    result = Math.sin(result) + Math.cos(result);
                }
                break;
            case "sqrt":
                result = Math.sqrt(a);
                if (useScientific) {
                    result = Math.atan(result);
                }
                break;
            case "log":
                result = Math.log(a);
                if (useScientific) {
                    result = Math.tanh(result);
                }
                break;
            case "sin":
                result = Math.sin(a);
                if (useScientific) {
                    result = Math.asin(result);
                }
                break;
            case "cos":
                result = Math.cos(a);
                if (useScientific) {
                    result = Math.acos(result);
                }
                break;
            case "tan":
                result = Math.tan(a);
                if (useScientific) {
                    result = Math.atan(result);
                }
                break;
            default:
                errorMessage = "Unknown operation: " + operation;
                return 0.0;
        }
        
        // Rounding logic
        if (roundResult) {
            double factor = Math.pow(10, precision);
            result = Math.round(result * factor) / factor;
        }
        
        // Update statistics
        updateStatistics(result);
        
        // Save to history
        if (saveToHistory) {
            history.add(result);
        }
        
        // Update last operation
        lastOperation = operation;
        operationCount++;
        lastCalculationTime = System.currentTimeMillis();
        
        this.result = result;
        return result;
    }
    
    /**
     * Feature envy - this method uses String operations more than Calculator operations
     */
    public String formatResult(double value, String format, int precision, String unit) {
        StringBuilder sb = new StringBuilder();
        
        // This method is more interested in String operations than Calculator state
        if (format.equals("scientific")) {
            sb.append(String.format("%." + precision + "e", value));
        } else if (format.equals("hex")) {
            sb.append("0x").append(Long.toHexString((long) value));
        } else if (format.equals("binary")) {
            sb.append("0b").append(Long.toBinaryString((long) value));
        } else {
            sb.append(String.format("%." + precision + "f", value));
        }
        
        if (!unit.isEmpty()) {
            sb.append(" ").append(unit);
        }
        
        return sb.toString();
    }
    
    /**
     * Data clumps - repeated parameter groups
     */
    public void setDisplaySettings(String format, int precision, String unit) {
        this.displayFormat = format;
        this.precision = precision;
        this.unit = unit;
    }
    
    public void setScientificSettings(String format, int precision, String unit) {
        this.scientificMode = true;
        this.displayFormat = format;
        this.precision = precision;
        this.unit = unit;
    }
    
    public void setMemorySettings(String format, int precision, String unit) {
        this.memory = 0.0;
        this.displayFormat = format;
        this.precision = precision;
        this.unit = unit;
    }
    
    // Getters and setters
    public double getResult() { return result; }
    public void setResult(double result) { this.result = result; }
    
    public List<Double> getHistory() { return history; }
    public void setHistory(List<Double> history) { this.history = history; }
    
    public Map<String, Double> getVariables() { return variables; }
    public void setVariables(Map<String, Double> variables) { this.variables = variables; }
    
    public String getLastOperation() { return lastOperation; }
    public void setLastOperation(String lastOperation) { this.lastOperation = lastOperation; }
    
    public int getOperationCount() { return operationCount; }
    public void setOperationCount(int operationCount) { this.operationCount = operationCount; }
    
    public double getTotalSum() { return totalSum; }
    public void setTotalSum(double totalSum) { this.totalSum = totalSum; }
    
    public double getTotalProduct() { return totalProduct; }
    public void setTotalProduct(double totalProduct) { this.totalProduct = totalProduct; }
    
    public double getAverage() { return average; }
    public void setAverage(double average) { this.average = average; }
    
    public double getMinValue() { return minValue; }
    public void setMinValue(double minValue) { this.minValue = minValue; }
    
    public double getMaxValue() { return maxValue; }
    public void setMaxValue(double maxValue) { this.maxValue = maxValue; }
    
    public boolean isEnabled() { return isEnabled; }
    public void setEnabled(boolean enabled) { isEnabled = enabled; }
    
    public String getDisplayFormat() { return displayFormat; }
    public void setDisplayFormat(String displayFormat) { this.displayFormat = displayFormat; }
    
    public int getPrecision() { return precision; }
    public void setPrecision(int precision) { this.precision = precision; }
    
    public String getUnit() { return unit; }
    public void setUnit(String unit) { this.unit = unit; }
    
    public boolean isScientificMode() { return scientificMode; }
    public void setScientificMode(boolean scientificMode) { this.scientificMode = scientificMode; }
    
    public double getMemory() { return memory; }
    public void setMemory(double memory) { this.memory = memory; }
    
    public String getErrorMessage() { return errorMessage; }
    public void setErrorMessage(String errorMessage) { this.errorMessage = errorMessage; }
    
    public long getLastCalculationTime() { return lastCalculationTime; }
    public void setLastCalculationTime(long lastCalculationTime) { this.lastCalculationTime = lastCalculationTime; }
    
    private void updateStatistics(double value) {
        totalSum += value;
        if (operationCount == 0) {
            totalProduct = value;
            average = value;
            minValue = value;
            maxValue = value;
        } else {
            totalProduct *= value;
            average = totalSum / (operationCount + 1);
            minValue = Math.min(minValue, value);
            maxValue = Math.max(maxValue, value);
        }
    }
}
