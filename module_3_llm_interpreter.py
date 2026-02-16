"""
Module 3: LLM-Based Criteria Interpreter

This module uses LLM APIs (Google Gemini or Ollama) to interpret clinical concepts, 
normalize medical terminology, and extract structured information from admission criteria.
"""

import os
import json
import logging
import time
import requests
from typing import Dict, List, Optional, Any

try:
    from google import genai
    from google.genai.types import GenerateContentConfig
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Google Gemini library not available. Only Ollama provider will work.")


logger = logging.getLogger(__name__)


class LLMInterpreter:
    """
    Interprets clinical criteria using LLM (supports Google Gemini or Ollama).
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize LLM interpreter with configuration.
        
        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config
        self.llm_config = config.get('llm', {})
        
        # Determine provider
        self.provider = self.llm_config.get('provider', 'google').lower()
        self.model = self.llm_config.get('model', 'gemini-2.0-flash')
        self.temperature = self.llm_config.get('temperature', 0.1)
        self.max_tokens = self.llm_config.get('max_tokens', 8000)
        self.retry_attempts = self.llm_config.get('retry_attempts', 3)
        self.retry_delay = self.llm_config.get('retry_delay', 2)
        
        # Initialize provider-specific client
        if self.provider == 'ollama':
            self.ollama_url = self.llm_config.get('ollama_url', 'http://localhost:11434')
            # Ollama performance settings
            self.ollama_num_thread = self.llm_config.get('ollama_num_thread', 8)
            self.ollama_num_ctx = self.llm_config.get('ollama_num_ctx', 8192)
            self.ollama_num_gpu = self.llm_config.get('ollama_num_gpu', 1)
            logger.info(f"Initialized Ollama LLM interpreter with model: {self.model} at {self.ollama_url}")
            logger.info(f"Ollama settings - Threads: {self.ollama_num_thread}, Context: {self.ollama_num_ctx}, GPU: {self.ollama_num_gpu}")
            self._verify_ollama_connection()
        elif self.provider == 'google':
            if not GEMINI_AVAILABLE:
                raise ValueError("Google Gemini library not installed. Run: pip install google-genai")
            api_key = os.getenv(self.llm_config.get('api_key_env_var', 'GOOGLE_API_KEY'))
            if not api_key:
                raise ValueError(f"API key not found in environment variable: {self.llm_config.get('api_key_env_var')}")
            self.client = genai.Client(api_key=api_key)
            logger.info(f"Initialized Google Gemini LLM interpreter with model: {self.model}")
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}. Use 'google' or 'ollama'")
        
        # Cache for LLM responses
        self.response_cache = {}
    
    def _verify_ollama_connection(self):
        """Verify Ollama server is running and model is available."""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m.get('name', '') for m in models]
                if self.model not in model_names:
                    logger.warning(f"Model {self.model} not found in Ollama. Available models: {model_names}")
                    logger.warning(f"To pull the model, run: ollama pull {self.model}")
            else:
                logger.warning(f"Could not verify Ollama models: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Could not connect to Ollama at {self.ollama_url}: {e}")
            logger.error("Make sure Ollama is running: ollama serve")
    
    def interpret_criteria(self, parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Interpret all criteria using LLM.
        
        Args:
            parsed_data: Output from module_2_structure_parser
            
        Returns:
            List of interpreted criteria
        """
        logger.info("Starting LLM-based interpretation of criteria")
        
        criteria_list = parsed_data['admission_criteria']['criteria_list']
        interpreted_criteria = []
        
        for i, criterion in enumerate(criteria_list):
            logger.info(f"Interpreting criterion {i+1}/{len(criteria_list)}: {criterion['criterion_id']}")
            
            try:
                interpreted = self.interpret_criterion(criterion)
                interpreted_criteria.append(interpreted)
            except Exception as e:
                logger.error(f"Error interpreting criterion {criterion['criterion_id']}: {str(e)}")
                # Add criterion with minimal interpretation on error
                interpreted_criteria.append({
                    "criterion_id": criterion['criterion_id'],
                    "criterion_text": criterion['criterion_text'],
                    "interpreted_criterion": {
                        "primary_condition": {
                            "term": criterion['primary_condition'],
                            "snomed_code": "",
                            "icd10_codes": [],
                            "synonyms": []
                        },
                        "related_clinical_findings": [],
                        "qualifiers": {
                            "severity": criterion.get('qualifiers', []),
                            "temporal": criterion.get('persistence_requirement', ''),
                            "persistence": criterion.get('persistence_requirement', '')
                        },
                        "dependencies": criterion.get('conditional_requirements', []),
                        "clinical_category": criterion.get('clinical_category', 'general')
                    },
                    "interpretation_error": str(e)
                })
        
        logger.info(f"Successfully interpreted {len(interpreted_criteria)} criteria")
        return interpreted_criteria
    
    def interpret_criterion(self, criterion: Dict[str, Any]) -> Dict[str, Any]:
        """
        Interpret a single criterion using LLM.
        
        Args:
            criterion: Criterion dictionary from parser
            
        Returns:
            Interpreted criterion dictionary
        """
        # Check cache first
        cache_key = criterion['criterion_text']
        if cache_key in self.response_cache:
            logger.debug(f"Using cached interpretation for: {criterion['criterion_id']}")
            return self.response_cache[cache_key]
        
        # Generate prompt
        prompt = self._generate_interpretation_prompt(criterion)
        
        # Call LLM with retry logic
        response_text = self._call_llm_with_retry(prompt)
        
        # Parse LLM response
        interpreted_data = self._parse_llm_response(response_text)
        
        # Combine with original criterion data
        result = {
            "criterion_id": criterion['criterion_id'],
            "criterion_text": criterion['criterion_text'],
            "interpreted_criterion": interpreted_data
        }
        
        # Cache the result
        self.response_cache[cache_key] = result
        
        return result
    
    def _generate_interpretation_prompt(self, criterion: Dict[str, Any]) -> str:
        """
        Generate prompt for LLM interpretation.
        
        Args:
            criterion: Criterion dictionary
            
        Returns:
            Prompt string
        """
        prompt = f"""You are a medical informatics expert specializing in clinical criteria interpretation.

Given this MCG admission criterion:
"{criterion['criterion_text']}"

Extract the following information in JSON format:

1. Primary clinical condition:
   - Standardized medical term
   - SNOMED CT code (if applicable)
   - ICD-10 codes (if applicable)
   - Clinical synonyms

2. Related clinical findings that would satisfy this criterion:
   - Vital signs (e.g., blood pressure, heart rate, temperature)
   - Laboratory values (e.g., platelet count, culture results)
   - Clinical assessments (e.g., Glasgow Coma Scale, mental status)
   - For each finding include:
     * Finding name
     * Threshold value (if quantitative)
     * Comparison operator (less_than, greater_than, equals, between)
     * Unit of measurement
     * LOINC code (if applicable)

3. Qualifiers:
   - Severity (severe, moderate, mild)
   - Temporal characteristics (acute, chronic, persistent)
   - Persistence requirements

4. Dependencies and conditional requirements

5. Clinical category (hemodynamic, respiratory, metabolic, laboratory, etc.)

Return ONLY a valid JSON object with this exact structure:
{{
  "primary_condition": {{
    "term": "string",
    "snomed_code": "string or empty",
    "icd10_codes": ["string"],
    "synonyms": ["string"]
  }},
  "related_clinical_findings": [
    {{
      "finding": "string",
      "threshold": "string (e.g., '90', '60', 'positive')",
      "operator": "less_than|greater_than|equals|between|contains",
      "value": "numeric value as number or null",
      "unit": "string (e.g., 'mmHg', 'per minute', 'degrees F')",
      "loinc_code": "string or empty",
      "snomed_code": "string or empty"
    }}
  ],
  "qualifiers": {{
    "severity": ["string"],
    "temporal": "string",
    "persistence": "string"
  }},
  "dependencies": ["string"],
  "clinical_category": "string"
}}

CRITICAL: 
- Return ONLY valid, parseable JSON - no markdown, no explanations
- Ensure all strings are properly quoted and escaped
- Do not include newlines inside JSON string values
- If a code is not available, use an empty string ""
Be specific and comprehensive. Focus on creating actionable matching conditions.
"""
        return prompt
    
    def _call_llm_with_retry(self, prompt: str) -> str:
        """
        Call LLM API with exponential backoff retry logic.
        
        Args:
            prompt: Prompt string
            
        Returns:
            Response text from LLM
        """
        for attempt in range(self.retry_attempts):
            try:
                if self.provider == 'ollama':
                    response_text = self._call_ollama(prompt)
                elif self.provider == 'google':
                    response_text = self._call_gemini(prompt)
                else:
                    raise ValueError(f"Unknown provider: {self.provider}")
                
                return response_text
                
            except Exception as e:
                logger.warning(f"LLM call attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < self.retry_attempts - 1:
                    # Exponential backoff
                    delay = self.retry_delay * (2 ** attempt)
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    logger.error(f"All {self.retry_attempts} attempts failed")
                    raise
    
    def _call_gemini(self, prompt: str) -> str:
        """
        Call Google Gemini API.
        
        Args:
            prompt: Prompt string
            
        Returns:
            Response text
        """
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=GenerateContentConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
                response_mime_type='application/json'  # Force valid JSON output
            )
        )
        return response.text
    
    def _call_ollama(self, prompt: str) -> str:
        """
        Call Ollama API.
        
        Args:
            prompt: Prompt string
            
        Returns:
            Response text
        """
        url = f"{self.ollama_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
                "num_thread": self.ollama_num_thread,
                "num_ctx": self.ollama_num_ctx,
                "num_gpu": self.ollama_num_gpu
            },
            "format": "json"  # Request JSON format output
        }
        
        # No timeout - wait indefinitely for large models
        response = requests.post(url, json=payload, timeout=None)
        response.raise_for_status()
        
        result = response.json()
        return result.get('response', '')
    
    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse JSON response from LLM with robust error handling.
        
        Args:
            response_text: Raw response text
            
        Returns:
            Parsed dictionary
        """
        # Try to extract JSON from response
        # Sometimes LLM wraps JSON in markdown code blocks
        json_match = response_text
        
        # Remove markdown code blocks if present
        if '```json' in response_text:
            json_match = response_text.split('```json')[1].split('```')[0]
        elif '```' in response_text:
            json_match = response_text.split('```')[1].split('```')[0]
        
        # Clean up common issues
        json_match = json_match.strip()
        
        # Try parsing with progressively more aggressive fixes
        parsing_attempts = [
            # Attempt 1: Parse as-is
            lambda x: json.loads(x),
            # Attempt 2: Replace newlines in strings
            lambda x: json.loads(x.replace('\n', ' ')),
            # Attempt 3: Try to extract just the JSON object
            lambda x: json.loads(x[x.find('{'):x.rfind('}')+1]),
        ]
        
        for i, parse_func in enumerate(parsing_attempts):
            try:
                parsed = parse_func(json_match)
                if i > 0:
                    logger.warning(f"JSON parsed successfully on attempt {i+1}")
                return parsed
            except (json.JSONDecodeError, ValueError, AttributeError) as e:
                if i == len(parsing_attempts) - 1:
                    # Last attempt failed
                    logger.error(f"Failed to parse JSON response: {str(e)}")
                    logger.debug(f"Response text (first 500 chars): {response_text[:500]}")
                    
                    # Return minimal structure on parse error
                    return {
                        "primary_condition": {
                            "term": "unknown",
                            "snomed_code": "",
                    "icd10_codes": [],
                    "synonyms": []
                },
                "related_clinical_findings": [],
                "qualifiers": {
                    "severity": [],
                    "temporal": "",
                    "persistence": ""
                },
                "dependencies": [],
                "clinical_category": "general"
            }
    
    def extract_clinical_concepts(self, text: str) -> Dict[str, Any]:
        """
        Extract clinical concepts from free text.
        
        Args:
            text: Clinical text
            
        Returns:
            Dictionary of extracted concepts
        """
        prompt = f"""Extract all clinical concepts from the following text:

"{text}"

Return a JSON object with:
- Medical conditions
- Symptoms
- Vital sign parameters
- Laboratory tests
- Procedures

Format:
{{
  "conditions": ["string"],
  "symptoms": ["string"],
  "vital_signs": ["string"],
  "laboratory_tests": ["string"],
  "procedures": ["string"]
}}
"""
        
        response_text = self._call_llm_with_retry(prompt)
        return self._parse_llm_response(response_text)
    
    def normalize_terminology(self, term: str, terminology_type: str = "auto") -> Dict[str, Any]:
        """
        Normalize medical terminology to standard codes.
        
        Args:
            term: Medical term to normalize
            terminology_type: Type of terminology (snomed, icd10, loinc, auto)
            
        Returns:
            Dictionary with normalized codes
        """
        prompt = f"""Normalize the following medical term: "{term}"

Provide standard medical codes:
- SNOMED CT code (if it's a clinical finding or condition)
- ICD-10 code (if it's a diagnosis)
- LOINC code (if it's a laboratory test or vital sign)

Return JSON:
{{
  "term": "standardized term",
  "snomed_code": "string or empty",
  "icd10_code": "string or empty",
  "loinc_code": "string or empty",
  "term_type": "condition|symptom|vital_sign|laboratory_test|procedure"
}}
"""
        
        response_text = self._call_llm_with_retry(prompt)
        return self._parse_llm_response(response_text)
    
    def identify_thresholds(self, criterion_text: str) -> List[Dict[str, Any]]:
        """
        Identify quantitative thresholds in criterion text.
        
        Args:
            criterion_text: Criterion text
            
        Returns:
            List of threshold dictionaries
        """
        prompt = f"""Identify all quantitative thresholds in this clinical criterion:

"{criterion_text}"

For each threshold, extract:
- Parameter name (e.g., "systolic blood pressure", "temperature")
- Threshold value
- Comparison operator (less_than, greater_than, equals, between)
- Unit
- Clinical significance

Return JSON array:
[
  {{
    "parameter": "string",
    "value": number,
    "operator": "string",
    "unit": "string",
    "clinical_significance": "string"
  }}
]
"""
        
        response_text = self._call_llm_with_retry(prompt)
        parsed = self._parse_llm_response(response_text)
        
        # Handle case where response is not an array
        if isinstance(parsed, dict):
            return []
        return parsed
    
    def analyze_dependencies(self, criterion: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze dependencies and conditional logic in criterion.
        
        Args:
            criterion: Criterion dictionary
            
        Returns:
            Dictionary with dependency analysis
        """
        prompt = f"""Analyze the dependencies and conditional logic in this criterion:

"{criterion['criterion_text']}"

Identify:
1. Conditional requirements (e.g., "if blood cultures performed")
2. Prerequisites
3. Temporal dependencies (e.g., "after observation period")
4. Logical relationships (AND, OR)

Return JSON:
{{
  "has_dependencies": boolean,
  "dependency_type": "conditional|prerequisite|temporal|none",
  "conditions": ["string"],
  "logic_operator": "AND|OR|NONE"
}}
"""
        
        response_text = self._call_llm_with_retry(prompt)
        return self._parse_llm_response(response_text)


def interpret_criteria(parsed_data: Dict[str, Any], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convenience function to interpret criteria.
    
    Args:
        parsed_data: Output from module_2_structure_parser
        config: Configuration dictionary
        
    Returns:
        List of interpreted criteria
    """
    interpreter = LLMInterpreter(config)
    return interpreter.interpret_criteria(parsed_data)


if __name__ == "__main__":
    # Test the module independently
    import yaml
    from module_1_pdf_extraction import extract_pdf_content
    from module_2_structure_parser import parse_admission_criteria
    
    logging.basicConfig(level=logging.INFO)
    
    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Test with sample criterion (without full pipeline)
    try:
        interpreter = LLMInterpreter(config)
        
        # Test with a sample criterion
        sample_criterion = {
            "criterion_id": "test_001",
            "criterion_text": "Hemodynamic instability with systolic blood pressure less than 90 mmHg",
            "primary_condition": "Hemodynamic instability",
            "qualifiers": ["severe"],
            "conditional_requirements": [],
            "persistence_requirement": "",
            "clinical_category": "hemodynamic"
        }
        
        result = interpreter.interpret_criterion(sample_criterion)
        print(f"\nInterpretation test successful!")
        print(f"Primary condition: {result['interpreted_criterion']['primary_condition']['term']}")
        print(f"Clinical findings: {len(result['interpreted_criterion']['related_clinical_findings'])}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
