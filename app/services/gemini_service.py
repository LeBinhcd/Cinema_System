"""OpenAI-compatible gateway for Claude models."""
from __future__ import annotations
import json, logging, math, os
from typing import Optional
from urllib.request import Request, urlopen

AI_TIMEOUT_SECONDS=60
GEMINI_TIMEOUT_SECONDS=AI_TIMEOUT_SECONDS
GROQ_TIMEOUT_SECONDS=AI_TIMEOUT_SECONDS
DEFAULT_AI_BASE_URL='https://api.xpiki.com/v1'
DEFAULT_AI_MODEL='claude-haiku-4-5'
DEFAULT_GROQ_MODEL=DEFAULT_AI_MODEL
API_ERROR_MESSAGE='Xin lỗi, hiện chưa thể xử lý yêu cầu. Vui lòng thử lại sau.'
CONFIG_ERROR_MESSAGE='Xin lỗi, dịch vụ tư vấn hiện chưa được cấu hình. Vui lòng thử lại sau.'
logger=logging.getLogger(__name__)

def _extract_text(payload):
    choices=payload.get('choices') if isinstance(payload,dict) else None
    if not isinstance(choices,list) or not choices: raise ValueError('compatible API returned no choices')
    content=choices[0].get('message',{}).get('content')
    if isinstance(content,list): content=''.join(x.get('text','') for x in content if isinstance(x,dict))
    if not isinstance(content,str) or not content.strip(): raise ValueError('compatible API returned empty content')
    return content.strip()

class GeminiService:
    def __init__(self, api_key:Optional[str]=None, model_name:Optional[str]=None, timeout:int=AI_TIMEOUT_SECONDS):
        self.api_key=api_key if api_key is not None else os.getenv('OPENAI_COMPATIBLE_API_KEY','')
        self.base_url=os.getenv('OPENAI_COMPATIBLE_BASE_URL',DEFAULT_AI_BASE_URL).rstrip('/')
        self.model_name=model_name if model_name is not None else os.getenv('OPENAI_COMPATIBLE_MODEL',DEFAULT_AI_MODEL)
        if isinstance(timeout,bool) or not isinstance(timeout,(int,float)) or not math.isfinite(timeout) or timeout<=0: raise ValueError('timeout must be positive')
        self.timeout=min(timeout,AI_TIMEOUT_SECONDS)
    def generate_response(self,prompt:str)->str:
        if not isinstance(prompt,str) or not prompt.strip(): raise ValueError('prompt must be a non-empty string')
        if not self.api_key or not self.model_name or not self.base_url: return CONFIG_ERROR_MESSAGE
        body=json.dumps({'model':self.model_name,'messages':[{'role':'user','content':prompt}],'temperature':0.3,'max_tokens':800}).encode()
        req=Request(self.base_url+'/chat/completions',data=body,headers={'Authorization':'Bearer '+self.api_key,'Content-Type':'application/json','Accept':'application/json'},method='POST')
        try:
            logger.info("[AI ->] provider=openai-compatible base=%s model=%s prompt_chars=%d", self.base_url, self.model_name, len(prompt))
            started = __import__('time').perf_counter()
            with urlopen(req,timeout=self.timeout) as response:
                text = _extract_text(json.loads(response.read().decode('utf-8')))
            logger.info("[AI <-] provider=openai-compatible status=200 duration_ms=%.1f response_chars=%d", (__import__('time').perf_counter()-started)*1000, len(text))
            return text
        except Exception as error:
            detail=str(error).replace(self.api_key,'<API_KEY_REDACTED>').replace(prompt,'<PROMPT_REDACTED>')
            logger.error('[OPENAI-COMPATIBLE ERROR]: %s - %s',type(error).__name__,detail)
            return API_ERROR_MESSAGE
    def generate(self,prompt:str)->str: return self.generate_response(prompt)

def generate_response(prompt:str)->str: return GeminiService().generate_response(prompt)
