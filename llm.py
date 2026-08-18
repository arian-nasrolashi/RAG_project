from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import json
import logging
from typing import Optional, Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class Question(BaseModel):
    question: str

class OllamaResponse(BaseModel):
    response: str
    model: str
    created_at: str
    done: bool

# Configuration
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:3b"
TIMEOUT = 60  # seconds
MAX_RETRIES = 3

def check_ollama_health() -> bool:
    """Check if Ollama service is running"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

def get_available_models() -> list:
    """Get list of available models from Ollama"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
    except:
        pass
    return []

def generate_response(prompt: str, temperature: float = 0.7, max_tokens: int = 512) -> str:
    """
    Generate response using Ollama with Qwen2.5 3B
    """
    # Check if Ollama is running
    if not check_ollama_health():
        raise HTTPException(
            status_code=503,
            detail="Ollama service is not running. Please start Ollama with: ollama serve"
        )
    
    # Check if model is available
    available_models = get_available_models()
    if OLLAMA_MODEL not in available_models:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{OLLAMA_MODEL}' not found. Please pull it with: ollama pull {OLLAMA_MODEL}"
        )
    
    # Prepare the payload
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "top_p": 0.9,
            "top_k": 40,
            "max_tokens": max_tokens,
            "repeat_penalty": 1.1,
            "stop": ["\n\nHuman:", "\n\nUser:"]
        }
    }
    
    # Make the request with retries
    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"Generating response (attempt {attempt + 1}/{MAX_RETRIES})...")
            
            response = requests.post(
                OLLAMA_URL,
                json=payload,
                timeout=TIMEOUT,
                headers={"Content-Type": "application/json"}
            )
            
            response.raise_for_status()
            
            result = response.json()
            generated_text = result.get("response", "")
            
            if not generated_text:
                raise ValueError("Empty response from Ollama")
            
            logger.info(f"Response generated successfully ({len(generated_text)} chars)")
            return generated_text.strip()
            
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout on attempt {attempt + 1}")
            if attempt == MAX_RETRIES - 1:
                raise HTTPException(
                    status_code=504,
                    detail=f"Request timed out after {TIMEOUT} seconds"
                )
                
        except requests.exceptions.ConnectionError:
            logger.error("Connection error to Ollama")
            raise HTTPException(
                status_code=503,
                detail="Cannot connect to Ollama. Make sure it's running on localhost:11434"
            )
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            if attempt == MAX_RETRIES - 1:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error communicating with Ollama: {str(e)}"
                )
                
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error: {str(e)}"
            )
    
    raise HTTPException(status_code=500, detail="Max retries exceeded")

@app.post("/search")
def search_api(data: Question):
    """
    Search endpoint that uses Qwen2.5 3B via Ollama
    """
    try:
        logger.info(f"Received question: {data.question}")
        
        # Generate response
        results = generate_response(data.question)
        
        return {
            "question": data.question,
            "results": results,
            "model_used": OLLAMA_MODEL,
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in search_api: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    """
    Health check endpoint
    """
    ollama_running = check_ollama_health()
    available_models = get_available_models() if ollama_running else []
    
    return {
        "status": "healthy" if ollama_running else "unhealthy",
        "ollama_running": ollama_running,
        "model_available": OLLAMA_MODEL in available_models,
        "available_models": available_models,
        "model": OLLAMA_MODEL,
        "service": "Ollama + Qwen2.5 3B"
    }

@app.get("/models")
def list_models():
    """
    List available models in Ollama
    """
    try:
        available_models = get_available_models()
        return {
            "available_models": available_models,
            "current_model": OLLAMA_MODEL,
            "is_available": OLLAMA_MODEL in available_models
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_with_params")
def generate_with_params(data: Question, temperature: float = 0.7, max_tokens: int = 512):
    """
    Generate with custom parameters
    """
    try:
        results = generate_response(data.question, temperature, max_tokens)
        return {
            "question": data.question,
            "results": results,
            "parameters": {
                "temperature": temperature,
                "max_tokens": max_tokens,
                "model": OLLAMA_MODEL
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    """
    Root endpoint with API information
    """
    return {
        "service": "Qwen2.5 3B API via Ollama",
        "endpoints": {
            "/search": "POST - Send a question and get response",
            "/health": "GET - Check service health",
            "/models": "GET - List available models",
            "/generate_with_params": "POST - Generate with custom parameters"
        },
        "model": OLLAMA_MODEL,
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    
    # Check if Ollama is running before starting
    if not check_ollama_health():
        logger.warning("Ollama is not running!")
        logger.warning("Please start Ollama with: ollama serve")
        logger.warning(f"Then pull the model: ollama pull {OLLAMA_MODEL}")
    
    logger.info(f"Starting FastAPI server with model: {OLLAMA_MODEL}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )