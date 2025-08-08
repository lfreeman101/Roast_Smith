import asyncio, edge_tts
VOICE_MAP={'Colonel Foghorn MethHorn':'en-US-GuyNeural','Velvet Chainsaw':'en-US-AriaNeural','Sir Clapsworth the Petty':'en-GB-RyanNeural','Cupcake the Widowmaker':'en-US-JennyNeural'}
async def synth_to_mp3(text, voice, out_path):
    v=VOICE_MAP.get(voice,'en-US-GuyNeural')
    await edge_tts.Communicate(text, voice=v).save(out_path)
