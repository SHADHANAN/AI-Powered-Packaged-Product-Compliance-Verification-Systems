"""AI Service module for structured Legal Metrology compliance evaluation."""
import json
import logging
from typing import Any, Dict, List

import httpx

from app.config import get_settings
from app.ai.prompt import format_compliance_prompt, format_ocr_interpretation_prompt

logger = logging.getLogger(__name__)


class AIServiceException(Exception):
    """Exception raised for errors in the AI service."""
    pass


class AIService:
    """Modular AI service for packaged commodity compliance checks.
    
    Supports mock, Gemini, and OpenAI providers, handles timeouts, network failures,
    and returns parsed, structured compliance evaluation JSON lists.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    def evaluate_compliance(self, fields: Dict[str, str], rules: List[Any]) -> List[Dict[str, Any]]:
        """Evaluate compliance rules using the configured AI provider.
        
        Args:
            fields: Dict of extracted label fields (field name -> value).
            rules: List of registered ComplianceRule objects.
            
        Returns:
            A list of rule evaluation dictionaries.
            
        Raises:
            AIServiceException: If the API call fails or parsing fails.
        """
        provider = self.settings.AI_PROVIDER.lower().strip()
        
        if provider == "mock":
            logger.info("Executing compliance evaluation using MOCK AI provider.")
            return self._evaluate_mock(fields, rules)
        elif provider == "gemini":
            logger.info("Executing compliance evaluation using GEMINI AI provider.")
            return self._evaluate_gemini(fields, rules)
        elif provider == "openai":
            logger.info("Executing compliance evaluation using OPENAI AI provider.")
            return self._evaluate_openai(fields, rules)
        else:
            raise AIServiceException(f"Unsupported AI provider: {provider}")

    def _evaluate_mock(self, fields: Dict[str, str], rules: List[Any]) -> List[Dict[str, Any]]:
        """Mock AI provider that runs deterministic rules locally and formats as LLM JSON response."""
        results = []
        for rule in rules:
            res = rule.evaluate(fields)
            
            # Map status and severity to string representations
            status_val = res.status.value if hasattr(res.status, "value") else str(res.status)
            severity_val = res.severity.value if hasattr(res.severity, "value") else str(res.severity)
            
            results.append({
                "rule_code": res.rule_code,
                "rule_name": res.rule_name,
                "status": status_val,
                "severity": severity_val,
                "message": res.message,
                "expected_value": res.expected_value,
                "actual_value": res.actual_value,
                "recommendation": res.recommendation,
            })
        return results

    def _evaluate_gemini(self, fields: Dict[str, str], rules: List[Any]) -> List[Dict[str, Any]]:
        """Call Gemini API to evaluate compliance."""
        api_key = self.settings.AI_API_KEY
        if not api_key:
            raise AIServiceException("Gemini API key is not configured in environment variables.")
        
        prompt_text = format_compliance_prompt(fields, rules)
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.settings.AI_MODEL}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt_text
                }]
            }],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": self.settings.AI_TEMPERATURE
            }
        }
        
        try:
            with httpx.Client(timeout=self.settings.AI_TIMEOUT_SECONDS) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                res_data = response.json()
                
                candidates = res_data.get("candidates", [])
                if not candidates:
                    raise AIServiceException("No response candidates returned from Gemini API.")
                
                content_parts = candidates[0].get("content", {}).get("parts", [])
                if not content_parts:
                    raise AIServiceException("Empty content parts in Gemini API response.")
                
                text_content = content_parts[0].get("text", "")
                return self._parse_json_response(text_content)
        except httpx.HTTPError as e:
            raise AIServiceException(f"Gemini API HTTP request failed: {e}")
        except Exception as e:
            raise AIServiceException(f"Failed to process Gemini API response: {e}")

    def _evaluate_openai(self, fields: Dict[str, str], rules: List[Any]) -> List[Dict[str, Any]]:
        """Call OpenAI API to evaluate compliance."""
        api_key = self.settings.AI_API_KEY
        if not api_key:
            raise AIServiceException("OpenAI API key is not configured in environment variables.")
        
        prompt_text = format_compliance_prompt(fields, rules)
        
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        payload = {
            "model": self.settings.AI_MODEL,
            "messages": [
                {"role": "user", "content": prompt_text}
            ],
            "response_format": {"type": "json_object"},
            "temperature": self.settings.AI_TEMPERATURE
        }
        
        try:
            with httpx.Client(timeout=self.settings.AI_TIMEOUT_SECONDS) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                res_data = response.json()
                
                choices = res_data.get("choices", [])
                if not choices:
                    raise AIServiceException("No choices returned from OpenAI API.")
                
                text_content = choices[0].get("message", {}).get("content", "")
                return self._parse_json_response(text_content)
        except httpx.HTTPError as e:
            raise AIServiceException(f"OpenAI API HTTP request failed: {e}")
        except Exception as e:
            raise AIServiceException(f"Failed to process OpenAI API response: {e}")

    def _parse_json_response(self, text_content: str) -> List[Dict[str, Any]]:
        """Parse text response from AI API ensuring valid JSON format."""
        text_content = text_content.strip()
        
        # Remove markdown code block wrappers if present
        if text_content.startswith("```"):
            lines = text_content.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text_content = "\n".join(lines).strip()
            
        try:
            data = json.loads(text_content)
        except json.JSONDecodeError as e:
            raise AIServiceException(f"AI returned invalid JSON: {e}. Output was: {text_content}")
            
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # If the JSON response is wrapped in an object, find the first list value inside it
            for val in data.values():
                if isinstance(val, list):
                    return val
            raise AIServiceException("JSON object returned, but could not find rule evaluations list inside it.")
        else:
            raise AIServiceException("AI response did not parse into a valid JSON array or object.")

    def interpret_ocr(self, raw_text: str, deterministic_fields: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Interpret raw OCR text fields with AI assistance.
        
        Args:
            raw_text: The complete raw OCR text.
            deterministic_fields: Extracted fields from deterministic extraction.
            
        Returns:
            A list of interpreted field dictionaries.
            
        Raises:
            AIServiceException: If the AI provider fails.
        """
        provider = self.settings.AI_PROVIDER.lower().strip()
        
        if provider == "mock":
            logger.info("Executing OCR interpretation using MOCK AI provider.")
            return self._interpret_ocr_mock(raw_text, deterministic_fields)
        elif provider == "gemini":
            logger.info("Executing OCR interpretation using GEMINI AI provider.")
            return self._interpret_ocr_gemini(raw_text, deterministic_fields)
        elif provider == "openai":
            logger.info("Executing OCR interpretation using OPENAI AI provider.")
            return self._interpret_ocr_openai(raw_text, deterministic_fields)
        else:
            raise AIServiceException(f"Unsupported AI provider: {provider}")

    def _interpret_ocr_mock(self, raw_text: str, deterministic_fields: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Mock AI provider for OCR interpretation."""
        results = []
        raw_lower = raw_text.lower()
        
        det_map = {f["field_name"]: f for f in deterministic_fields}
        
        all_possible_fields = [
            "mrp", "net_quantity", "quantity_unit", "batch_number",
            "manufacturing_date", "import_date", "country_of_origin",
            "manufacturer", "manufacturer_address", "importer", "importer_address",
            "customer_care_details", "product_name", "brand_name"
        ]
        
        if not raw_text.strip():
            for f_name in all_possible_fields:
                results.append({
                    "field": f_name,
                    "original_ocr_value": None,
                    "interpreted_value": None,
                    "confidence": 0.0,
                    "evidence": None,
                    "short_reason": "No OCR text provided.",
                    "status": "UNRESOLVED"
                })
            return results

        is_low_conf = "smudge" in raw_lower or "unreadable" in raw_lower or "poor" in raw_lower
        has_ambiguous_mrp = "1o0" in raw_lower or "l00" in raw_lower
        
        for f_name in all_possible_fields:
            det = det_map.get(f_name)
            original_val = det["field_value"] if det else None
            evidence = det["source_text"] if det else None
            
            if is_low_conf:
                results.append({
                    "field": f_name,
                    "original_ocr_value": original_val,
                    "interpreted_value": original_val,
                    "confidence": 0.3,
                    "evidence": evidence,
                    "short_reason": "OCR text is smudged/unreadable.",
                    "status": "NEEDS_REVIEW"
                })
            elif f_name == "mrp" and has_ambiguous_mrp:
                results.append({
                    "field": "mrp",
                    "original_ocr_value": "1O0",
                    "interpreted_value": "100.00",
                    "confidence": 0.95,
                    "evidence": "MRP: Rs. 1O0",
                    "short_reason": "Corrected letter 'O' to number '0' in price.",
                    "status": "COMPLETED"
                })
            elif f_name == "mrp" and original_val:
                results.append({
                    "field": "mrp",
                    "original_ocr_value": original_val,
                    "interpreted_value": f"{float(original_val.replace('Rs', '').replace('/-', '').strip()):.2f}" if original_val.replace('Rs', '').replace('/-', '').strip().replace('.', '', 1).isdigit() else original_val,
                    "confidence": 0.98,
                    "evidence": evidence,
                    "short_reason": "Normalized MRP format",
                    "status": "COMPLETED"
                })
            elif det:
                results.append({
                    "field": f_name,
                    "original_ocr_value": original_val,
                    "interpreted_value": original_val,
                    "confidence": det.get("confidence", 0.9),
                    "evidence": evidence,
                    "short_reason": "Extracted with high confidence via pattern matching.",
                    "status": "COMPLETED"
                })
            else:
                results.append({
                    "field": f_name,
                    "original_ocr_value": None,
                    "interpreted_value": None,
                    "confidence": 0.0,
                    "evidence": None,
                    "short_reason": "Field not present in OCR text.",
                    "status": "UNRESOLVED"
                })
                
        return results

    def _interpret_ocr_gemini(self, raw_text: str, deterministic_fields: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Call Gemini API for OCR interpretation."""
        api_key = self.settings.AI_API_KEY
        if not api_key:
            raise AIServiceException("Gemini API key is not configured in environment variables.")
        
        prompt_text = format_ocr_interpretation_prompt(raw_text, deterministic_fields)
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.settings.AI_MODEL}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt_text
                }]
            }],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": self.settings.AI_TEMPERATURE
            }
        }
        
        try:
            with httpx.Client(timeout=self.settings.AI_TIMEOUT_SECONDS) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                res_data = response.json()
                
                candidates = res_data.get("candidates", [])
                if not candidates:
                    raise AIServiceException("No response candidates returned from Gemini API.")
                
                content_parts = candidates[0].get("content", {}).get("parts", [])
                if not content_parts:
                    raise AIServiceException("Empty content parts in Gemini API response.")
                
                text_content = content_parts[0].get("text", "")
                return self._parse_json_response(text_content)
        except httpx.HTTPError as e:
            raise AIServiceException(f"Gemini API HTTP request failed: {e}")
        except Exception as e:
            raise AIServiceException(f"Failed to process Gemini API response: {e}")

    def _interpret_ocr_openai(self, raw_text: str, deterministic_fields: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Call OpenAI API for OCR interpretation."""
        api_key = self.settings.AI_API_KEY
        if not api_key:
            raise AIServiceException("OpenAI API key is not configured in environment variables.")
        
        prompt_text = format_ocr_interpretation_prompt(raw_text, deterministic_fields)
        
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        payload = {
            "model": self.settings.AI_MODEL,
            "messages": [
                {"role": "user", "content": prompt_text}
            ],
            "response_format": {"type": "json_object"},
            "temperature": self.settings.AI_TEMPERATURE
        }
        
        try:
            with httpx.Client(timeout=self.settings.AI_TIMEOUT_SECONDS) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                res_data = response.json()
                
                choices = res_data.get("choices", [])
                if not choices:
                    raise AIServiceException("No choices returned from OpenAI API.")
                
                text_content = choices[0].get("message", {}).get("content", "")
                return self._parse_json_response(text_content)
        except httpx.HTTPError as e:
            raise AIServiceException(f"OpenAI API HTTP request failed: {e}")
        except Exception as e:
            raise AIServiceException(f"Failed to process OpenAI API response: {e}")

    def generate_text(self, prompt: str) -> str:
        """Call configured AI provider to generate raw text response.
        
        Args:
            prompt: The formatted prompt to send to the provider.
            
        Returns:
            The raw text response from the provider.
            
        Raises:
            AIServiceException: If the AI provider fails.
        """
        provider = self.settings.AI_PROVIDER.lower().strip()
        
        if provider == "mock":
            logger.info("Executing text generation using MOCK AI provider.")
            return self._generate_text_mock(prompt)
        elif provider == "gemini":
            logger.info("Executing text generation using GEMINI AI provider.")
            return self._generate_text_gemini(prompt)
        elif provider == "openai":
            logger.info("Executing text generation using OPENAI AI provider.")
            return self._generate_text_openai(prompt)
        else:
            raise AIServiceException(f"Unsupported AI provider: {provider}")

    def _generate_text_mock(self, prompt: str) -> str:
        """Mock text generator."""
        if "Status: COMPLIANT" in prompt:
            return "Mock AI: The product satisfies all Legal Metrology packaged commodity regulations. No missing declarations or warnings detected."
        elif "Status: PARTIALLY_COMPLIANT" in prompt:
            return "Mock AI: The product is partially compliant but contains some warnings that require manual verification."
        else:
            return "Mock AI: The product has failed compliance verification because one or more mandatory declarations are missing or invalid."

    def _generate_text_gemini(self, prompt: str) -> str:
        """Call Gemini API for text generation."""
        api_key = self.settings.AI_API_KEY
        if not api_key:
            raise AIServiceException("Gemini API key is not configured in environment variables.")
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.settings.AI_MODEL}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": self.settings.AI_TEMPERATURE
            }
        }
        
        try:
            with httpx.Client(timeout=self.settings.AI_TIMEOUT_SECONDS) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                res_data = response.json()
                
                candidates = res_data.get("candidates", [])
                if not candidates:
                    raise AIServiceException("No response candidates returned from Gemini API.")
                
                content_parts = candidates[0].get("content", {}).get("parts", [])
                if not content_parts:
                    raise AIServiceException("Empty content parts in Gemini API response.")
                
                return content_parts[0].get("text", "").strip()
        except httpx.HTTPError as e:
            raise AIServiceException(f"Gemini API HTTP request failed: {e}")
        except Exception as e:
            raise AIServiceException(f"Failed to process Gemini API response: {e}")

    def _generate_text_openai(self, prompt: str) -> str:
        """Call OpenAI API for text generation."""
        api_key = self.settings.AI_API_KEY
        if not api_key:
            raise AIServiceException("OpenAI API key is not configured in environment variables.")
        
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        payload = {
            "model": self.settings.AI_MODEL,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": self.settings.AI_TEMPERATURE
        }
        
        try:
            with httpx.Client(timeout=self.settings.AI_TIMEOUT_SECONDS) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                res_data = response.json()
                
                choices = res_data.get("choices", [])
                if not choices:
                    raise AIServiceException("No choices returned from OpenAI API.")
                
                return choices[0].get("message", {}).get("content", "").strip()
        except httpx.HTTPError as e:
            raise AIServiceException(f"OpenAI API HTTP request failed: {e}")
        except Exception as e:
            raise AIServiceException(f"Failed to process OpenAI API response: {e}")
