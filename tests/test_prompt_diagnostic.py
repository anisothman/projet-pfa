"""Tests pour le module de prompt diagnostic"""

import unittest
import json
from src.prompts.prompt_diagnostic import PromptDiagnostic


class TestPromptDiagnostic(unittest.TestCase):
    
    def setUp(self):
        self.prompt_creator = PromptDiagnostic()
        self.sample_company = {
            "company_name": "TestCorp",
            "results": [
                {
                    "position": 1,
                    "title": "TestCorp Main",
                    "snippet": "Main company info",
                },
                {
                    "position": 2,
                    "title": "TestCorp Services",
                    "snippet": "Service description",
                }
            ]
        }
    
    def test_prompt_creation(self):
        """Test création d'un prompt diagnostic"""
        prompt = self.prompt_creator.create_diagnostic_prompt(self.sample_company)
        self.assertIsNotNone(prompt)
        self.assertIn("TestCorp", prompt)
    
    def test_prompt_validation(self):
        """Test validation du prompt"""
        prompt = self.prompt_creator.create_diagnostic_prompt(self.sample_company)
        self.assertTrue(self.prompt_creator.validate_prompt(prompt))
    
    def test_multi_company_prompt(self):
        """Test prompt comparatif"""
        companies = [self.sample_company, self.sample_company]
        prompt = self.prompt_creator.create_multi_company_diagnostic_prompt(companies)
        self.assertIsNotNone(prompt)
        self.assertIn("comparison", prompt.lower())
    
    def test_schema_structure(self):
        """Test structure du schéma"""
        schema = self.prompt_creator.get_schema()
        required_keys = ["company_name", "strengths", "weaknesses", "opportunities"]
        for key in required_keys:
            self.assertIn(key, schema)


if __name__ == '__main__':
    unittest.main()