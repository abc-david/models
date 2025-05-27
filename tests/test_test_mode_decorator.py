"""
Test module for the with_model_test_mode decorator.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.models.testing import with_model_test_mode
from services.models.orchestrator import ModelOrchestrator


class TestWithModelTestModeDecorator:
    """Test cases for the with_model_test_mode decorator."""
    
    @pytest.mark.asyncio
    async def test_decorator_without_mode(self):
        """Test the decorator without specifying a mode (defaults to production)."""
        with patch('services.models.testing.decorators.ModelOrchestrator') as mock_orchestrator_class:
            # Set up mock orchestrator
            mock_orchestrator = AsyncMock()
            mock_orchestrator_class.return_value = mock_orchestrator
            
            # Define test function to decorate
            @with_model_test_mode()
            async def test_func(orchestrator):
                return orchestrator.test_mode
            
            # Call the decorated function
            result = await test_func()
            
            # Assert orchestrator was created with None test_mode
            mock_orchestrator_class.assert_called_once_with(test_mode=None)
            
            # Assert close was called on orchestrator
            mock_orchestrator.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_decorator_with_e2e_mode(self):
        """Test the decorator with e2e test mode."""
        with patch('services.models.testing.decorators.ModelOrchestrator') as mock_orchestrator_class:
            # Set up mock orchestrator
            mock_orchestrator = AsyncMock()
            mock_orchestrator.test_mode = 'e2e'
            mock_orchestrator_class.return_value = mock_orchestrator
            
            # Define test function to decorate
            @with_model_test_mode(mode='e2e')
            async def test_func(orchestrator):
                return orchestrator.test_mode
            
            # Call the decorated function
            result = await test_func()
            
            # Assert result is correct
            assert result == 'e2e'
            
            # Assert orchestrator was created with e2e test_mode
            mock_orchestrator_class.assert_called_once_with(test_mode='e2e')
            
            # Assert close was called on orchestrator
            mock_orchestrator.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_decorator_with_mock_mode(self):
        """Test the decorator with mock test mode."""
        with patch('services.models.testing.decorators.ModelOrchestrator') as mock_orchestrator_class:
            # Set up mock orchestrator
            mock_orchestrator = AsyncMock()
            mock_orchestrator.test_mode = 'mock'
            mock_orchestrator_class.return_value = mock_orchestrator
            
            # Define test function to decorate
            @with_model_test_mode(mode='mock')
            async def test_func(orchestrator):
                return orchestrator.test_mode
            
            # Call the decorated function
            result = await test_func()
            
            # Assert result is correct
            assert result == 'mock'
            
            # Assert orchestrator was created with mock test_mode
            mock_orchestrator_class.assert_called_once_with(test_mode='mock')
            
            # Assert close was called on orchestrator
            mock_orchestrator.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_decorator_with_exception(self):
        """Test the decorator handles exceptions properly and still closes resources."""
        with patch('services.models.testing.decorators.ModelOrchestrator') as mock_orchestrator_class:
            # Set up mock orchestrator
            mock_orchestrator = AsyncMock()
            mock_orchestrator_class.return_value = mock_orchestrator
            
            # Define test function to decorate that raises an exception
            @with_model_test_mode(mode='e2e')
            async def test_func(orchestrator):
                raise ValueError("Test exception")
            
            # Call the decorated function and expect exception
            with pytest.raises(ValueError) as excinfo:
                await test_func()
            
            # Assert exception message is correct
            assert "Test exception" in str(excinfo.value)
            
            # Assert close was still called on orchestrator (cleanup)
            mock_orchestrator.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_decorator_passes_arguments(self):
        """Test the decorator passes additional arguments to the wrapped function."""
        with patch('services.models.testing.decorators.ModelOrchestrator') as mock_orchestrator_class:
            # Set up mock orchestrator
            mock_orchestrator = AsyncMock()
            mock_orchestrator_class.return_value = mock_orchestrator
            
            # Define test function to decorate with additional parameters
            @with_model_test_mode(mode='e2e')
            async def test_func(orchestrator, arg1, arg2, kwarg1=None, kwarg2=None):
                return {
                    'orchestrator_mode': orchestrator.test_mode,
                    'arg1': arg1,
                    'arg2': arg2,
                    'kwarg1': kwarg1,
                    'kwarg2': kwarg2
                }
            
            # Call the decorated function with arguments
            result = await test_func("value1", "value2", kwarg1="key1", kwarg2="key2")
            
            # Assert result contains all arguments
            assert result == {
                'orchestrator_mode': mock_orchestrator.test_mode,
                'arg1': "value1",
                'arg2': "value2",
                'kwarg1': "key1",
                'kwarg2': "key2"
            } 