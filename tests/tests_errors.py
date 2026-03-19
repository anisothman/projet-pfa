import os
import sys
import unittest
from unittest.mock import Mock, patch

import requests

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.error_handler import (
    EmptyResponseError,
    InvalidKeyError,
    NetworkError,
    QuotaExceededError,
    retry_with_backoff,
    safe_extract,
    validate_response,
)


class TestErrorHandler(unittest.TestCase):
    def setUp(self):
        self.valid_response = {
            "place_results": {
                "title": "Test Business",
                "address": "123 Test St",
            }
        }

    def test_validate_response_valid(self):
        result = validate_response(self.valid_response)
        self.assertEqual(result, self.valid_response)

    def test_validate_response_empty(self):
        with self.assertRaises(EmptyResponseError):
            validate_response({})

    def test_validate_response_none(self):
        with self.assertRaises(EmptyResponseError):
            validate_response(None)

    def test_validate_response_api_error(self):
        with self.assertRaises(InvalidKeyError):
            validate_response({"error": "Invalid API key"})

    def test_validate_response_quota_error(self):
        with self.assertRaises(QuotaExceededError):
            validate_response({"error": "Quota exceeded"})

    def test_validate_response_missing_place_results(self):
        response = {"other": "data"}
        result = validate_response(response)
        self.assertEqual(result["place_results"], {})

    def test_safe_extract_valid(self):
        data = {"a": {"b": {"c": "value"}}}
        self.assertEqual(safe_extract(data, "a.b.c"), "value")

    def test_safe_extract_missing_key(self):
        data = {"a": {"b": "value"}}
        self.assertEqual(safe_extract(data, "a.b.c", default="default"), "default")

    def test_safe_extract_none_value(self):
        data = {"a": {"b": None}}
        self.assertEqual(safe_extract(data, "a.b", default="default"), "default")

    @patch("time.sleep")
    def test_retry_decorator_success_first_try(self, mock_sleep):
        mock_func = Mock(return_value="success")
        decorated = retry_with_backoff(max_retries=3)(mock_func)

        result = decorated()

        self.assertEqual(result, "success")
        mock_func.assert_called_once()
        mock_sleep.assert_not_called()

    @patch("time.sleep")
    def test_retry_decorator_success_after_retry(self, mock_sleep):
        mock_func = Mock()
        mock_func.side_effect = [
            requests.Timeout("Timeout"),
            requests.ConnectionError("Connection error"),
            "success",
        ]
        decorated = retry_with_backoff(max_retries=3)(mock_func)

        result = decorated()

        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch("time.sleep")
    def test_retry_decorator_all_fail(self, mock_sleep):
        mock_func = Mock(side_effect=requests.Timeout("Timeout"))
        decorated = retry_with_backoff(max_retries=2)(mock_func)

        with self.assertRaises(NetworkError):
            decorated()

        self.assertEqual(mock_func.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)

    def test_retry_decorator_http_401(self):
        mock_response = Mock()
        mock_response.status_code = 401
        mock_func = Mock(side_effect=requests.HTTPError(response=mock_response))
        decorated = retry_with_backoff(max_retries=3)(mock_func)

        with self.assertRaises(InvalidKeyError):
            decorated()

    def test_retry_decorator_http_429(self):
        mock_response = Mock()
        mock_response.status_code = 429
        mock_func = Mock(side_effect=requests.HTTPError(response=mock_response))
        decorated = retry_with_backoff(max_retries=3)(mock_func)

        with self.assertRaises(QuotaExceededError):
            decorated()


if __name__ == "__main__":
    unittest.main(verbosity=2)
import unittest
from unittest.mock import Mock, patch
import requests
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.error_handler import (
    retry_with_backoff,
    validate_response,
    safe_extract,
    SerpAPIError,
    InvalidKeyError,
    QuotaExceededError,
    EmptyResponseError,
    NetworkError
)
from src.logger_config import logger

class TestErrorHandler(unittest.TestCase):
    def setUp(self):
        self.valid_response = {
            'place_results': {
                'title': 'Test Business',
                'address': '123 Test St'
            }
        }
    
    def test_validate_response_valid(self):
        result = validate_response(self.valid_response)
        self.assertEqual(result, self.valid_response)
    
    def test_validate_response_empty(self):
        with self.assertRaises(EmptyResponseError):
            validate_response({})
    
    def test_validate_response_none(self):
        with self.assertRaises(EmptyResponseError):
            validate_response(None)
    
    def test_validate_response_api_error(self):
        error_response = {'error': 'Invalid API key'}
        with self.assertRaises(InvalidKeyError):
            validate_response(error_response)
    
    def test_validate_response_quota_error(self):
        error_response = {'error': 'Quota exceeded'}
        with self.assertRaises(QuotaExceededError):
            validate_response(error_response)
    
    def test_validate_response_missing_place_results(self):
        response = {'other': 'data'}
        result = validate_response(response)
        self.assertEqual(result['place_results'], {})
    
    def test_safe_extract_valid(self):
        data = {'a': {'b': {'c': 'value'}}}
        result = safe_extract(data, 'a.b.c')
        self.assertEqual(result, 'value')
    
    def test_safe_extract_missing_key(self):
        data = {'a': {'b': 'value'}}
        result = safe_extract(data, 'a.b.c', default='default')
        self.assertEqual(result, 'default')
    
    def test_safe_extract_none_value(self):
        data = {'a': {'b': None}}
        result = safe_extract(data, 'a.b', default='default')
        self.assertEqual(result, 'default')
    
    @patch('time.sleep')
    def test_retry_decorator_success_first_try(self, mock_sleep):
        mock_func = Mock(return_value="success")
        decorated = retry_with_backoff(max_retries=3)(mock_func)
        result = decorated()
        self.assertEqual(result, "success")
        mock_func.assert_called_once()
        mock_sleep.assert_not_called()
    
    @patch('time.sleep')
    def test_retry_decorator_success_after_retry(self, mock_sleep):
        mock_func = Mock()
        mock_func.side_effect = [
            requests.Timeout("Timeout"),
            requests.ConnectionError("Connection error"),
            "success"
        ]
        decorated = retry_with_backoff(max_retries=3)(mock_func)
        result = decorated()
        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)
    
    @patch('time.sleep')
    def test_retry_decorator_all_fail(self, mock_sleep):
        mock_func = Mock(side_effect=requests.Timeout("Timeout"))
        decorated = retry_with_backoff(max_retries=2)(mock_func)
        with self.assertRaises(NetworkError):
            decorated()
        self.assertEqual(mock_func.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)
    
    def test_retry_decorator_http_401(self):
        mock_response = Mock()
        mock_response.status_code = 401
        mock_func = Mock(side_effect=requests.HTTPError(response=mock_response))
        decorated = retry_with_backoff(max_retries=3)(mock_func)
        with self.assertRaises(InvalidKeyError):
            decorated()
        mock_func.assert_called_once()
    
    def test_retry_decorator_http_429(self):
        mock_response = Mock()
        mock_response.status_code = 429
        mock_func = Mock(side_effect=requests.HTTPError(response=mock_response))
        decorated = retry_with_backoff(max_retries=3)(mock_func)
        with self.assertRaises(QuotaExceededError):
            decorated()
        mock_func.assert_called_once()

class TestIntegrationSimulation(unittest.TestCase):
    def test_complete_workflow_success(self):
        data = {
            'place_results': {
                'title': 'Restaurant Test',
                'address': 'Paris',
                'rating': 4.5,
                'reviews': 100
            }
        }
        validated = validate_response(data)
        self.assertIn('place_results', validated)
        name = safe_extract(validated, 'place_results.title')
        rating = safe_extract(validated, 'place_results.rating')
        self.assertEqual(name, 'Restaurant Test')
        self.assertEqual(rating, 4.5)
    
    def test_complete_workflow_missing_data(self):
        data = {
            'place_results': {
                'title': 'Restaurant Test'
            }
        }
        validated = validate_response(data)
        name = safe_extract(validated, 'place_results.title')
        address = safe_extract(validated, 'place_results.address', default='Adresse non disponible')
        rating = safe_extract(validated, 'place_results.rating', default=None)
        self.assertEqual(name, 'Restaurant Test')
        self.assertEqual(address, 'Adresse non disponible')
        self.assertIsNone(rating)
    
    def test_complete_workflow_empty(self):
        with self.assertRaises(EmptyResponseError):
            validate_response({})

if __name__ == '__main__':
    unittest.main(verbosity=2)