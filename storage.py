"""
Oracle Cloud Object Storage Client
Upload videos and generate pre-authenticated signed URLs
"""

import oci
from oci.object_storage import ObjectStorageClient
from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple
from config import settings


class StorageError(Exception):
    """Custom storage error"""
    pass


class OracleObjectStorage:
    """Oracle Cloud Object Storage client"""

    def __init__(self):
        """Initialize OCI client with credentials from config"""
        try:
            # Use the working configuration (same as your "Signer OK" test)
            self.config = {
                "user": settings.OCI_USER_OCID,
                "fingerprint": settings.OCI_FINGERPRINT,
                "tenancy": settings.OCI_TENANCY_OCID,
                "region": settings.OCI_REGION,
                "key_file": settings.OCI_PRIVATE_KEY_PATH,  # ❗ critically important
            }

            # Do NOT use key_content. Do NOT manually load PEM.
            # Let the OCI SDK read the file itself.
            self.client = oci.object_storage.ObjectStorageClient(self.config)

            self.namespace = settings.OCI_NAMESPACE
            self.bucket = settings.OCI_BUCKET_NAME
            self.bucket_name = self.bucket
            self.region = settings.OCI_REGION

            print("✓ Oracle Object Storage initialized")

        except Exception as e:
            raise StorageError(f"Failed to initialize Oracle Object Storage: {e}")

    async def upload_video(
        self,
        file_path: str,
        job_id: str,
        content_type: str = "video/mp4"
    ) -> Tuple[str, str]:
        """
        Upload video file to Oracle Cloud Object Storage

        Args:
            file_path: Local path to video file
            job_id: Job ID (used as object name)
            content_type: MIME type

        Returns:
            Tuple of (object_name, signed_url)

        Raises:
            StorageError: If upload fails
        """
        # Validate file exists
        if not Path(file_path).exists():
            raise StorageError(f"File not found: {file_path}")

        # Build object name (organize by date for easier management)
        now = datetime.utcnow()
        date_prefix = now.strftime("%Y/%m/%d")
        object_name = f"videos/{date_prefix}/{job_id}.mp4"

        try:
            print(f"Uploading video to OCI: {object_name}")

            # Upload file with streaming
            with open(file_path, 'rb') as f:
                self.client.put_object(
                    namespace_name=self.namespace,
                    bucket_name=self.bucket_name,
                    object_name=object_name,
                    put_object_body=f,
                    content_type=content_type,
                    # Optional metadata
                    metadata={
                        'job_id': job_id,
                        'uploaded_at': now.isoformat()
                    }
                )

            print(f"✓ Upload complete: {object_name}")

            # Generate signed URL
            signed_url = await self.create_signed_url(object_name, expiration_days=7)

            return object_name, signed_url

        except Exception as e:
            raise StorageError(f"Failed to upload video: {e}")

    async def create_signed_url(
        self,
        object_name: str,
        expiration_days: int = 7
    ) -> str:
        """
        Create pre-authenticated request (PAR) for secure download

        Args:
            object_name: Object key in bucket
            expiration_days: Number of days until URL expires

        Returns:
            Signed HTTPS URL

        Raises:
            StorageError: If PAR creation fails
        """
        try:
            # Calculate expiration time
            expiration = datetime.utcnow() + timedelta(days=expiration_days)

            # Create PAR details
            par_name = f"par-{object_name.replace('/', '-')}-{int(datetime.utcnow().timestamp())}"

            create_par_details = oci.object_storage.models.CreatePreauthenticatedRequestDetails(
                name=par_name,
                object_name=object_name,
                access_type="ObjectRead",  # Read-only access
                time_expires=expiration
            )

            # Create PAR
            response = self.client.create_preauthenticated_request(
                namespace_name=self.namespace,
                bucket_name=self.bucket_name,
                create_preauthenticated_request_details=create_par_details
            )

            # Build full URL
            base_url = f"https://objectstorage.{self.region}.oraclecloud.com"
            signed_url = f"{base_url}{response.data.access_uri}"

            print(f"✓ Generated signed URL (expires: {expiration_days} days)")

            return signed_url

        except Exception as e:
            raise StorageError(f"Failed to create signed URL: {e}")

    async def delete_video(self, object_name: str) -> bool:
        """
        Delete video from storage

        Args:
            object_name: Object key to delete

        Returns:
            True if successful

        Raises:
            StorageError: If deletion fails
        """
        try:
            self.client.delete_object(
                namespace_name=self.namespace,
                bucket_name=self.bucket_name,
                object_name=object_name
            )
            print(f"✓ Deleted: {object_name}")
            return True

        except oci.exceptions.ServiceError as e:
            if e.status == 404:
                # Object doesn't exist, consider it deleted
                return True
            raise StorageError(f"Failed to delete video: {e}")

        except Exception as e:
            raise StorageError(f"Failed to delete video: {e}")

    async def check_object_exists(self, object_name: str) -> bool:
        """
        Check if object exists in storage

        Args:
            object_name: Object key to check

        Returns:
            True if exists
        """
        try:
            self.client.head_object(
                namespace_name=self.namespace,
                bucket_name=self.bucket_name,
                object_name=object_name
            )
            return True

        except oci.exceptions.ServiceError as e:
            if e.status == 404:
                return False
            raise StorageError(f"Failed to check object existence: {e}")

        except Exception as e:
            raise StorageError(f"Failed to check object existence: {e}")

    async def get_object_size(self, object_name: str) -> int:
        """
        Get object size in bytes

        Args:
            object_name: Object key

        Returns:
            Size in bytes

        Raises:
            StorageError: If object not found or error occurs
        """
        try:
            response = self.client.head_object(
                namespace_name=self.namespace,
                bucket_name=self.bucket_name,
                object_name=object_name
            )
            return int(response.headers.get('Content-Length', 0))

        except Exception as e:
            raise StorageError(f"Failed to get object size: {e}")

    async def list_videos(
        self,
        prefix: str = "videos/",
        limit: int = 100
    ) -> list:
        """
        List videos in storage

        Args:
            prefix: Object name prefix
            limit: Maximum number of objects to return

        Returns:
            List of object names
        """
        try:
            response = self.client.list_objects(
                namespace_name=self.namespace,
                bucket_name=self.bucket_name,
                prefix=prefix,
                limit=limit
            )

            objects = []
            if response.data.objects:
                for obj in response.data.objects:
                    objects.append({
                        'name': obj.name,
                        'size': obj.size,
                        'time_created': obj.time_created.isoformat() if obj.time_created else None
                    })

            return objects

        except Exception as e:
            raise StorageError(f"Failed to list videos: {e}")

    def get_storage_info(self) -> dict:
        """
        Get storage configuration info

        Returns:
            Dictionary with storage details
        """
        return {
            'namespace': self.namespace,
            'bucket': self.bucket_name,
            'region': self.region
        }


# Global storage instance
storage = OracleObjectStorage()


if __name__ == "__main__":
    # Test storage connection
    import asyncio

    async def test():
        print("Testing Oracle Object Storage...")

        storage = OracleObjectStorage()

        # Get storage info
        info = storage.get_storage_info()
        print(f"✓ Namespace: {info['namespace']}")
        print(f"✓ Bucket: {info['bucket']}")
        print(f"✓ Region: {info['region']}")

        # Test listing (should work even if empty)
        try:
            videos = await storage.list_videos(limit=5)
            print(f"✓ Found {len(videos)} videos in storage")
        except Exception as e:
            print(f"✗ List failed: {e}")

    asyncio.run(test())
