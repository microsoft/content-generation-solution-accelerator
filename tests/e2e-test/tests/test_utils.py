"""Shared utility functions for test modules."""
import logging
import time

logger = logging.getLogger(__name__)


def log_test_summary(start_time, step_times, test_name, additional_info=None):
    """
    Log test execution summary with timing details.

    Args:
        start_time: Test start timestamp
        step_times: List of tuples (step_name, step_duration)
        test_name: Name of the test
        additional_info: Optional dict with additional info to log
    
    Returns:
        float: Total duration of the test
    """
    end_time = time.time()
    total_duration = end_time - start_time

    logger.info("\n" + "=" * 80)
    logger.info("TEST EXECUTION SUMMARY")
    logger.info("=" * 80)

    for step_name, step_duration in step_times:
        logger.info(f"{step_name}: {step_duration:.2f}s")

    if additional_info:
        for key, value in additional_info.items():
            logger.info(f"{key}: {value}")

    logger.info(f"Total Execution Time: {total_duration:.2f}s")
    logger.info("=" * 80)
    logger.info(f"✓ {test_name} PASSED")
    logger.info("=" * 80)

    return total_duration


def log_test_failure(start_time, error):
    """
    Log test failure with timing and error details.

    Args:
        start_time: Test start timestamp
        error: Exception object
    
    Returns:
        float: Total duration before failure
    """
    end_time = time.time()
    total_duration = end_time - start_time

    logger.error("\n" + "=" * 80)
    logger.error("TEST EXECUTION FAILED")
    logger.error("=" * 80)
    logger.error(f"Error: {str(error)}")
    logger.error(f"Execution time before failure: {total_duration:.2f}s")
    logger.error("=" * 80)

    return total_duration
