package junit.tests.framework;

import junit.framework.AssertionFailedError;
import junit.framework.TestCase;

/**
 * Test cases for AssertionFailedError message handling.
 */
public class AssertionFailedErrorTest extends TestCase {
    private static final String ARBITRARY_MESSAGE = "arbitrary message";
    private AssertionFailedError error;

    /**
     * Tests creating an AssertionFailedError with no message.
     */
    public void testCreateErrorWithoutMessage() throws Exception {
        error = new AssertionFailedError();
        assertNull(error.getMessage());
    }

    /**
     * Tests creating an AssertionFailedError with a specific message.
     */
    public void testCreateErrorWithMessage() throws Exception {
        error = new AssertionFailedError(ARBITRARY_MESSAGE);
        assertEquals(ARBITRARY_MESSAGE, error.getMessage());
    }

    /**
     * Tests creating an AssertionFailedError with null message,
     * which should result in an empty string message.
     */
    public void testCreateErrorWithoutMessageInsteadOfNull() throws Exception {
        error = new AssertionFailedError(null);
        assertEquals("", error.getMessage());
    }
} 