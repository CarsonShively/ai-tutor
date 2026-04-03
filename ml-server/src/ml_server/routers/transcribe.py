# improve edge case handling further onces full system is in place
# improve receive conrol flow
# potentially split aspects into modules
# class with state
# preprocess here and chunk or send all at once and return
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ml_server.components.transcribe.schema import StartMetadata, EndMetadata
from pydantic import ValidationError

transcribe_router = APIRouter()

@transcribe_router.websocket("/transcribe")
async def transcribe(websocket: WebSocket):
    await websocket.accept()
    transcribe_worker = websocket.app.state.transcribe_worker
    
    try:
        state = "start"
        buffer = bytearray()
        
        while True:
            match state:
                case "start":
                    
                    try:
                        scheme = await websocket.receive_json()
                        StartMetadata.model_validate(scheme)
                    except ValidationError as e:
                        await websocket.send_json({
                            "type": "error",
                            "code": "INVALID_JSON_FORMAT",
                            "message": "json format failed validation",
                            "details": e.errors()
                            
                        })
                        continue
                    except Exception as e:
                        await websocket.send_json({
                            "type": "error",
                            "code": "NOT_JSON_RECIEVED",
                            "message": "json not recieved",
                            "details": str(e)
                        })
                    
                    state = "stream"
                    
                case "stream":
                    stream = await websocket.receive()
                    
                    if stream["type"] == "websocket.disconnect":
                        return
                    
                    if stream.get("bytes") is not None:
                        chunk = stream["bytes"]
                        buffer.extend(chunk)
        
                    elif stream.get("text") is not None:
                        if not buffer:
                            await websocket.send_json({
                                "type": "error",
                                "code": "NO_BYTES_IN_BUFFER",
                                "message": "audio buffer is empty",
                            })
                            continue
                        text = stream["text"]
                        try:
                            EndMetadata.model_validate_json(text)
                        except ValidationError as e:
                            await websocket.send_json({
                                "type": "error",
                                "code": "INVALID_JSON_FORMAT",
                                "message": "json format failed validation",
                                "details": e.errors()
                                
                            })
                            continue
                        
                        state = "end"
                                
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "code": "INVALID_REQUEST_TYPE",
                            "message": "request is empty text, empty bytes, or an invlaid type. supported types: text and bytes",
                        })
                        
                case "end": 
                    try:
                        response = await transcribe_worker.submit(bytes(buffer))
                        await websocket.send_json({
                            "type": "response",
                            "transcript": response["text"],
                            "language": response["language"]
                        })
                        
                    except Exception as e:
                        await websocket.send_json({
                            "type": "error",
                            "code": "TRANSCRIBE_FAIL",
                            "message": "failed to transcribe audio",
                            "details": str(e)                            
                        })
                        
                    finally:
                        state = "start"
                        buffer.clear()
                          # unknown whisper languege? 
    except WebSocketDisconnect:
        return