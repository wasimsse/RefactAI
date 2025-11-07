package org.junit;

import java.util.List;
import java.util.ArrayList;

/**
 * A set of assertion methods useful for writing tests.
 * Only failed assertions are recorded.
 */
public class Assert {
    
    private static final String DEFAULT_MESSAGE = "";
    private static final int MAX_LENGTH = 1000;
    
    /**
     * Asserts that a condition is true. If it isn't it throws
     * an AssertionFailedError with the given message.
     */
    public static void assertTrue(String message, boolean condition) {
        if (!condition) {
            fail(message);
        }
    }
    
    /**
     * Asserts that a condition is true. If it isn't it throws
     * an AssertionFailedError.
     */
    public static void assertTrue(boolean condition) {
        assertTrue(DEFAULT_MESSAGE, condition);
    }
    
    /**
     * Asserts that a condition is false. If it isn't it throws
     * an AssertionFailedError with the given message.
     */
    public static void assertFalse(String message, boolean condition) {
        assertTrue(message, !condition);
    }
    
    /**
     * Asserts that a condition is false. If it isn't it throws
     * an AssertionFailedError.
     */
    public static void assertFalse(boolean condition) {
        assertFalse(DEFAULT_MESSAGE, condition);
    }
    
    /**
     * Fails a test with the given message.
     */
    public static void fail(String message) {
        if (message == null) {
            throw new AssertionFailedError();
        }
        throw new AssertionFailedError(message);
    }
    
    /**
     * Fails a test with no message.
     */
    public static void fail() {
        fail(null);
    }
    
    /**
     * Asserts that two objects are equal. If they are not,
     * an AssertionFailedError is thrown with the given message.
     */
    public static void assertEquals(String message, Object expected, Object actual) {
        if (expected == null && actual == null) {
            return;
        }
        if (expected != null && expected.equals(actual)) {
            return;
        }
        failNotEquals(message, expected, actual);
    }
    
    /**
     * Asserts that two objects are equal. If they are not,
     * an AssertionFailedError is thrown.
     */
    public static void assertEquals(Object expected, Object actual) {
        assertEquals(DEFAULT_MESSAGE, expected, actual);
    }
    
    /**
     * Asserts that two Strings are equal. If they are not,
     * an AssertionFailedError is thrown with the given message.
     */
    public static void assertEquals(String message, String expected, String actual) {
        if (expected == null && actual == null) {
            return;
        }
        if (expected != null && expected.equals(actual)) {
            return;
        }
        failNotEquals(message, expected, actual);
    }
    
    /**
     * Asserts that two Strings are equal. If they are not,
     * an AssertionFailedError is thrown.
     */
    public static void assertEquals(String expected, String actual) {
        assertEquals(DEFAULT_MESSAGE, expected, actual);
    }
    
    /**
     * Asserts that two doubles are equal concerning a delta. If they are not,
     * an AssertionFailedError is thrown with the given message.
     */
    public static void assertEquals(String message, double expected, double actual, double delta) {
        if (Double.compare(expected, actual) == 0) {
            return;
        }
        if (!(Math.abs(expected - actual) <= delta)) {
            failNotEquals(message, new Double(expected), new Double(actual));
        }
    }
    
    /**
     * Asserts that two doubles are equal concerning a delta. If they are not,
     * an AssertionFailedError is thrown.
     */
    public static void assertEquals(double expected, double actual, double delta) {
        assertEquals(DEFAULT_MESSAGE, expected, actual, delta);
    }
    
    /**
     * Asserts that two floats are equal concerning a delta. If they are not,
     * an AssertionFailedError is thrown with the given message.
     */
    public static void assertEquals(String message, float expected, float actual, float delta) {
        if (Float.compare(expected, actual) == 0) {
            return;
        }
        if (!(Math.abs(expected - actual) <= delta)) {
            failNotEquals(message, new Float(expected), new Float(actual));
        }
    }
    
    /**
     * Asserts that two floats are equal concerning a delta. If they are not,
     * an AssertionFailedError is thrown.
     */
    public static void assertEquals(float expected, float actual, float delta) {
        assertEquals(DEFAULT_MESSAGE, expected, actual, delta);
    }
    
    /**
     * Asserts that two longs are equal. If they are not,
     * an AssertionFailedError is thrown with the given message.
     */
    public static void assertEquals(String message, long expected, long actual) {
        assertEquals(message, new Long(expected), new Long(actual));
    }
    
    /**
     * Asserts that two longs are equal. If they are not,
     * an AssertionFailedError is thrown.
     */
    public static void assertEquals(long expected, long actual) {
        assertEquals(DEFAULT_MESSAGE, expected, actual);
    }
    
    /**
     * Asserts that two booleans are equal. If they are not,
     * an AssertionFailedError is thrown with the given message.
     */
    public static void assertEquals(String message, boolean expected, boolean actual) {
        assertEquals(message, new Boolean(expected), new Boolean(actual));
    }
    
    /**
     * Asserts that two booleans are equal. If they are not,
     * an AssertionFailedError is thrown.
     */
    public static void assertEquals(boolean expected, boolean actual) {
        assertEquals(DEFAULT_MESSAGE, expected, actual);
    }
    
    /**
     * Asserts that two bytes are equal. If they are not,
     * an AssertionFailedError is thrown with the given message.
     */
    public static void assertEquals(String message, byte expected, byte actual) {
        assertEquals(message, new Byte(expected), new Byte(actual));
    }
    
    /**
     * Asserts that two bytes are equal. If they are not,
     * an AssertionFailedError is thrown.
     */
    public static void assertEquals(byte expected, byte actual) {
        assertEquals(DEFAULT_MESSAGE, expected, actual);
    }
    
    /**
     * Asserts that two chars are equal. If they are not,
     * an AssertionFailedError is thrown with the given message.
     */
    public static void assertEquals(String message, char expected, char actual) {
        assertEquals(message, new Character(expected), new Character(actual));
    }
    
    /**
     * Asserts that two chars are equal. If they are not,
     * an AssertionFailedError is thrown.
     */
    public static void assertEquals(char expected, char actual) {
        assertEquals(DEFAULT_MESSAGE, expected, actual);
    }
    
    /**
     * Asserts that two shorts are equal. If they are not,
     * an AssertionFailedError is thrown with the given message.
     */
    public static void assertEquals(String message, short expected, short actual) {
        assertEquals(message, new Short(expected), new Short(actual));
    }
    
    /**
     * Asserts that two shorts are equal. If they are not,
     * an AssertionFailedError is thrown.
     */
    public static void assertEquals(short expected, short actual) {
        assertEquals(DEFAULT_MESSAGE, expected, actual);
    }
    
    /**
     * Asserts that two ints are equal. If they are not,
     * an AssertionFailedError is thrown with the given message.
     */
    public static void assertEquals(String message, int expected, int actual) {
        assertEquals(message, new Integer(expected), new Integer(actual));
    }
    
    /**
     * Asserts that two ints are equal. If they are not,
     * an AssertionFailedError is thrown.
     */
    public static void assertEquals(int expected, int actual) {
        assertEquals(DEFAULT_MESSAGE, expected, actual);
    }
    
    /**
     * Asserts that an object isn't null. If it is,
     * an AssertionFailedError is thrown with the given message.
     */
    public static void assertNotNull(String message, Object object) {
        assertTrue(message, object != null);
    }
    
    /**
     * Asserts that an object isn't null. If it is,
     * an AssertionFailedError is thrown.
     */
    public static void assertNotNull(Object object) {
        assertNotNull(DEFAULT_MESSAGE, object);
    }
    
    /**
     * Asserts that an object is null. If it isn't,
     * an AssertionFailedError is thrown with the given message.
     */
    public static void assertNull(String message, Object object) {
        assertTrue(message, object == null);
    }
    
    /**
     * Asserts that an object is null. If it isn't,
     * an AssertionFailedError is thrown.
     */
    public static void assertNull(Object object) {
        assertNull(DEFAULT_MESSAGE, object);
    }
    
    /**
     * Asserts that two objects refer to the same object. If they are not,
     * an AssertionFailedError is thrown with the given message.
     */
    public static void assertSame(String message, Object expected, Object actual) {
        if (expected == actual) {
            return;
        }
        failNotSame(message, expected, actual);
    }
    
    /**
     * Asserts that two objects refer to the same object. If they are not,
     * an AssertionFailedError is thrown.
     */
    public static void assertSame(Object expected, Object actual) {
        assertSame(DEFAULT_MESSAGE, expected, actual);
    }
    
    /**
     * Asserts that two objects do not refer to the same object. If they do,
     * an AssertionFailedError is thrown with the given message.
     */
    public static void assertNotSame(String message, Object expected, Object actual) {
        if (expected == actual) {
            failSame(message);
        }
    }
    
    /**
     * Asserts that two objects do not refer to the same object. If they do,
     * an AssertionFailedError is thrown.
     */
    public static void assertNotSame(Object expected, Object actual) {
        assertNotSame(DEFAULT_MESSAGE, expected, actual);
    }
    
    /**
     * Asserts that two objects are not equal. If they are,
     * an AssertionFailedError is thrown with the given message.
     */
    public static void assertNotEquals(String message, Object unexpected, Object actual) {
        if (unexpected == null && actual == null) {
            fail(message);
        }
        if (unexpected != null && unexpected.equals(actual)) {
            fail(message);
        }
    }
    
    /**
     * Asserts that two objects are not equal. If they are,
     * an AssertionFailedError is thrown.
     */
    public static void assertNotEquals(Object unexpected, Object actual) {
        assertNotEquals(DEFAULT_MESSAGE, unexpected, actual);
    }
    
    /**
     * Asserts that two Strings are not equal. If they are,
     * an AssertionFailedError is thrown with the given message.
     */
    public static void assertNotEquals(String message, String unexpected, String actual) {
        if (unexpected == null && actual == null) {
            fail(message);
        }
        if (unexpected != null && unexpected.equals(actual)) {
            fail(message);
        }
    }
    
    /**
     * Asserts that two Strings are not equal. If they are,
     * an AssertionFailedError is thrown.
     */
    public static void assertNotEquals(String unexpected, String actual) {
        assertNotEquals(DEFAULT_MESSAGE, unexpected, actual);
    }
    
    /**
     * Asserts that two doubles are not equal. If they are,
     * an AssertionFailedError is thrown with the given message.
     */
    public static void assertNotEquals(String message, double unexpected, double actual, double delta) {
        if (Double.compare(unexpected, actual) == 0) {
            fail(message);
        }
        if (!(Math.abs(unexpected - actual) <= delta)) {
            return;
        }
        fail(message);
    }
    
    /**
     * Asserts that two doubles are not equal. If they are,
     * an AssertionFailedError is thrown.
     */
    public static void assertNotEquals(double unexpected, double actual, double delta) {
        assertNotEquals(DEFAULT_MESSAGE, unexpected, actual, delta);
    }
    
    /**
     * Asserts that two floats are not equal. If they are,
     * an AssertionFailedError is thrown with the given message.
     */
    public static void assertNotEquals(String message, float unexpected, float actual, float delta) {
        if (Float.compare(unexpected, actual) == 0) {
            fail(message);
        }
        if (!(Math.abs(unexpected - actual) <= delta)) {
            return;
        }
        fail(message);
    }
    
    /**
     * Asserts that two floats are not equal. If they are,
     * an AssertionFailedError is thrown.
     */
    public static void assertNotEquals(float unexpected, float actual, float delta) {
        assertNotEquals(DEFAULT_MESSAGE, unexpected, actual, delta);
    }
    
    /**
     * Asserts that two longs are not equal. If they are,
     * an AssertionFailedError is thrown with the given message.
     */
    public static void assertNotEquals(String message, long unexpected, long actual) {
        assertNotEquals(message, new Long(unexpected), new Long(actual));
    }
    
    /**
     * Asserts that two longs are not equal. If they are,
     * an AssertionFailedError is thrown.
     */
    public static void assertNotEquals(long unexpected, long actual) {
        assertNotEquals(DEFAULT_MESSAGE, unexpected, actual);
    }
    
    /**
     * Asserts that two booleans are not equal. If they are,
     * an AssertionFailedError is thrown with the given message.
     */
    public static void assertNotEquals(String message, boolean unexpected, boolean actual) {
        assertNotEquals(message, new Boolean(unexpected), new Boolean(actual));
    }
    
    /**
     * Asserts that two booleans are not equal. If they are,
     * an AssertionFailedError is thrown.
     */
    public static void assertNotEquals(boolean unexpected, boolean actual) {
        assertNotEquals(DEFAULT_MESSAGE, unexpected, actual);
    }
    
    /**
     * Asserts that two bytes are not equal. If they are,
     * an AssertionFailedError is thrown with the given message.
     */
    public static void assertNotEquals(String message, byte unexpected, byte actual) {
        assertNotEquals(message, new Byte(unexpected), new Byte(actual));
    }
    
    /**
     * Asserts that two bytes are not equal. If they are,
     * an AssertionFailedError is thrown.
     */
    public static void assertNotEquals(byte unexpected, byte actual) {
        assertNotEquals(DEFAULT_MESSAGE, unexpected, actual);
    }
    
    /**
     * Asserts that two chars are not equal. If they are,
     * an AssertionFailedError is thrown with the given message.
     */
    public static void assertNotEquals(String message, char unexpected, char actual) {
        assertNotEquals(message, new Character(unexpected), new Character(actual));
    }
    
    /**
     * Asserts that two chars are not equal. If they are,
     * an AssertionFailedError is thrown.
     */
    public static void assertNotEquals(char unexpected, char actual) {
        assertNotEquals(DEFAULT_MESSAGE, unexpected, actual);
    }
    
    /**
     * Asserts that two shorts are not equal. If they are,
     * an AssertionFailedError is thrown with the given message.
     */
    public static void assertNotEquals(String message, short unexpected, short actual) {
        assertNotEquals(message, new Short(unexpected), new Short(actual));
    }
    
    /**
     * Asserts that two shorts are not equal. If they are,
     * an AssertionFailedError is thrown.
     */
    public static void assertNotEquals(short unexpected, short actual) {
        assertNotEquals(DEFAULT_MESSAGE, unexpected, actual);
    }
    
    /**
     * Asserts that two ints are not equal. If they are,
     * an AssertionFailedError is thrown with the given message.
     */
    public static void assertNotEquals(String message, int unexpected, int actual) {
        assertNotEquals(message, new Integer(unexpected), new Integer(actual));
    }
    
    /**
     * Asserts that two ints are not equal. If they are,
     * an AssertionFailedError is thrown.
     */
    public static void assertNotEquals(int unexpected, int actual) {
        assertNotEquals(DEFAULT_MESSAGE, unexpected, actual);
    }
    
    /**
     * Asserts that two objects are equal. If they are not,
     * an AssertionFailedError is thrown with the given message.
     */
    public static void assertEquals(String message, Object[] expected, Object[] actual) {
        if (expected == null && actual == null) {
            return;
        }
        if (expected == null || actual == null) {
            failNotEquals(message, expected, actual);
        }
        if (expected.length != actual.length) {
            failNotEquals(message, expected, actual);
        }
        for (int i = 0; i < expected.length; i++) {
            assertEquals(message, expected[i], actual[i]);
        }
    }
    
    /**
     * Asserts that two objects are equal. If they are not,
     * an AssertionFailedError is thrown.
     */
    public static void assertEquals(Object[] expected, Object[] actual) {
        assertEquals(DEFAULT_MESSAGE, expected, actual);
    }
    
    /**
     * Asserts that two Strings are equal. If they are not,
     * an AssertionFailedError is thrown with the given message.
     */
    public static void assertEquals(String message, String[] expected, String[] actual) {
        if (expected == null && actual == null) {
            return;
        }
        if (expected == null || actual == null) {
            failNotEquals(message, expected, actual);
        }
        if (expected.length != actual.length) {
            failNotEquals(message, expected, actual);
        }
        for (int i = 0; i < expected.length; i++) {
            assertEquals(message, expected[i], actual[i]);
        }
    }
    
    /**
     * Asserts that two Strings are equal. If they are not,
     * an AssertionFailedError is thrown.
     */
    public static void assertEquals(String[] expected, String[] actual) {
        assertEquals(DEFAULT_MESSAGE, expected, actual);
    }
    
    /**
     * Asserts that two doubles are equal. If they are not,
     * an AssertionFailedError is thrown with the given message.
     */
    public static void assertEquals(String message, double[] expected, double[] actual, double delta) {
        if (expected == null && actual == null) {
            return;
        }
        if (expected == null || actual == null) {
            failNotEquals(message, expected, actual);
        }
        if (expected.length != actual.length) {
            failNotEquals(message, expected, actual);
        }
        for (int i = 0; i < expected.length; i++) {
            assertEquals(message, expected[i], actual[i], delta);
        }
    }
    
    /**
     * Asserts that two doubles are equal. If they are not,
     * an AssertionFailedError is thrown.
     */
    public static void assertEquals(double[] expected, double[] actual, double delta) {
        assertEquals(DEFAULT_MESSAGE, expected, actual, delta);
    }
    
    /**
     * Asserts that two floats are equal. If they are not,
     * an AssertionFailedError is thrown with the given message.
     */
    public static void assertEquals(String message, float[] expected, float[] actual, float delta) {
        if (expected == null && actual == null) {
            return;
        }
        if (expected == null || actual == null) {
            failNotEquals(message, expected, actual);
        }
        if (expected.length != actual.length) {
            failNotEquals(message, expected, actual);
        }
        for (int i = 0; i < expected.length; i++) {
            assertEquals(message, expected[i], actual[i], delta);
        }
    }
    
    /**
     * Asserts that two floats are equal. If they are not,
     * an AssertionFailedError is thrown.
     */
    public static void assertEquals(float[] expected, float[] actual, float delta) {
        assertEquals(DEFAULT_MESSAGE, expected, actual, delta);
    }
    
    /**
     * Asserts that two longs are equal. If they are not,
     * an AssertionFailedError is thrown with the given message.
     */
    public static void assertEquals(String message, long[] expected, long[] actual) {
        if (expected == null && actual == null) {
            return;
        }
        if (expected == null || actual == null) {
            failNotEquals(message, expected, actual);
        }
        if (expected.length != actual.length) {
            failNotEquals(message, expected, actual);
        }
        for (int i = 0; i < expected.length; i++) {
            assertEquals(message, expected[i], actual[i]);
        }
    }
    
    /**
     * Asserts that two longs are equal. If they are not,
     * an AssertionFailedError is thrown.
     */
    public static void assertEquals(long[] expected, long[] actual) {
        assertEquals(DEFAULT_MESSAGE, expected, actual);
    }
    
    /**
     * Asserts that two booleans are equal. If they are not,
     * an AssertionFailedError is thrown with the given message.
     */
    public static void assertEquals(String message, boolean[] expected, boolean[] actual) {
        if (expected == null && actual == null) {
            return;
        }
        if (expected == null || actual == null) {
            failNotEquals(message, expected, actual);
        }
        if (expected.length != actual.length) {
            failNotEquals(message, expected, actual);
        }
        for (int i = 0; i < expected.length; i++) {
            assertEquals(message, expected[i], actual[i]);
        }
    }
    
    /**
     * Asserts that two booleans are equal. If they are not,
     * an AssertionFailedError is thrown.
     */
    public static void assertEquals(boolean[] expected, boolean[] actual) {
        assertEquals(DEFAULT_MESSAGE, expected, actual);
    }
    
    /**
     * Asserts that two bytes are equal. If they are not,
     * an AssertionFailedError is thrown with the given message.
     */
    public static void assertEquals(String message, byte[] expected, byte[] actual) {
        if (expected == null && actual == null) {
            return;
        }
        if (expected == null || actual == null) {
            failNotEquals(message, expected, actual);
        }
        if (expected.length != actual.length) {
            failNotEquals(message, expected, actual);
        }
        for (int i = 0; i < expected.length; i++) {
            assertEquals(message, expected[i], actual[i]);
        }
    }
    
    /**
     * Asserts that two bytes are equal. If they are not,
     * an AssertionFailedError is thrown.
     */
    public static void assertEquals(byte[] expected, byte[] actual) {
        assertEquals(DEFAULT_MESSAGE, expected, actual);
    }
    
    /**
     * Asserts that two chars are equal. If they are not,
     * an AssertionFailedError is thrown with the given message.
     */
    public static void assertEquals(String message, char[] expected, char[] actual) {
        if (expected == null && actual == null) {
            return;
        }
        if (expected == null || actual == null) {
            failNotEquals(message, expected, actual);
        }
        if (expected.length != actual.length) {
            failNotEquals(message, expected, actual);
        }
        for (int i = 0; i < expected.length; i++) {
            assertEquals(message, expected[i], actual[i]);
        }
    }
    
    /**
     * Asserts that two chars are equal. If they are not,
     * an AssertionFailedError is thrown.
     */
    public static void assertEquals(char[] expected, char[] actual) {
        assertEquals(DEFAULT_MESSAGE, expected, actual);
    }
    
    /**
     * Asserts that two shorts are equal. If they are not,
     * an AssertionFailedError is thrown with the given message.
     */
    public static void assertEquals(String message, short[] expected, short[] actual) {
        if (expected == null && actual == null) {
            return;
        }
        if (expected == null || actual == null) {
            failNotEquals(message, expected, actual);
        }
        if (expected.length == actual.length) {
            for (int i = 0; i < expected.length; i++) {
                assertEquals(message, expected[i], actual[i]);
            }
        } else {
            failNotEquals(message, expected, actual);
        }
    }
    
    /**
     * Asserts that two shorts are equal. If they are not,
     * an AssertionFailedError is thrown.
     */
    public static void assertEquals(short[] expected, short[] actual) {
        assertEquals(DEFAULT_MESSAGE, expected, actual);
    }
    
    /**
     * Asserts that two ints are equal. If they are not,
     * an AssertionFailedError is thrown with the given message.
     */
    public static void assertEquals(String message, int[] expected, int[] actual) {
        if (expected == null && actual == null) {
            return;
        }
        if (expected == null || actual == null) {
            failNotEquals(message, expected, actual);
        }
        if (expected.length != actual.length) {
            failNotEquals(message, expected, actual);
        }
        for (int i = 0; i < expected.length; i++) {
            assertEquals(message, expected[i], actual[i]);
        }
    }
    
    /**
     * Asserts that two ints are equal. If they are not,
     * an AssertionFailedError is thrown.
     */
    public static void assertEquals(int[] expected, int[] actual) {
        assertEquals(DEFAULT_MESSAGE, expected, actual);
    }
    
    private static void failNotEquals(String message, Object expected, Object actual) {
        fail(format(message, expected, actual));
    }
    
    private static void failNotSame(String message, Object expected, Object actual) {
        fail(format(message, expected, actual));
    }
    
    private static void failSame(String message) {
        fail(message);
    }
    
    private static String format(String message, Object expected, Object actual) {
        String formatted = "";
        if (message != null && !message.equals("")) {
            formatted = message + " ";
        }
        String expectedString = String.valueOf(expected);
        String actualString = String.valueOf(actual);
        if (expectedString.equals(actualString)) {
            return formatted + "expected: " + formatClassAndValue(expected, expectedString) + " but was: " + formatClassAndValue(actual, actualString);
        } else {
            return formatted + "expected:<" + expectedString + "> but was:<" + actualString + ">";
        }
    }
    
    private static String formatClassAndValue(Object value, String valueString) {
        String className = value == null ? "null" : value.getClass().getName();
        return className + "<" + valueString + ">";
    }
}
