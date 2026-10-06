"""Server-only Hugging Face router boundary; never expose SDK errors or credentials."""
from dataclasses import dataclass,field
import json
import os
import re
from pathlib import Path
from openai import OpenAI,APIError,APIConnectionError,APITimeoutError,APIStatusError
from config import ROOT

BASE_URL='https://router.huggingface.co/v1'
DEFAULT_MODEL='openai/gpt-oss-120b:groq'
TIMEOUT_SECONDS=25
MAX_PROMPT_BYTES=24000
MAX_OUTPUT_TOKENS=2048


class AIUnavailable(RuntimeError):
    """Safe public message; no upstream body, headers, paths or tokens."""


@dataclass(frozen=True)
class Configuration:
    token:str=field(repr=False)
    model:str=DEFAULT_MODEL


def configuration():
    # Deliberately read only these server-side names, with no interpolation/eval.
    values={}
    path=ROOT/'.env'
    if path.is_file():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            name,separator,value=line.partition('=')
            if separator and name.strip() in {'HF_TOKEN','HF_MODEL'}:
                values[name.strip()]=value.strip().strip('"').strip("'")
    token=os.environ.get('HF_TOKEN',values.get('HF_TOKEN','')).strip()
    model=os.environ.get('HF_MODEL',values.get('HF_MODEL',DEFAULT_MODEL)).strip()
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?::[a-z0-9-]+)?',model) or len(model)>128 or (token and token in model):
        raise AIUnavailable('HF_MODEL must be a supported repository/model with an optional provider or routing suffix.')
    return Configuration(token=token,model=model)


def status():
    try:
        config=configuration()
        available=bool(config.token) and config.token!='<YOUR_LOCAL_HF_TOKEN>'
        return {'available':available,'provider':'Hugging Face Inference Providers','model':config.model,
            'routing':config.model.partition(':')[2] or 'fastest','base_url':BASE_URL,
            'reason':'Hugging Face narration is configured. Use an explicit AI action to verify the connection.' if available else
                'Set HF_TOKEN in the ignored local .env or server environment. Local calculated evidence remains available.'}
    except (AIUnavailable,OSError,UnicodeError):
        return {'available':False,'provider':'Hugging Face Inference Providers','model':DEFAULT_MODEL,
            'routing':'groq','base_url':BASE_URL,'reason':'AI configuration is invalid or unreadable. Check HF_TOKEN and HF_MODEL locally.'}


def generate(messages,schema=None):
    """One bounded request, no automatic retries, no mock/provider fallback."""
    try:
        config=configuration()
    except (OSError,UnicodeError):
        raise AIUnavailable('AI configuration is unreadable. Check the local environment.') from None
    if not config.token or config.token=='<YOUR_LOCAL_HF_TOKEN>':
        raise AIUnavailable('Set HF_TOKEN in the ignored local .env or server environment before generating AI insights.')
    if not isinstance(messages,list) or not messages or any(not isinstance(m,dict) or m.get('role') not in {'system','user','assistant'} or not isinstance(m.get('content'),str) for m in messages):
        raise AIUnavailable('AI request is invalid. Rebuild the analysis and retry.')
    if len(json.dumps(messages,ensure_ascii=False).encode('utf-8'))>MAX_PROMPT_BYTES:
        raise AIUnavailable('The analysis exceeds the AI request limit. Select fewer measures or shorten the question.')
    if any(config.token in m['content'] for m in messages):
        raise AIUnavailable('The request contains a private credential and cannot be submitted.')
    arguments={'model':config.model,'messages':messages,'max_completion_tokens':MAX_OUTPUT_TOKENS,'stream':False}
    if config.model.startswith('openai/gpt-oss-'):
        arguments['reasoning_effort']='low'
    if schema is not None:
        arguments['response_format']={'type':'json_schema','json_schema':{'name':'supplychain_insights','strict':True,'schema':schema}}
    try:
        with OpenAI(base_url=BASE_URL,api_key=config.token,timeout=TIMEOUT_SECONDS,max_retries=0) as client:
            response=client.chat.completions.create(**arguments)
        if not response.choices or response.choices[0].finish_reason!='stop' or getattr(response.choices[0].message,'refusal',None):
            raise AIUnavailable('The AI response was empty, interrupted or refused. Retry the same analysis later.')
        content=response.choices[0].message.content
        if not isinstance(content,str) or not content.strip():
            raise AIUnavailable('The AI returned no usable answer. Retry later; local evidence remains available.')
        if len(content.encode('utf-8'))>200000 or config.token in content:
            raise AIUnavailable('The AI response did not pass safety validation. Local evidence remains available.')
        if schema is not None:
            try:
                decoded=json.loads(content)
            except (json.JSONDecodeError,ValueError):
                raise AIUnavailable('The AI returned malformed JSON. Retry later; local evidence remains available.') from None
            if config.token in json.dumps(decoded,ensure_ascii=False):
                raise AIUnavailable('The AI response did not pass safety validation. Local evidence remains available.')
        return content
    except APITimeoutError:
        raise AIUnavailable('The AI request timed out. Retry later; local results remain available.') from None
    except APIConnectionError:
        raise AIUnavailable('The AI request could not connect. Check connectivity and retry later.') from None
    except APIStatusError as exc:
        reasons={400:'The model/provider rejected the request format. Check the selected HF_MODEL configuration.',
            401:'HF_TOKEN was rejected. Check the private local token configuration.',
            402:'Hugging Face inference credits are exhausted. Check your account before retrying.',
            403:'HF_TOKEN cannot access this provider/model. Check Inference Providers permission.',
            404:'The selected model/provider is unavailable. Check current Hugging Face routing.',
            422:'The model/provider could not accept this structured request.',
            429:'Hugging Face/provider rate limit or quota reached. Wait before retrying.'}
        raise AIUnavailable(reasons.get(exc.status_code,'The Hugging Face provider is unavailable. Retry later; local results remain available.')) from None
    except AIUnavailable:
        raise
    except (APIError,ValueError,TypeError,AttributeError,OSError):
        raise AIUnavailable('The AI response was unexpected. Retry later; local results remain available.') from None
