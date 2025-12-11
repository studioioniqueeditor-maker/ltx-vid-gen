"""
Oracle Database Client
Job persistence, rate limiting, and API key management
"""

import oracledb
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from contextlib import asynccontextmanager
from config import settings
import hashlib
import oracledb


class DatabaseError(Exception):
    """Custom database error"""
    pass


class OracleDatabase:
    """Oracle Database client with connection pooling"""

    def __init__(self):
        self.pool = None
        self.dsn = settings.ORACLE_DB_DSN
        self.user = settings.ORACLE_DB_USER
        self.password = settings.ORACLE_DB_PASSWORD
        self.wallet_dir=settings.ORACLE_WALLET_DIR

    def init_pool(self, min_connections: int = 2, max_connections: int = 10):
        """
        Initialize connection pool

        Args:
            min_connections: Minimum pool size
            max_connections: Maximum pool size
        """

        oracledb.init_oracle_client(
            lib_dir="/Users/aditya/Downloads/instantclient_23_3",
            config_dir=self.wallet_dir  # folder where wallet is unzipped
        )

        try:
            self.pool = oracledb.create_pool(
                user=self.user,
                password=self.password,
                dsn=self.dsn,
                min=min_connections,
                max=max_connections,
                increment=1,
                # threaded=True,
                getmode=oracledb.POOL_GETMODE_WAIT
            )
            print(f"✓ Database pool initialized ({min_connections}-{max_connections} connections)")
        except Exception as e:
            raise DatabaseError(f"Failed to initialize database pool: {e}")

    @asynccontextmanager
    async def get_connection(self):
        """
        Get connection from pool (async context manager)

        Yields:
            Database connection
        """
        if not self.pool:
            raise DatabaseError("Database pool not initialized. Call init_pool() first.")

        conn = None
        try:
            conn = self.pool.acquire()
            yield conn
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            raise DatabaseError(f"Database operation failed: {e}")
        finally:
            if conn:
                try:
                    self.pool.release(conn)
                except:
                    pass

    async def create_job(
        self,
        job_id: str,
        api_key_hash: str,
        image_url: str,
        prompt: str,
        seed: int,
        width: int,
        height: int,
        num_frames: int,
        webhook_url: Optional[str] = None
    ) -> bool:
        """
        Create new job record

        Args:
            job_id: Unique job identifier
            api_key_hash: SHA-256 hash of API key
            image_url: URL of input image
            prompt: Motion description
            seed: Random seed
            width: Output width
            height: Output height
            num_frames: Number of frames
            webhook_url: Optional webhook URL

        Returns:
            True if successful
        """
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO video_jobs
                    (job_id, api_key_hash, status, image_url, prompt,
                     seed, width, height, num_frames, webhook_url)
                    VALUES
                    (:job_id, :api_key_hash, 'queued', :image_url, :prompt,
                     :seed, :width, :height, :num_frames, :webhook_url)
                """, {
                    'job_id': job_id,
                    'api_key_hash': api_key_hash,
                    'image_url': image_url,
                    'prompt': prompt,
                    'seed': seed,
                    'width': width,
                    'height': height,
                    'num_frames': num_frames,
                    'webhook_url': webhook_url
                })
                conn.commit()
                return True
            except Exception as e:
                conn.rollback()
                raise DatabaseError(f"Failed to create job: {e}")

    async def get_job(self, job_id: str) -> Optional[Dict]:
        """
        Get job by ID

        Args:
            job_id: Job ID to fetch

        Returns:
            Job dictionary or None if not found
        """
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT job_id, api_key_hash, status, created_at, started_at,
                       completed_at, image_url, prompt, seed, width, height,
                       num_frames, video_url, video_object_name,
                       generation_time_seconds, error_message, webhook_url,
                       webhook_delivered, webhook_attempts
                FROM video_jobs
                WHERE job_id = :job_id
            """, {'job_id': job_id})

            row = cursor.fetchone()
            if not row:
                return None

            return {
                'job_id': row[0],
                'api_key_hash': row[1],
                'status': row[2],
                'created_at': row[3].isoformat() if row[3] else None,
                'started_at': row[4].isoformat() if row[4] else None,
                'completed_at': row[5].isoformat() if row[5] else None,
                'image_url': row[6],
                'prompt': row[7],
                'seed': row[8],
                'width': row[9],
                'height': row[10],
                'num_frames': row[11],
                'video_url': row[12],
                'video_object_name': row[13],
                'generation_time_seconds': row[14],
                'error_message': row[15],
                'webhook_url': row[16],
                'webhook_delivered': row[17] == 'Y',
                'webhook_attempts': row[18]
            }

    async def update_job_status(
        self,
        job_id: str,
        status: str,
        started_at: Optional[datetime] = None
    ) -> bool:
        """
        Update job status

        Args:
            job_id: Job ID
            status: New status ('queued', 'processing', 'completed', 'failed')
            started_at: Optional start timestamp

        Returns:
            True if successful
        """
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                if started_at:
                    cursor.execute("""
                        UPDATE video_jobs
                        SET status = :status, started_at = :started_at
                        WHERE job_id = :job_id
                    """, {
                        'status': status,
                        'started_at': started_at,
                        'job_id': job_id
                    })
                else:
                    cursor.execute("""
                        UPDATE video_jobs
                        SET status = :status
                        WHERE job_id = :job_id
                    """, {'status': status, 'job_id': job_id})

                conn.commit()
                return cursor.rowcount > 0
            except Exception as e:
                conn.rollback()
                raise DatabaseError(f"Failed to update job status: {e}")

    async def complete_job(
        self,
        job_id: str,
        video_url: str,
        object_name: str,
        generation_time: float
    ) -> bool:
        """
        Mark job as completed

        Args:
            job_id: Job ID
            video_url: Signed URL to video
            object_name: Object storage key
            generation_time: Time taken in seconds

        Returns:
            True if successful
        """
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE video_jobs
                    SET status = 'completed',
                        completed_at = CURRENT_TIMESTAMP,
                        video_url = :video_url,
                        video_object_name = :object_name,
                        generation_time_seconds = :gen_time
                    WHERE job_id = :job_id
                """, {
                    'video_url': video_url,
                    'object_name': object_name,
                    'gen_time': generation_time,
                    'job_id': job_id
                })
                conn.commit()
                return cursor.rowcount > 0
            except Exception as e:
                conn.rollback()
                raise DatabaseError(f"Failed to complete job: {e}")

    async def fail_job(self, job_id: str, error_message: str) -> bool:
        """
        Mark job as failed

        Args:
            job_id: Job ID
            error_message: Error description

        Returns:
            True if successful
        """
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                # Truncate error message to fit in database
                error_message = error_message[:4000]

                cursor.execute("""
                    UPDATE video_jobs
                    SET status = 'failed',
                        completed_at = CURRENT_TIMESTAMP,
                        error_message = :error
                    WHERE job_id = :job_id
                """, {'error': error_message, 'job_id': job_id})

                conn.commit()
                return cursor.rowcount > 0
            except Exception as e:
                conn.rollback()
                raise DatabaseError(f"Failed to mark job as failed: {e}")

    async def check_rate_limit(self, api_key_hash: str) -> tuple[int, int]:
        """
        Check rate limit for API key

        Args:
            api_key_hash: SHA-256 hash of API key

        Returns:
            Tuple of (current_count, limit)

        Raises:
            DatabaseError: If API key is not found or inactive
        """
        async with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get rate limit for this key from api_keys table
            cursor.execute("""
                SELECT rate_limit_per_minute
                FROM api_keys
                WHERE key_hash = :key_hash AND is_active = 'Y'
            """, {'key_hash': api_key_hash})

            result = cursor.fetchone()
            if not result:
                # Key not in database - use default limit
                rate_limit = settings.RATE_LIMIT_PER_MINUTE
            else:
                rate_limit = result[0]

            # Count requests in last minute
            one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
            cursor.execute("""
                SELECT COUNT(*)
                FROM rate_limit_log
                WHERE key_hash = :key_hash
                AND request_time > :since
            """, {'key_hash': api_key_hash, 'since': one_minute_ago})

            count = cursor.fetchone()[0]

            return count, rate_limit

    async def log_request(self, api_key_hash: str, endpoint: str) -> bool:
        """
        Log API request for rate limiting

        Args:
            api_key_hash: SHA-256 hash of API key
            endpoint: Endpoint name

        Returns:
            True if successful
        """
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                # Insert rate limit log
                cursor.execute("""
                    INSERT INTO rate_limit_log (key_hash, endpoint)
                    VALUES (:key_hash, :endpoint)
                """, {'key_hash': api_key_hash, 'endpoint': endpoint})

                # Update last_used_at in api_keys if key exists
                cursor.execute("""
                    UPDATE api_keys
                    SET last_used_at = CURRENT_TIMESTAMP,
                        total_requests = total_requests + 1
                    WHERE key_hash = :key_hash
                """, {'key_hash': api_key_hash})

                conn.commit()
                return True
            except Exception as e:
                conn.rollback()
                # Don't fail request if logging fails
                print(f"Warning: Failed to log request: {e}")
                return False

    async def update_webhook_delivered(
        self,
        job_id: str,
        delivered: bool,
        attempts: int
    ) -> bool:
        """
        Update webhook delivery status

        Args:
            job_id: Job ID
            delivered: Whether webhook was delivered successfully
            attempts: Number of delivery attempts

        Returns:
            True if successful
        """
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE video_jobs
                    SET webhook_delivered = :delivered,
                        webhook_attempts = :attempts,
                        last_webhook_attempt = CURRENT_TIMESTAMP
                    WHERE job_id = :job_id
                """, {
                    'delivered': 'Y' if delivered else 'N',
                    'attempts': attempts,
                    'job_id': job_id
                })
                conn.commit()
                return cursor.rowcount > 0
            except Exception as e:
                conn.rollback()
                raise DatabaseError(f"Failed to update webhook status: {e}")

    async def cleanup_old_rate_limits(self, hours: int = 1) -> int:
        """
        Clean up old rate limit logs

        Args:
            hours: Delete logs older than this many hours

        Returns:
            Number of rows deleted
        """
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cutoff = datetime.utcnow() - timedelta(hours=hours)
                cursor.execute("""
                    DELETE FROM rate_limit_log
                    WHERE request_time < :cutoff
                """, {'cutoff': cutoff})

                deleted = cursor.rowcount
                conn.commit()
                return deleted
            except Exception as e:
                conn.rollback()
                raise DatabaseError(f"Failed to cleanup rate limits: {e}")

    async def get_jobs_by_api_key(
        self,
        api_key_hash: str,
        limit: int = 20,
        status: Optional[str] = None
    ) -> List[Dict]:
        """
        Get recent jobs for an API key

        Args:
            api_key_hash: SHA-256 hash of API key
            limit: Maximum number of jobs to return
            status: Optional status filter

        Returns:
            List of job dictionaries
        """
        async with self.get_connection() as conn:
            cursor = conn.cursor()

            if status:
                cursor.execute("""
                    SELECT job_id, status, created_at, completed_at,
                           generation_time_seconds, error_message
                    FROM video_jobs
                    WHERE api_key_hash = :key_hash AND status = :status
                    ORDER BY created_at DESC
                    FETCH FIRST :limit ROWS ONLY
                """, {'key_hash': api_key_hash, 'status': status, 'limit': limit})
            else:
                cursor.execute("""
                    SELECT job_id, status, created_at, completed_at,
                           generation_time_seconds, error_message
                    FROM video_jobs
                    WHERE api_key_hash = :key_hash
                    ORDER BY created_at DESC
                    FETCH FIRST :limit ROWS ONLY
                """, {'key_hash': api_key_hash, 'limit': limit})

            jobs = []
            for row in cursor.fetchall():
                jobs.append({
                    'job_id': row[0],
                    'status': row[1],
                    'created_at': row[2].isoformat() if row[2] else None,
                    'completed_at': row[3].isoformat() if row[3] else None,
                    'generation_time_seconds': row[4],
                    'error_message': row[5]
                })

            return jobs

    def close(self):
        """Close database pool"""
        if self.pool:
            try:
                self.pool.close()
                print("✓ Database pool closed")
            except Exception as e:
                print(f"Warning: Error closing database pool: {e}")


# Global database instance
db = OracleDatabase()


if __name__ == "__main__":
    # Test database connection
    import asyncio

    async def test():
        print("Testing Oracle Database connection...")
        db.init_pool(min_connections=1, max_connections=2)

        # Test connection
        async with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 'Connection successful' FROM DUAL")
            result = cursor.fetchone()
            print(f"✓ {result[0]}")

        db.close()

    asyncio.run(test())
