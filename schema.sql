-- ==========================================
-- LTX Video I2V - Oracle Database Schema
-- ==========================================
-- Run this script to create the required database tables and indexes
-- for the LTX Video I2V application

-- ====================
-- Video Jobs Table
-- ====================
-- Stores all video generation jobs with metadata and status

CREATE TABLE video_jobs (
    -- Primary key
    job_id VARCHAR2(36) PRIMARY KEY,

    -- API key (hashed with SHA-256)
    api_key_hash VARCHAR2(64) NOT NULL,

    -- Job status
    status VARCHAR2(20) NOT NULL CHECK (status IN ('queued', 'processing', 'completed', 'failed')),

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,

    -- Input parameters
    image_url VARCHAR2(500),
    prompt VARCHAR2(2000) NOT NULL,
    seed NUMBER,
    width NUMBER,
    height NUMBER,
    num_frames NUMBER,

    -- Output data
    video_url VARCHAR2(500),
    video_object_name VARCHAR2(200),
    generation_time_seconds NUMBER,

    -- Error handling
    error_message VARCHAR2(4000),
    retry_count NUMBER DEFAULT 0,

    -- Webhook
    webhook_url VARCHAR2(500),
    webhook_delivered CHAR(1) DEFAULT 'N' CHECK (webhook_delivered IN ('Y', 'N')),
    webhook_attempts NUMBER DEFAULT 0,
    last_webhook_attempt TIMESTAMP
);

-- Create indexes for efficient querying
CREATE INDEX idx_jobs_api_key ON video_jobs(api_key_hash);
CREATE INDEX idx_jobs_status ON video_jobs(status);
CREATE INDEX idx_jobs_created ON video_jobs(created_at DESC);
CREATE INDEX idx_jobs_webhook ON video_jobs(webhook_delivered, status) WHERE webhook_url IS NOT NULL;

-- ====================
-- API Keys Table
-- ====================
-- Manages API keys with rate limiting configuration

CREATE TABLE api_keys (
    -- API key hash (SHA-256)
    key_hash VARCHAR2(64) PRIMARY KEY,

    -- Metadata
    key_name VARCHAR2(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP,

    -- Status
    is_active CHAR(1) DEFAULT 'Y' CHECK (is_active IN ('Y', 'N')),

    -- Rate limiting
    rate_limit_per_minute NUMBER DEFAULT 10,

    -- Usage statistics
    total_requests NUMBER DEFAULT 0
);

-- ====================
-- Rate Limiting Log
-- ====================
-- Tracks API requests for rate limiting
-- Auto-cleanup recommended: Delete entries older than 1 hour

CREATE TABLE rate_limit_log (
    key_hash VARCHAR2(64) NOT NULL,
    request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    endpoint VARCHAR2(50),

    -- Foreign key to api_keys table
    CONSTRAINT fk_rate_limit_key FOREIGN KEY (key_hash) REFERENCES api_keys(key_hash)
);

-- Index for efficient rate limit queries
CREATE INDEX idx_rate_limit ON rate_limit_log(key_hash, request_time DESC);

-- ====================
-- Sample Data (Optional)
-- ====================
-- Insert sample API keys for testing
-- In production, use actual hashed API keys

-- Example: Insert test API key
-- To generate hash: echo -n "your-api-key" | sha256sum
COMMENT ON TABLE api_keys IS 'To add an API key, insert its SHA-256 hash';

-- INSERT INTO api_keys (key_hash, key_name, rate_limit_per_minute)
-- VALUES (
--     'hash_of_your_api_key_here',
--     'Production API Key 1',
--     10
-- );

-- ====================
-- Cleanup Procedures
-- ====================
-- Create procedure to clean up old rate limit logs

CREATE OR REPLACE PROCEDURE cleanup_rate_limits(p_hours IN NUMBER DEFAULT 1)
IS
    v_cutoff TIMESTAMP;
    v_deleted NUMBER;
BEGIN
    v_cutoff := CURRENT_TIMESTAMP - NUMTODSINTERVAL(p_hours, 'HOUR');

    DELETE FROM rate_limit_log
    WHERE request_time < v_cutoff;

    v_deleted := SQL%ROWCOUNT;
    COMMIT;

    DBMS_OUTPUT.PUT_LINE('Deleted ' || v_deleted || ' old rate limit entries');
END;
/

-- Schedule cleanup to run hourly (optional, requires DBMS_SCHEDULER privileges)
/*
BEGIN
    DBMS_SCHEDULER.CREATE_JOB (
        job_name        => 'CLEANUP_RATE_LIMITS_JOB',
        job_type        => 'PLSQL_BLOCK',
        job_action      => 'BEGIN cleanup_rate_limits(1); END;',
        start_date      => SYSTIMESTAMP,
        repeat_interval => 'FREQ=HOURLY; INTERVAL=1',
        enabled         => TRUE,
        comments        => 'Cleanup rate limit logs older than 1 hour'
    );
END;
/
*/

-- ====================
-- Archive Procedure
-- ====================
-- Archive old completed jobs (optional)

CREATE OR REPLACE PROCEDURE archive_old_jobs(p_days IN NUMBER DEFAULT 90)
IS
    v_cutoff TIMESTAMP;
    v_archived NUMBER;
BEGIN
    v_cutoff := CURRENT_TIMESTAMP - NUMTODSINTERVAL(p_days, 'DAY');

    -- In a real system, you might move these to an archive table
    -- For now, we'll just mark them for manual review
    UPDATE video_jobs
    SET error_message = error_message || ' [ARCHIVED]'
    WHERE completed_at < v_cutoff
    AND status IN ('completed', 'failed')
    AND error_message NOT LIKE '%[ARCHIVED]%';

    v_archived := SQL%ROWCOUNT;
    COMMIT;

    DBMS_OUTPUT.PUT_LINE('Marked ' || v_archived || ' jobs for archival');
END;
/

-- ====================
-- Useful Queries
-- ====================

-- Check job statistics
/*
SELECT
    status,
    COUNT(*) as count,
    AVG(generation_time_seconds) as avg_time,
    MAX(generation_time_seconds) as max_time
FROM video_jobs
WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '7' DAY
GROUP BY status;
*/

-- Check API key usage
/*
SELECT
    a.key_name,
    a.total_requests,
    a.last_used_at,
    COUNT(r.request_time) as requests_last_hour
FROM api_keys a
LEFT JOIN rate_limit_log r ON a.key_hash = r.key_hash
    AND r.request_time > CURRENT_TIMESTAMP - INTERVAL '1' HOUR
WHERE a.is_active = 'Y'
GROUP BY a.key_name, a.total_requests, a.last_used_at;
*/

-- Find failed jobs
/*
SELECT
    job_id,
    created_at,
    error_message
FROM video_jobs
WHERE status = 'failed'
AND created_at > CURRENT_TIMESTAMP - INTERVAL '1' DAY
ORDER BY created_at DESC;
*/

-- Check webhook delivery issues
/*
SELECT
    job_id,
    webhook_attempts,
    last_webhook_attempt,
    webhook_url
FROM video_jobs
WHERE webhook_url IS NOT NULL
AND webhook_delivered = 'N'
AND status IN ('completed', 'failed')
ORDER BY last_webhook_attempt DESC;
*/

-- ====================
-- Grants (Optional)
-- ====================
-- Grant necessary permissions to application user

-- GRANT SELECT, INSERT, UPDATE, DELETE ON video_jobs TO app_user;
-- GRANT SELECT, INSERT, UPDATE ON api_keys TO app_user;
-- GRANT SELECT, INSERT, DELETE ON rate_limit_log TO app_user;
-- GRANT EXECUTE ON cleanup_rate_limits TO app_user;

-- ====================
-- Schema Verification
-- ====================

-- Verify tables were created
SELECT table_name FROM user_tables
WHERE table_name IN ('VIDEO_JOBS', 'API_KEYS', 'RATE_LIMIT_LOG');

-- Verify indexes were created
SELECT index_name, table_name FROM user_indexes
WHERE table_name IN ('VIDEO_JOBS', 'API_KEYS', 'RATE_LIMIT_LOG');

-- ==========================================
-- Schema Setup Complete
-- ==========================================
-- Next steps:
-- 1. Insert your API keys (hashed with SHA-256)
-- 2. Test connection from application
-- 3. Monitor performance and adjust indexes as needed
-- 4. Set up backup schedule
-- 5. Configure cleanup jobs