"""
Unit tests for Pydantic models with logic.

Only tests models that have computed properties or custom validators.
Simple field-only models are tested implicitly through service/API tests.
"""

from models import (ComplianceResult, ComplianceSeverity, ComplianceViolation,
                    ContentGenerationResponse, GeneratedTextContent)


class TestComplianceResult:
    """Tests for ComplianceResult model properties."""

    def test_has_errors_false_when_empty(self):
        """Test has_errors is False with no violations."""
        result = ComplianceResult(is_valid=True, violations=[])

        assert result.has_errors is False

    def test_has_errors_true_with_error_violations(self):
        """Test has_errors is True with error-level violations."""
        result = ComplianceResult(
            is_valid=False,
            violations=[
                ComplianceViolation(
                    severity=ComplianceSeverity.ERROR,
                    message="Error",
                    suggestion="Fix"
                )
            ]
        )

        assert result.has_errors is True

    def test_has_errors_false_with_only_warnings(self):
        """Test has_errors is False when only warnings exist."""
        result = ComplianceResult(
            is_valid=True,
            violations=[
                ComplianceViolation(
                    severity=ComplianceSeverity.WARNING,
                    message="Warning",
                    suggestion="Review"
                )
            ]
        )

        assert result.has_errors is False

    def test_has_warnings_false_when_empty(self):
        """Test has_warnings is False with no violations."""
        result = ComplianceResult(is_valid=True, violations=[])

        assert result.has_warnings is False

    def test_has_warnings_true_with_warning_violations(self):
        """Test has_warnings is True with warning-level violations."""
        result = ComplianceResult(
            is_valid=True,
            violations=[
                ComplianceViolation(
                    severity=ComplianceSeverity.WARNING,
                    message="Warning",
                    suggestion="Review"
                )
            ]
        )

        assert result.has_warnings is True

    def test_has_warnings_false_with_only_errors(self):
        """Test has_warnings is False when only errors exist."""
        result = ComplianceResult(
            is_valid=False,
            violations=[
                ComplianceViolation(
                    severity=ComplianceSeverity.ERROR,
                    message="Error",
                    suggestion="Fix"
                )
            ]
        )

        assert result.has_warnings is False

    def test_mixed_violations(self):
        """Test both properties with mixed violations."""
        result = ComplianceResult(
            is_valid=False,
            violations=[
                ComplianceViolation(
                    severity=ComplianceSeverity.ERROR,
                    message="Error",
                    suggestion="Fix"
                ),
                ComplianceViolation(
                    severity=ComplianceSeverity.WARNING,
                    message="Warning",
                    suggestion="Review"
                ),
                ComplianceViolation(
                    severity=ComplianceSeverity.INFO,
                    message="Info",
                    suggestion="Optional"
                )
            ]
        )

        assert result.has_errors is True
        assert result.has_warnings is True


class TestContentGenerationResponse:
    """Tests for ContentGenerationResponse requires_modification property."""

    def test_requires_modification_false_with_no_content(self, sample_creative_brief):
        """Test requires_modification is falsy when no content exists."""
        response = ContentGenerationResponse(
            creative_brief=sample_creative_brief,
            generation_id="gen-123"
        )

        assert not response.requires_modification

    def test_requires_modification_false_with_valid_text(self, sample_creative_brief):
        """Test requires_modification is falsy when text has no errors."""
        response = ContentGenerationResponse(
            text_content=GeneratedTextContent(
                headline="Test",
                compliance=ComplianceResult(is_valid=True, violations=[])
            ),
            creative_brief=sample_creative_brief,
            generation_id="gen-123"
        )

        assert not response.requires_modification

    def test_requires_modification_true_with_text_errors(self, sample_creative_brief):
        """Test requires_modification is True when text has errors."""
        response = ContentGenerationResponse(
            text_content=GeneratedTextContent(
                headline="Test",
                compliance=ComplianceResult(
                    is_valid=False,
                    violations=[
                        ComplianceViolation(
                            severity=ComplianceSeverity.ERROR,
                            message="Error",
                            suggestion="Fix"
                        )
                    ]
                )
            ),
            creative_brief=sample_creative_brief,
            generation_id="gen-123"
        )

        assert response.requires_modification is True

    def test_requires_modification_false_with_only_warnings(self, sample_creative_brief):
        """Test requires_modification is falsy when only warnings exist."""
        response = ContentGenerationResponse(
            text_content=GeneratedTextContent(
                headline="Test",
                compliance=ComplianceResult(
                    is_valid=True,
                    violations=[
                        ComplianceViolation(
                            severity=ComplianceSeverity.WARNING,
                            message="Warning",
                            suggestion="Review"
                        )
                    ]
                )
            ),
            creative_brief=sample_creative_brief,
            generation_id="gen-123"
        )

        assert not response.requires_modification
