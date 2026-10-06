"""Real SDK request/response contract with an isolated HTTP mock, never live credentials."""
import json
import httpx2 as httpx
import pytest
from openai import OpenAI as SDKClient
from services import ai_provider as provider

TOKEN='synthetic-private-token'


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setattr(provider,'configuration',lambda:provider.Configuration(TOKEN,provider.DEFAULT_MODEL))


def transport(monkeypatch,handler):
    def client(**kwargs):
        assert kwargs['base_url']==provider.BASE_URL and kwargs['api_key']==TOKEN
        assert kwargs['max_retries']==0 and kwargs['timeout']==25
        return SDKClient(**kwargs,http_client=httpx.Client(transport=httpx.MockTransport(handler)))
    monkeypatch.setattr(provider,'OpenAI',client)


def response(request,content='{"result":"ok"}',finish='stop',choices=True):
    body={'id':'test-completion','object':'chat.completion','created':0,'model':provider.DEFAULT_MODEL,
        'choices':[{'index':0,'finish_reason':finish,'message':{'role':'assistant','content':content}}] if choices else []}
    return httpx.Response(200,json=body,request=request)


def test_sdk_sends_token_only_in_server_auth_header_and_preserves_schema(monkeypatch,configured):
    def handler(request):
        assert str(request.url)=='https://router.huggingface.co/v1/chat/completions'
        assert request.headers['authorization']=='Bearer '+TOKEN
        body=json.loads(request.content)
        assert TOKEN not in json.dumps(body)
        assert body['model']==provider.DEFAULT_MODEL
        assert body['response_format']['json_schema']['strict'] is True
        assert body['max_completion_tokens']==2048 and body['stream'] is False
        return response(request)
    transport(monkeypatch,handler)
    assert provider.generate([{'role':'user','content':'Return JSON'}],{'type':'object'})=='{"result":"ok"}'


@pytest.mark.parametrize('code',[400,401,402,403,404,422,429,500,503])
def test_upstream_failures_never_leak_body_headers_or_token(monkeypatch,configured,code):
    calls=[]
    def handler(request):
        calls.append(request)
        return httpx.Response(code,json={'error':{'message':TOKEN,'type':'upstream_error'}},request=request)
    transport(monkeypatch,handler)
    with pytest.raises(provider.AIUnavailable) as caught:provider.generate([{'role':'user','content':'Test'}])
    assert TOKEN not in str(caught.value) and len(calls)==1


@pytest.mark.parametrize('error',[httpx.ConnectError,httpx.ReadTimeout])
def test_network_and_timeout_failures_are_safe_without_retries(monkeypatch,configured,error):
    calls=[]
    def handler(request):
        calls.append(request);raise error(TOKEN,request=request)
    transport(monkeypatch,handler)
    with pytest.raises(provider.AIUnavailable) as caught:provider.generate([{'role':'user','content':'Test'}])
    assert TOKEN not in str(caught.value) and len(calls)==1


@pytest.mark.parametrize('content,finish,choices',[(None,'stop',True),('','stop',True),('partial','length',True),('refused','content_filter',True),('text','stop',False),(TOKEN,'stop',True)])
def test_empty_refused_truncated_or_credential_echo_is_rejected(monkeypatch,configured,content,finish,choices):
    transport(monkeypatch,lambda request:response(request,content,finish,choices))
    with pytest.raises(provider.AIUnavailable) as caught:provider.generate([{'role':'user','content':'Test'}])
    assert TOKEN not in str(caught.value)


def test_missing_token_does_not_make_request(monkeypatch):
    monkeypatch.setattr(provider,'configuration',lambda:provider.Configuration(''))
    monkeypatch.setattr(provider,'OpenAI',lambda **kwargs:pytest.fail('Missing credentials must not call SDK'))
    with pytest.raises(provider.AIUnavailable,match='HF_TOKEN'):provider.generate([{'role':'user','content':'Test'}])


def test_request_limits_and_private_credential_input_never_make_request(monkeypatch,configured):
    monkeypatch.setattr(provider,'OpenAI',lambda **kwargs:pytest.fail('Invalid input must not call SDK'))
    for content in ['x'*24001,TOKEN]:
        with pytest.raises(provider.AIUnavailable):provider.generate([{'role':'user','content':content}])


def test_environment_precedence_and_redacted_configuration(monkeypatch,tmp_path):
    monkeypatch.setattr(provider,'ROOT',tmp_path)
    (tmp_path/'.env').write_text('HF_TOKEN=local-synthetic-token\nHF_MODEL=openai/gpt-oss-120b:groq\n',encoding='utf-8')
    monkeypatch.setenv('HF_TOKEN',TOKEN);monkeypatch.setenv('HF_MODEL','openai/gpt-oss-120b:fastest')
    config=provider.configuration()
    assert config.token==TOKEN and config.model.endswith(':fastest')
    assert TOKEN not in repr(config) and TOKEN not in json.dumps(provider.status())


def test_invalid_model_configuration_is_safe(monkeypatch,tmp_path):
    monkeypatch.setattr(provider,'ROOT',tmp_path)
    monkeypatch.setenv('HF_MODEL','invalid private model configuration')
    assert not provider.status()['available']
    assert 'invalid private model configuration' not in json.dumps(provider.status())
