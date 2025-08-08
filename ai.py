import os, json, requests
DEFAULT_ENDPOINT=os.getenv("OLLAMA_ENDPOINT","http://localhost:11434")
DEFAULT_MODEL=os.getenv("OLLAMA_MODEL","mistral:7b-instruct")
def is_ollama_available()->bool:
    try:
        r=requests.get(DEFAULT_ENDPOINT,timeout=2); return r.status_code<500
    except Exception: return False
def ollama_generate(prompt:str, model:str=None, temp:float=0.6, timeout:int=120)->str:
    model=model or DEFAULT_MODEL
    r=requests.post(f"{DEFAULT_ENDPOINT}/api/generate", json={"model":model,"prompt":prompt,"options":{"temperature":temp},"stream":False}, timeout=timeout)
    r.raise_for_status(); return r.json().get("response","").strip()
def hf_generate(prompt:str, token:str, model:str="mistralai/Mistral-7B-Instruct-v0.2", temp:float=0.6, timeout:int=120)->str:
    api=f"https://api-inference.huggingface.co/models/{model}"
    headers={"Authorization": f"Bearer {token}"}
    payload={"inputs":prompt,"parameters":{"temperature":temp,"max_new_tokens":256,"return_full_text":False}}
    r=requests.post(api,headers=headers,json=payload,timeout=timeout); r.raise_for_status()
    data=r.json()
    if isinstance(data,list) and data and isinstance(data[0],dict):
        for k in ("generated_text","text","output_text"):
            if k in data[0] and isinstance(data[0][k],str): return data[0][k].strip()
    if isinstance(data,dict):
        for k in ("generated_text","text"):
            if k in data and isinstance(data[k],str): return data[k].strip()
    if isinstance(data,str): return data.strip()
    return ""
def judge_json(text:str)->dict:
    try: return json.loads(text)
    except Exception: return {"humor":0,"relevance":0,"shutdown":0,"toxicity":5,"notes":"parse_error"}
