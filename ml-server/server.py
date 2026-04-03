# audio ai to navigate the ui
# migrate to event loop and corutine once initial system is in place
from ml_server.routers.transcribe import transcribe_router
from ml_server.workers.transcribe import TranscribeWorker
from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio

@asynccontextmanager
async def server_lifespan(server):
    server.state.transcribe_worker = TranscribeWorker()
    server.state.transcribe_task = asyncio.create_task(server.state.transcribe_worker.worker())
    yield
    
server = FastAPI(lifespan=server_lifespan)

server.include_router(transcribe_router)