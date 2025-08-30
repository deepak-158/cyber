-- Cyber Threat Detection Database Schema
-- PostgreSQL initialization script

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create custom types
CREATE TYPE platform_type AS ENUM ('twitter', 'reddit', 'youtube', 'facebook', 'instagram', 'telegram');
CREATE TYPE alert_severity AS ENUM ('low', 'medium', 'high', 'critical');
CREATE TYPE post_status AS ENUM ('active', 'deleted', 'suspended', 'flagged');
CREATE TYPE campaign_status AS ENUM ('detected', 'investigating', 'confirmed', 'false_positive', 'resolved');
CREATE TYPE language_code AS ENUM ('en', 'hi', 'mr', 'ta', 'te', 'gu', 'bn', 'kn', 'ml', 'or', 'pa', 'as', 'ur', 'mixed');

-- Authors/Users table
CREATE TABLE authors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    platform platform_type NOT NULL,
    platform_user_id VARCHAR(255) NOT NULL,
    username VARCHAR(255) NOT NULL,
    display_name VARCHAR(500),
    bio TEXT,
    location VARCHAR(255),
    url VARCHAR(500),
    followers_count INTEGER DEFAULT 0,
    following_count INTEGER DEFAULT 0,
    posts_count INTEGER DEFAULT 0,
    verified BOOLEAN DEFAULT FALSE,
    account_created_at TIMESTAMP WITH TIME ZONE,
    profile_image_url VARCHAR(1000),
    is_private BOOLEAN DEFAULT FALSE,
    
    -- Bot detection features
    bot_likelihood_score FLOAT DEFAULT 0.0 CHECK (bot_likelihood_score >= 0.0 AND bot_likelihood_score <= 1.0),
    bot_features JSONB,
    
    -- Metadata
    first_seen_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    UNIQUE(platform, platform_user_id),
    INDEX (username),
    INDEX (platform, platform_user_id),
    INDEX (bot_likelihood_score),
    INDEX (account_created_at),
    INDEX (followers_count),
    INDEX USING GIN (bio gin_trgm_ops),
    INDEX USING GIN (bot_features)
);

-- Posts table
CREATE TABLE posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    platform platform_type NOT NULL,
    platform_post_id VARCHAR(255) NOT NULL,
    author_id UUID NOT NULL REFERENCES authors(id) ON DELETE CASCADE,
    
    -- Content
    text_content TEXT NOT NULL,
    media_urls TEXT[],
    hashtags TEXT[],
    mentions TEXT[],
    urls TEXT[],
    
    -- Metadata
    posted_at TIMESTAMP WITH TIME ZONE NOT NULL,
    language language_code,
    status post_status DEFAULT 'active',
    
    -- Engagement metrics
    likes_count INTEGER DEFAULT 0,
    retweets_count INTEGER DEFAULT 0,
    replies_count INTEGER DEFAULT 0,
    views_count INTEGER DEFAULT 0,
    
    -- Parent post (for replies/retweets)
    parent_post_id UUID REFERENCES posts(id),
    is_retweet BOOLEAN DEFAULT FALSE,
    is_reply BOOLEAN DEFAULT FALSE,
    
    -- NLP Analysis Results
    toxicity_score FLOAT DEFAULT 0.0 CHECK (toxicity_score >= 0.0 AND toxicity_score <= 1.0),
    stance_scores JSONB, -- {"anti_india": 0.8, "pro_india": 0.1, "neutral": 0.1}
    sentiment_scores JSONB, -- {"positive": 0.1, "negative": 0.8, "neutral": 0.1}
    narrative_cluster_id INTEGER,
    embedding_vector FLOAT[],
    
    -- Timestamps
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    analyzed_at TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(platform, platform_post_id),
    INDEX (author_id),
    INDEX (posted_at),
    INDEX (platform, platform_post_id),
    INDEX (language),
    INDEX (toxicity_score),
    INDEX (narrative_cluster_id),
    INDEX (status),
    INDEX USING GIN (text_content gin_trgm_ops),
    INDEX USING GIN (hashtags),
    INDEX USING GIN (mentions),
    INDEX USING GIN (stance_scores),
    INDEX USING GIN (sentiment_scores)
);

-- Campaigns table (detected coordinated campaigns)
CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(500) NOT NULL,
    description TEXT,
    status campaign_status DEFAULT 'detected',
    
    -- Detection metrics
    campaign_score FLOAT NOT NULL CHECK (campaign_score >= 0.0 AND campaign_score <= 100.0),
    confidence_score FLOAT DEFAULT 0.0 CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    
    -- Campaign characteristics
    platforms platform_type[] NOT NULL,
    languages language_code[] NOT NULL,
    keywords TEXT[] NOT NULL,
    hashtags TEXT[],
    
    -- Time boundaries
    detected_start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    detected_end_time TIMESTAMP WITH TIME ZONE,
    peak_activity_time TIMESTAMP WITH TIME ZONE,
    
    -- Statistics
    total_posts INTEGER DEFAULT 0,
    unique_authors INTEGER DEFAULT 0,
    total_engagement INTEGER DEFAULT 0,
    geographic_spread JSONB, -- {"countries": ["IN", "PK"], "states": ["UP", "MH"]}
    
    -- Detection algorithms that flagged this campaign
    detection_methods TEXT[] NOT NULL, -- ["burst_detection", "coordination_analysis", "bot_network"]
    detection_details JSONB, -- Detailed results from each method
    
    -- Human review
    human_reviewed BOOLEAN DEFAULT FALSE,
    human_reviewer_id VARCHAR(255),
    human_review_notes TEXT,
    human_review_timestamp TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX (status),
    INDEX (campaign_score DESC),
    INDEX (detected_start_time),
    INDEX (platforms),
    INDEX (languages),
    INDEX USING GIN (keywords),
    INDEX USING GIN (hashtags),
    INDEX USING GIN (detection_methods),
    INDEX USING GIN (geographic_spread)
);

-- Campaign Posts junction table
CREATE TABLE campaign_posts (
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    post_id UUID NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    relevance_score FLOAT DEFAULT 1.0 CHECK (relevance_score >= 0.0 AND relevance_score <= 1.0),
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (campaign_id, post_id),
    INDEX (campaign_id),
    INDEX (post_id),
    INDEX (relevance_score)
);

-- Alerts table
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    severity alert_severity NOT NULL,
    
    -- Alert triggers
    trigger_conditions JSONB NOT NULL, -- What conditions triggered this alert
    trigger_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Alert status
    is_active BOOLEAN DEFAULT TRUE,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(255),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    
    -- Resolution
    resolved BOOLEAN DEFAULT FALSE,
    resolved_by VARCHAR(255),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT,
    
    -- Notifications
    notification_sent BOOLEAN DEFAULT FALSE,
    notification_channels TEXT[], -- ["email", "slack", "webhook"]
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX (campaign_id),
    INDEX (severity),
    INDEX (trigger_timestamp),
    INDEX (is_active),
    INDEX (acknowledged),
    INDEX (resolved),
    INDEX USING GIN (trigger_conditions),
    INDEX USING GIN (notification_channels)
);

-- Narrative Clusters table
CREATE TABLE narrative_clusters (
    id SERIAL PRIMARY KEY,
    cluster_name VARCHAR(500),
    cluster_description TEXT,
    
    -- Cluster characteristics
    dominant_keywords TEXT[] NOT NULL,
    representative_texts TEXT[],
    cluster_center_embedding FLOAT[],
    
    -- Statistics
    post_count INTEGER DEFAULT 0,
    author_count INTEGER DEFAULT 0,
    avg_toxicity_score FLOAT DEFAULT 0.0,
    avg_stance_scores JSONB,
    
    -- Time boundaries
    first_post_time TIMESTAMP WITH TIME ZONE,
    last_post_time TIMESTAMP WITH TIME ZONE,
    peak_activity_time TIMESTAMP WITH TIME ZONE,
    
    -- Cluster metadata
    languages language_code[] NOT NULL,
    platforms platform_type[] NOT NULL,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX (post_count DESC),
    INDEX (avg_toxicity_score DESC),
    INDEX (first_post_time),
    INDEX (last_post_time),
    INDEX USING GIN (dominant_keywords),
    INDEX USING GIN (languages),
    INDEX USING GIN (platforms),
    INDEX USING GIN (avg_stance_scores)
);

-- Coordination Events table (for burst detection and coordination analysis)
CREATE TABLE coordination_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(100) NOT NULL, -- "burst", "coordinated_posting", "amplification"
    
    -- Event characteristics
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    peak_time TIMESTAMP WITH TIME ZONE,
    intensity_score FLOAT NOT NULL CHECK (intensity_score >= 0.0),
    
    -- Involved entities
    post_ids UUID[] NOT NULL,
    author_ids UUID[] NOT NULL,
    keywords TEXT[],
    hashtags TEXT[],
    
    -- Detection details
    detection_algorithm VARCHAR(100) NOT NULL,
    algorithm_parameters JSONB,
    statistical_significance FLOAT,
    
    -- Associated campaign (if any)
    campaign_id UUID REFERENCES campaigns(id),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX (event_type),
    INDEX (start_time),
    INDEX (end_time),
    INDEX (intensity_score DESC),
    INDEX (campaign_id),
    INDEX (detection_algorithm),
    INDEX USING GIN (post_ids),
    INDEX USING GIN (author_ids),
    INDEX USING GIN (keywords),
    INDEX USING GIN (hashtags)
);

-- System Logs table for monitoring and debugging
CREATE TABLE system_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    level VARCHAR(20) NOT NULL, -- "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
    component VARCHAR(100) NOT NULL, -- "data_collector", "nlp_analyzer", "campaign_detector", etc.
    message TEXT NOT NULL,
    details JSONB,
    
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX (level),
    INDEX (component),
    INDEX (timestamp),
    INDEX USING GIN (details)
);

-- Create triggers for updating timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_authors_updated_at BEFORE UPDATE ON authors FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_campaigns_updated_at BEFORE UPDATE ON campaigns FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_alerts_updated_at BEFORE UPDATE ON alerts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_narrative_clusters_updated_at BEFORE UPDATE ON narrative_clusters FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create materialized views for performance
CREATE MATERIALIZED VIEW campaign_statistics AS
SELECT 
    c.id,
    c.name,
    c.status,
    c.campaign_score,
    COUNT(DISTINCT cp.post_id) as post_count,
    COUNT(DISTINCT p.author_id) as author_count,
    AVG(p.toxicity_score) as avg_toxicity,
    AVG(p.likes_count + p.retweets_count + p.replies_count) as avg_engagement,
    c.detected_start_time,
    c.detected_end_time
FROM campaigns c
LEFT JOIN campaign_posts cp ON c.id = cp.campaign_id
LEFT JOIN posts p ON cp.post_id = p.id
GROUP BY c.id, c.name, c.status, c.campaign_score, c.detected_start_time, c.detected_end_time;

CREATE UNIQUE INDEX ON campaign_statistics (id);
CREATE INDEX ON campaign_statistics (campaign_score DESC);
CREATE INDEX ON campaign_statistics (post_count DESC);
CREATE INDEX ON campaign_statistics (avg_toxicity DESC);

-- Create performance monitoring view
CREATE VIEW system_performance AS
SELECT 
    DATE_TRUNC('hour', timestamp) as hour,
    component,
    level,
    COUNT(*) as log_count
FROM system_logs
WHERE timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', timestamp), component, level
ORDER BY hour DESC, log_count DESC;

-- Insert initial data for testing
INSERT INTO narrative_clusters (cluster_name, cluster_description, dominant_keywords, languages, platforms) VALUES
('Anti-India Economic Narratives', 'Cluster focusing on economic criticism and misinformation about India', ARRAY['economy', 'gdp', 'poverty', 'unemployment'], ARRAY['en', 'hi'], ARRAY['twitter', 'reddit']),
('Kashmir Misinformation', 'Coordinated misinformation campaigns about Kashmir situation', ARRAY['kashmir', 'occupation', 'human rights'], ARRAY['en', 'ur'], ARRAY['twitter', 'facebook']),
('Religious Division Content', 'Content aimed at creating religious tensions', ARRAY['hindu', 'muslim', 'religious', 'violence'], ARRAY['en', 'hi', 'ur'], ARRAY['twitter', 'telegram']);

COMMIT;