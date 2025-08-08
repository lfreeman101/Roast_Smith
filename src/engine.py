from __future__ import annotations
import random, textwrap, os
from typing import Dict, List, Any, Optional
import yaml
DEFAULT_PACK=os.path.join(os.path.dirname(__file__),"..","content","packs","base_sardonic_v1.yaml")
def load_pack(path: Optional[str]=None)->Dict[str,Any]:
    path=path or DEFAULT_PACK
    with open(path,"r",encoding="utf-8") as f: return yaml.safe_load(f)
def choose(arr:List[str],k:int=1)->List[str]:
    if not arr: return []
    k=max(0,min(k,len(arr)))
    return random.sample(arr,k) if k>0 else []
def pick_slot(pack:Dict[str,Any],slot:str,style:str,fallback:str="intelligent")->List[str]:
    slots=pack.get("slots",{}); by_style=slots.get(slot,{})
    if isinstance(by_style,dict):
        arr=by_style.get(style,None)
        if arr is None: arr=by_style.get(fallback,[])
        return arr or []
    return []
def pick_callouts(pack:Dict[str,Any], detector_ids:List[str])->List[str]:
    out=[]; callouts=pack.get("slots",{}).get("callout",{})
    for did in detector_ids or []:
        arr=callouts.get(did,[])
        if arr: out+=choose(arr,1)
    return out[:2]
def build_threebeat(pack:Dict[str,Any], style:str, detector_ids:List[str], intensity:int)->str:
    intro=choose(pick_slot(pack,"intro",style),1)
    call_or_body=pick_callouts(pack,detector_ids) or choose(pick_slot(pack,"body",style),1)
    body=choose(pick_slot(pack,"body",style),1+(1 if intensity>=8 else 0))
    outro=choose(pick_slot(pack,"outro",style),1)
    return textwrap.fill(" ".join(intro+call_or_body+body+outro), width=92)
def build_oneliner(pack:Dict[str,Any], style:str, detector_ids:List[str], intensity:int)->str:
    intro=choose(pick_slot(pack,"intro",style),1)
    call=pick_callouts(pack,detector_ids)
    body=choose(pick_slot(pack,"body",style),1)
    outro=choose(pick_slot(pack,"outro",style),1 if intensity>=3 else 0)
    return " ".join((intro+call+body+outro)[:3])
def build_monologue(pack:Dict[str,Any], style:str, detector_ids:List[str], intensity:int)->str:
    intro=choose(pick_slot(pack,"intro",style),1)
    call=pick_callouts(pack,detector_ids)
    body=choose(pick_slot(pack,"body",style),2 if intensity>=6 else 1)
    outro=choose(pick_slot(pack,"outro",style),1)
    return textwrap.fill(" ".join(intro+call+body+outro), width=92)
def build_from_yaml(insult:str, style:str, mode:str, intensity:int, detector_ids:List[str], pack_path:Optional[str]=None)->str:
    pack=load_pack(pack_path)
    if mode=="oneliner": return build_oneliner(pack,style,detector_ids,intensity)
    if mode=="monologue": return build_monologue(pack,style,detector_ids,intensity)
    return build_threebeat(pack,style,detector_ids,intensity)
