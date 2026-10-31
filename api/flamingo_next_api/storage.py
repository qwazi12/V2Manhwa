"""Private hash-addressed source/export media and session-bound preview signatures."""
import hashlib
import hmac
import io
import re
import time
import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException

class Storage:
    def __init__(self, settings):
        self.settings = settings
        self.client = boto3.client('s3', endpoint_url=settings.storage_endpoint,
            aws_access_key_id=settings.storage_user, aws_secret_access_key=settings.storage_password,
            region_name='us-east-1')

    def initialize(self):
        try:
            self.client.head_bucket(Bucket=self.settings.bucket)
        except ClientError as e:
            if e.response['Error']['Code'] != '404':
                raise
            self.client.create_bucket(Bucket=self.settings.bucket)
        # Explicit private policy. Never issue object-store links to the browser.
        try:
            self.client.delete_bucket_policy(Bucket=self.settings.bucket)
        except ClientError as e:
            if e.response['Error']['Code'] != 'NoSuchBucketPolicy':
                raise

    def put(self, data: bytes):
        digest = hashlib.sha256(data).hexdigest()
        self.client.put_object(Bucket=self.settings.bucket, Key=f'synthetic/{digest}.svg',
            Body=io.BytesIO(data), ContentType='image/svg+xml', Metadata={'sha256': digest})
        return digest

    def get(self, digest):
        if not re.fullmatch('[0-9a-f]{64}', digest):
            raise HTTPException(404, 'Unknown preview')
        data = self.client.get_object(Bucket=self.settings.bucket, Key=f'synthetic/{digest}.svg')['Body'].read()
        if hashlib.sha256(data).hexdigest() != digest:
            raise HTTPException(409, 'Preview checksum mismatch')
        return data

    def signature(self, digest, session_id, expires):
        message = f'preview:GET:{digest}:{session_id}:{expires}'.encode()
        return hmac.new(self.settings.signing_key.encode(), message, hashlib.sha256).hexdigest()

    def verify(self, digest, session_id, expires, signature):
        if expires <= int(time.time()) or expires > int(time.time()) + 300:
            raise HTTPException(403, 'Preview link expired')
        if not hmac.compare_digest(self.signature(digest, session_id, expires), signature):
            raise HTTPException(403, 'Invalid preview signature')

    def put_blob(self,data,mime):
        extensions={'image/png':'png','image/jpeg':'jpg','image/webp':'webp','audio/wav':'wav','video/mp4':'mp4','application/json':'json','text/vtt':'vtt'}
        if mime not in extensions: raise ValueError('Unsupported stored media type')
        digest=hashlib.sha256(data).hexdigest()
        key=f'assets/{digest}.{extensions[mime]}'
        self.client.put_object(Bucket=self.settings.bucket,Key=key,Body=data,ContentType=mime,Metadata={'sha256':digest})
        return {'key':key,'sha256':digest,'size_bytes':len(data),'mime_type':mime}

    def read_blob(self,key,digest):
        if not re.fullmatch(r'assets/[0-9a-f]{64}\.(png|jpg|webp|wav|mp4|json|vtt)',key):
            raise HTTPException(404,'Unknown asset')
        try:
            response=self.client.get_object(Bucket=self.settings.bucket,Key=key)
            data=response['Body'].read()
        except ClientError as e:
            raise HTTPException(404,'Asset is unavailable') from e
        if hashlib.sha256(data).hexdigest()!=digest:
            raise HTTPException(409,'Asset checksum mismatch')
        return data
