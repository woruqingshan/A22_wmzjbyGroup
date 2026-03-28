class TTSRuntime:
    def synthesize(self, *, session_id: str, turn_id: int, text: str) -> str | None:
        del session_id, turn_id, text
        return None


tts_runtime = TTSRuntime()
