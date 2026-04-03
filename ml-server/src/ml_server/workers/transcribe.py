from faster_whisper import WhisperModel
import numpy as np
import asyncio

class TranscribeWorker:
    # not documentation personal notes:
    # class variables for different transrcibe models, or multiple models to decrease queue time, async threads
    # class methods are used for working on class variables
    # fill thinking time with explainability / thought process 
    def __init__(self):
        self.model = WhisperModel("base", device="cpu", compute_type="int8")
        self.queue = asyncio.Queue()


    async def transcribe(self, buffer):
        
        if len(buffer) % 2 != 0:
            raise ValueError("buffer length must be divisble by 2 for pcm_s16le, bytes might not match metadata")
            
        try: 
            sample = np.frombuffer(buffer, dtype="<i2").astype(np.float32)
            sample = sample / 32768.0

            segments, info = await asyncio.to_thread(self.model.transcribe, sample, beam_size=5)

            text = "".join(segment.text for segment in segments).strip()
            return {
                "text": text,
                "language": info.language
            }
        except Exception as e:
            raise RuntimeError("transcribe failed") from e
        
    async def submit(self, buffer):
        loop = asyncio.get_running_loop()
        transcribe_future = loop.create_future()
        await self.queue.put((buffer, transcribe_future))
        return await transcribe_future
    
    async def worker(self):
        while True:
            buffer, transcribe_future = await self.queue.get()
            try:
                text = await self.transcribe(buffer)
                transcribe_future.set_result(text)
            except Exception as e:
                transcribe_future.set_exception(e)
                
            finally:
                self.queue.task_done()