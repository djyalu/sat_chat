"""Storage service for S3/MinIO operations"""

import logging
from typing import Optional, List, Dict, Any, BinaryIO
from pathlib import Path
import asyncio
import aiofiles
from datetime import datetime, timedelta

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.config import Config

from satchat.core.config import settings

logger = logging.getLogger(__name__)


class S3Service:
    """S3/MinIO storage service"""
    
    def __init__(self):
        """Initialize S3 service"""
        self.config = Config(
            region_name=settings.s3_region,
            signature_version='s3v4',
            retries={'max_attempts': 3, 'mode': 'adaptive'}
        )
        
        self.client = boto3.client(
            's3',
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key.get_secret_value(),
            aws_secret_access_key=settings.s3_secret_key.get_secret_value(),
            config=self.config
        )
        
        self.resource = boto3.resource(
            's3',
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key.get_secret_value(),
            aws_secret_access_key=settings.s3_secret_key.get_secret_value(),
            config=self.config
        )
        
        # Initialize buckets
        self._init_buckets()
    
    def _init_buckets(self):
        """Create buckets if they don't exist"""
        buckets = [
            settings.s3_bucket_raw,
            settings.s3_bucket_processed
        ]
        
        for bucket_name in buckets:
            try:
                self.client.head_bucket(Bucket=bucket_name)
                logger.info(f"Bucket {bucket_name} exists")
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == '404':
                    try:
                        self.client.create_bucket(Bucket=bucket_name)
                        logger.info(f"Created bucket {bucket_name}")
                    except Exception as create_error:
                        logger.error(f"Error creating bucket {bucket_name}: {create_error}")
                else:
                    logger.error(f"Error checking bucket {bucket_name}: {e}")
    
    async def upload_file(
        self,
        file_path: str,
        bucket: str,
        object_key: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Upload file to S3
        
        Args:
            file_path: Local file path
            bucket: S3 bucket name
            object_key: S3 object key
            metadata: Optional metadata
        
        Returns:
            S3 URL of uploaded file
        """
        try:
            extra_args = {}
            if metadata:
                extra_args['Metadata'] = metadata
            
            # Upload file
            self.client.upload_file(
                file_path,
                bucket,
                object_key,
                ExtraArgs=extra_args
            )
            
            # Generate URL
            url = f"{settings.s3_endpoint}/{bucket}/{object_key}"
            logger.info(f"Uploaded file to {url}")
            
            return url
            
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise
        except NoCredentialsError:
            logger.error("S3 credentials not available")
            raise
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            raise
    
    async def upload_bytes(
        self,
        data: bytes,
        bucket: str,
        object_key: str,
        content_type: str = "application/octet-stream",
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Upload bytes data to S3
        
        Args:
            data: Bytes data to upload
            bucket: S3 bucket name
            object_key: S3 object key
            content_type: Content type
            metadata: Optional metadata
        
        Returns:
            S3 URL of uploaded file
        """
        try:
            extra_args = {'ContentType': content_type}
            if metadata:
                extra_args['Metadata'] = metadata
            
            # Upload bytes
            self.client.put_object(
                Bucket=bucket,
                Key=object_key,
                Body=data,
                **extra_args
            )
            
            # Generate URL
            url = f"{settings.s3_endpoint}/{bucket}/{object_key}"
            logger.info(f"Uploaded bytes to {url}")
            
            return url
            
        except Exception as e:
            logger.error(f"Error uploading bytes: {e}")
            raise
    
    async def download_file(
        self,
        bucket: str,
        object_key: str,
        local_path: str
    ) -> bool:
        """
        Download file from S3
        
        Args:
            bucket: S3 bucket name
            object_key: S3 object key
            local_path: Local file path to save
        
        Returns:
            Success status
        """
        try:
            # Ensure directory exists
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Download file
            self.client.download_file(bucket, object_key, local_path)
            logger.info(f"Downloaded {object_key} to {local_path}")
            
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.error(f"Object not found: {bucket}/{object_key}")
            else:
                logger.error(f"Error downloading file: {e}")
            return False
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            return False
    
    async def get_object_bytes(self, bucket: str, object_key: str) -> Optional[bytes]:
        """
        Get object bytes from S3
        
        Args:
            bucket: S3 bucket name
            object_key: S3 object key
        
        Returns:
            Bytes data or None
        """
        try:
            response = self.client.get_object(Bucket=bucket, Key=object_key)
            return response['Body'].read()
        except ClientError as e:
            logger.error(f"Error getting object bytes: {e}")
            return None
    
    def list_objects(
        self,
        bucket: str,
        prefix: str = "",
        max_keys: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        List objects in bucket
        
        Args:
            bucket: S3 bucket name
            prefix: Object key prefix
            max_keys: Maximum number of keys to return
        
        Returns:
            List of object metadata
        """
        try:
            response = self.client.list_objects_v2(
                Bucket=bucket,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            objects = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    objects.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'],
                        'etag': obj['ETag']
                    })
            
            return objects
            
        except Exception as e:
            logger.error(f"Error listing objects: {e}")
            return []
    
    def delete_object(self, bucket: str, object_key: str) -> bool:
        """
        Delete object from S3
        
        Args:
            bucket: S3 bucket name
            object_key: S3 object key
        
        Returns:
            Success status
        """
        try:
            self.client.delete_object(Bucket=bucket, Key=object_key)
            logger.info(f"Deleted {bucket}/{object_key}")
            return True
        except Exception as e:
            logger.error(f"Error deleting object: {e}")
            return False
    
    def generate_presigned_url(
        self,
        bucket: str,
        object_key: str,
        expiration: int = 3600,
        http_method: str = 'GET'
    ) -> Optional[str]:
        """
        Generate presigned URL for object
        
        Args:
            bucket: S3 bucket name
            object_key: S3 object key
            expiration: URL expiration in seconds
            http_method: HTTP method (GET or PUT)
        
        Returns:
            Presigned URL or None
        """
        try:
            if http_method == 'GET':
                url = self.client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket, 'Key': object_key},
                    ExpiresIn=expiration
                )
            elif http_method == 'PUT':
                url = self.client.generate_presigned_url(
                    'put_object',
                    Params={'Bucket': bucket, 'Key': object_key},
                    ExpiresIn=expiration
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {http_method}")
            
            return url
            
        except Exception as e:
            logger.error(f"Error generating presigned URL: {e}")
            return None
    
    def get_object_metadata(self, bucket: str, object_key: str) -> Optional[Dict[str, Any]]:
        """
        Get object metadata
        
        Args:
            bucket: S3 bucket name
            object_key: S3 object key
        
        Returns:
            Object metadata or None
        """
        try:
            response = self.client.head_object(Bucket=bucket, Key=object_key)
            return {
                'content_type': response.get('ContentType'),
                'content_length': response.get('ContentLength'),
                'last_modified': response.get('LastModified'),
                'etag': response.get('ETag'),
                'metadata': response.get('Metadata', {})
            }
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.debug(f"Object not found: {bucket}/{object_key}")
            else:
                logger.error(f"Error getting object metadata: {e}")
            return None
    
    async def cleanup_old_files(
        self,
        bucket: str,
        prefix: str = "",
        days_old: int = 30
    ) -> int:
        """
        Clean up old files from bucket
        
        Args:
            bucket: S3 bucket name
            prefix: Object key prefix
            days_old: Delete files older than this many days
        
        Returns:
            Number of files deleted
        """
        cutoff_date = datetime.now() - timedelta(days=days_old)
        deleted_count = 0
        
        try:
            objects = self.list_objects(bucket, prefix)
            
            for obj in objects:
                if obj['last_modified'].replace(tzinfo=None) < cutoff_date:
                    if self.delete_object(bucket, obj['key']):
                        deleted_count += 1
                        logger.info(f"Deleted old file: {obj['key']}")
            
            logger.info(f"Cleaned up {deleted_count} old files from {bucket}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old files: {e}")
            return deleted_count