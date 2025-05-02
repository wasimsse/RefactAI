from typing import Dict, Any
import logging
from gptlab_integration import (
    get_gptlab_client,
    get_gptlab_models,
    normalize_model_name,
    GPTLAB_ENDPOINTS
)

logger = logging.getLogger(__name__)

def detect_code_smells(
    code: str,
    model_name: str = "llama3.2",
    endpoint: str = "RANDOM"
) -> Dict[str, Any]:
    """
    Detect code smells in the provided code using GPT-Lab API.
    
    Args:
        code (str): The source code to analyze
        model_name (str): Name of the model to use for analysis
        endpoint (str): GPT-Lab endpoint to use
        
    Returns:
        Dict containing:
        - smells: List of detected code smells
        - metrics: Code quality metrics
        - reasoning: Explanation for each smell
        - evidence: Evidence for metrics
    """
    try:
        # Get GPT-Lab client
        client = get_gptlab_client(endpoint)
        
        # Get available models and normalize model name
        available_models = get_gptlab_models()
        model = normalize_model_name(model_name)
        if not model:
            return {
                "error": f"Model {model_name} not found",
                "smells": [],
                "metrics": {},
                "reasoning": {},
                "evidence": {}
            }
            
        # Construct analysis prompt
        prompt = f"""Analyze the following code for code smells and quality metrics. Provide a structured response with:
1. List of code smells detected
2. Code quality metrics (complexity, cohesion, coupling)
3. Reasoning for each smell
4. Evidence supporting the metrics

Code to analyze:
{code}

Provide output in JSON format with the following structure:
{{
    "smells": ["smell1", "smell2"],
    "metrics": {{"complexity": "value", "cohesion": "value", "coupling": "value"}},
    "reasoning": {{"smell1": "explanation", "smell2": "explanation"}},
    "evidence": {{"complexity": "evidence", "cohesion": "evidence", "coupling": "evidence"}}
}}"""

        # Make API request
        response = client.chat.completions.create(
            model=model,
            messages=[{
                "role": "user",
                "content": prompt
            }],
            temperature=0.1,
            max_tokens=4096
        )
        
        # Extract JSON from response text
        response_text = response.choices[0].message.content
        
        try:
            # Find JSON object in response using regex
            import json
            import re
            json_match = re.search(r'({.*})', response_text, re.DOTALL)
            if json_match:
                analysis_results = json.loads(json_match.group(1))
                return {
                    "smells": analysis_results.get("smells", []),
                    "metrics": analysis_results.get("metrics", {}),
                    "reasoning": analysis_results.get("reasoning", {}),
                    "evidence": analysis_results.get("evidence", {})
                }
            else:
                logger.error("No JSON found in response")
                return {
                    "error": "Could not parse analysis results",
                    "smells": [],
                    "metrics": {},
                    "reasoning": {},
                    "evidence": {}
                }
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return {
                "error": f"Invalid JSON response: {e}",
                "smells": [],
                "metrics": {},
                "reasoning": {},
                "evidence": {}
            }
            
    except Exception as e:
        logger.error(f"Error in detect_code_smells: {e}")
        return {
            "error": str(e),
            "smells": [],
            "metrics": {},
            "reasoning": {},
            "evidence": {}
        } 