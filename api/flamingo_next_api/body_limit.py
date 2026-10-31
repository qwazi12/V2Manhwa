"""Bound ASGI input bytes, including chunked requests, before parsing JSON images."""
from starlette.exceptions import HTTPException

class BodyLimitMiddleware:
    def __init__(self,app,max_bytes=45_000_000):self.app,self.max_bytes=app,max_bytes
    async def __call__(self,scope,receive,send):
        if scope['type']!='http':return await self.app(scope,receive,send)
        consumed=0
        async def bounded_receive():
            nonlocal consumed
            message=await receive()
            if message['type']=='http.request':
                consumed+=len(message.get('body',b''))
                if consumed>self.max_bytes:raise HTTPException(413,'Chapter request exceeds the 45 MB transport limit')
            return message
        await self.app(scope,bounded_receive,send)
