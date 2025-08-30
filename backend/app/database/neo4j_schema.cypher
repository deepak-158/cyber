// Cyber Threat Detection - Neo4j Graph Schema
// This file contains Cypher queries to set up the Neo4j graph database schema
// for social network analysis and coordination detection

// ============================================================================
// NODE TYPES AND CONSTRAINTS
// ============================================================================

// Create uniqueness constraints for nodes
CREATE CONSTRAINT user_platform_id IF NOT EXISTS FOR (u:User) REQUIRE (u.platform, u.platform_user_id) IS UNIQUE;
CREATE CONSTRAINT post_platform_id IF NOT EXISTS FOR (p:Post) REQUIRE (p.platform, p.platform_post_id) IS UNIQUE;
CREATE CONSTRAINT hashtag_name IF NOT EXISTS FOR (h:Hashtag) REQUIRE h.name IS UNIQUE;
CREATE CONSTRAINT url_address IF NOT EXISTS FOR (u:URL) REQUIRE u.address IS UNIQUE;
CREATE CONSTRAINT campaign_id IF NOT EXISTS FOR (c:Campaign) REQUIRE c.campaign_id IS UNIQUE;
CREATE CONSTRAINT cluster_id IF NOT EXISTS FOR (n:NarrativeCluster) REQUIRE n.cluster_id IS UNIQUE;

// Create indexes for performance
CREATE INDEX user_username IF NOT EXISTS FOR (u:User) ON u.username;
CREATE INDEX user_created_at IF NOT EXISTS FOR (u:User) ON u.created_at;
CREATE INDEX user_bot_score IF NOT EXISTS FOR (u:User) ON u.bot_likelihood_score;
CREATE INDEX post_timestamp IF NOT EXISTS FOR (p:Post) ON p.posted_at;
CREATE INDEX post_toxicity IF NOT EXISTS FOR (p:Post) ON p.toxicity_score;
CREATE INDEX post_stance IF NOT EXISTS FOR (p:Post) ON p.stance_score;
CREATE INDEX hashtag_frequency IF NOT EXISTS FOR (h:Hashtag) ON h.usage_count;
CREATE INDEX campaign_score IF NOT EXISTS FOR (c:Campaign) ON c.campaign_score;

// ============================================================================
// NODE LABELS AND PROPERTIES
// ============================================================================

// User nodes represent social media accounts
// Properties:
// - platform: twitter, reddit, youtube, etc.
// - platform_user_id: unique ID on the platform
// - username: display username
// - display_name: user's display name
// - bio: user bio/description
// - location: user-stated location
// - followers_count: number of followers
// - following_count: number of following
// - verified: verification status
// - created_at: account creation date
// - bot_likelihood_score: 0.0-1.0 bot probability
// - profile_features: JSON of extracted features
// - last_seen: last activity timestamp

// Post nodes represent individual posts/tweets/comments
// Properties:
// - platform: source platform
// - platform_post_id: unique ID on platform
// - text: post content
// - posted_at: timestamp
// - language: detected language
// - toxicity_score: 0.0-1.0 toxicity level
// - stance_score: stance towards India (-1 to 1)
// - sentiment_score: overall sentiment (-1 to 1)
// - engagement_count: total likes + shares + comments
// - reach_estimate: estimated reach
// - embedding_vector: text embedding for similarity

// Hashtag nodes represent hashtags
// Properties:
// - name: hashtag text (without #)
// - usage_count: total times used
// - first_seen: first occurrence
// - last_seen: last occurrence
// - toxicity_avg: average toxicity of posts using this hashtag
// - stance_avg: average stance of posts using this hashtag

// URL nodes represent shared links
// Properties:
// - address: full URL
// - domain: extracted domain
// - title: page title if available
// - description: page description
// - share_count: times shared
// - suspicious_score: 0.0-1.0 suspiciousness rating

// Campaign nodes represent detected coordinated campaigns
// Properties:
// - campaign_id: unique identifier
// - name: campaign name
// - description: campaign description
// - start_time: campaign start
// - end_time: campaign end
// - campaign_score: 0-100 coordination score
// - detection_methods: array of detection algorithms used
// - status: detected, confirmed, false_positive

// NarrativeCluster nodes represent thematic clusters
// Properties:
// - cluster_id: unique identifier
// - name: cluster name
// - keywords: dominant keywords
// - post_count: number of posts in cluster
// - avg_toxicity: average toxicity score
// - avg_stance: average stance score

// ============================================================================
// RELATIONSHIP TYPES
// ============================================================================

// User-to-Post relationships
// (:User)-[:POSTED]->(:Post)
// Properties: timestamp

// (:User)-[:RETWEETED]->(:Post)
// Properties: timestamp, original_post_id

// (:User)-[:REPLIED_TO]->(:Post)
// Properties: timestamp, reply_post_id

// (:User)-[:LIKED]->(:Post)
// Properties: timestamp

// User-to-User relationships
// (:User)-[:FOLLOWS]->(:User)
// Properties: since_date, is_active

// (:User)-[:MENTIONS]->(:User)
// Properties: post_id, timestamp, context

// (:User)-[:COORDINATES_WITH]->(:User)
// Properties: coordination_score, evidence_posts, detection_method, confidence

// Post-to-Content relationships
// (:Post)-[:CONTAINS_HASHTAG]->(:Hashtag)
// Properties: position_in_text

// (:Post)-[:CONTAINS_URL]->(:URL)
// Properties: position_in_text, click_count

// (:Post)-[:SIMILAR_TO]->(:Post)
// Properties: similarity_score, similarity_type (text, timing, engagement)

// (:Post)-[:AMPLIFIES]->(:Post)
// Properties: amplification_strength, method (retweet, quote, manual)

// Campaign relationships
// (:Campaign)-[:INCLUDES_POST]->(:Post)
// Properties: relevance_score, detection_confidence

// (:Campaign)-[:INVOLVES_USER]->(:User)
// Properties: participation_score, role (coordinator, amplifier, bot)

// (:Campaign)-[:TARGETS_NARRATIVE]->(:NarrativeCluster)
// Properties: targeting_strength

// Cluster relationships
// (:NarrativeCluster)-[:CONTAINS_POST]->(:Post)
// Properties: cluster_distance, assignment_confidence

// (:NarrativeCluster)-[:EVOLVES_TO]->(:NarrativeCluster)
// Properties: transition_strength, time_gap

// ============================================================================
// SAMPLE DATA CREATION QUERIES
// ============================================================================

// Create sample users with bot likelihood scores
MERGE (u1:User {
    platform: 'twitter',
    platform_user_id: 'user_001',
    username: 'account_activist_001',
    display_name: 'Truth Seeker',
    followers_count: 1500,
    following_count: 200,
    verified: false,
    created_at: datetime('2020-01-15T10:30:00Z'),
    bot_likelihood_score: 0.85,
    profile_features: {
        posting_frequency: 45.2,
        account_age_days: 1400,
        username_pattern_score: 0.9,
        profile_completeness: 0.3
    }
});

MERGE (u2:User {
    platform: 'twitter',
    platform_user_id: 'user_002',
    username: 'news_reporter_india',
    display_name: 'India News Reporter',
    followers_count: 50000,
    following_count: 1000,
    verified: true,
    created_at: datetime('2018-05-10T08:15:00Z'),
    bot_likelihood_score: 0.1,
    profile_features: {
        posting_frequency: 8.5,
        account_age_days: 2000,
        username_pattern_score: 0.2,
        profile_completeness: 0.95
    }
});

// Create sample posts with NLP analysis results
MERGE (p1:Post {
    platform: 'twitter',
    platform_post_id: 'post_001',
    text: 'India economy is collapsing! Unemployment at all time high #IndiaFailing #EconomicCrisis',
    posted_at: datetime('2024-08-30T14:30:00Z'),
    language: 'en',
    toxicity_score: 0.75,
    stance_score: -0.8,
    sentiment_score: -0.9,
    engagement_count: 1500,
    embedding_vector: [0.1, -0.3, 0.7, -0.2, 0.4]
});

MERGE (p2:Post {
    platform: 'twitter',
    platform_post_id: 'post_002',
    text: 'Responding to misinformation: India continues robust economic growth with strong fundamentals',
    posted_at: datetime('2024-08-30T15:45:00Z'),
    language: 'en',
    toxicity_score: 0.05,
    stance_score: 0.7,
    sentiment_score: 0.6,
    engagement_count: 800,
    embedding_vector: [0.2, 0.4, -0.1, 0.3, -0.5]
});

// Create hashtags
MERGE (h1:Hashtag {
    name: 'IndiaFailing',
    usage_count: 2500,
    first_seen: datetime('2024-08-25T09:00:00Z'),
    last_seen: datetime('2024-08-30T18:00:00Z'),
    toxicity_avg: 0.78,
    stance_avg: -0.85
});

MERGE (h2:Hashtag {
    name: 'EconomicCrisis',
    usage_count: 1800,
    first_seen: datetime('2024-08-26T12:00:00Z'),
    last_seen: datetime('2024-08-30T17:30:00Z'),
    toxicity_avg: 0.65,
    stance_avg: -0.72
});

// Create campaign
MERGE (c1:Campaign {
    campaign_id: 'campaign_001',
    name: 'Anti-India Economic Narrative Campaign',
    description: 'Coordinated campaign spreading economic misinformation about India',
    start_time: datetime('2024-08-25T00:00:00Z'),
    end_time: datetime('2024-08-30T23:59:59Z'),
    campaign_score: 87.5,
    detection_methods: ['burst_detection', 'coordination_analysis', 'bot_network'],
    status: 'detected'
});

// Create narrative cluster
MERGE (n1:NarrativeCluster {
    cluster_id: 'cluster_001',
    name: 'Economic Doom Narratives',
    keywords: ['economy', 'unemployment', 'crisis', 'failing'],
    post_count: 1250,
    avg_toxicity: 0.72,
    avg_stance: -0.75
});

// ============================================================================
// CREATE RELATIONSHIPS
// ============================================================================

// User posted content
MATCH (u:User {platform_user_id: 'user_001'}), (p:Post {platform_post_id: 'post_001'})
MERGE (u)-[:POSTED {timestamp: datetime('2024-08-30T14:30:00Z')}]->(p);

MATCH (u:User {platform_user_id: 'user_002'}), (p:Post {platform_post_id: 'post_002'})
MERGE (u)-[:POSTED {timestamp: datetime('2024-08-30T15:45:00Z')}]->(p);

// Posts contain hashtags
MATCH (p:Post {platform_post_id: 'post_001'}), (h:Hashtag {name: 'IndiaFailing'})
MERGE (p)-[:CONTAINS_HASHTAG {position_in_text: 45}]->(h);

MATCH (p:Post {platform_post_id: 'post_001'}), (h:Hashtag {name: 'EconomicCrisis'})
MERGE (p)-[:CONTAINS_HASHTAG {position_in_text: 58}]->(h);

// Campaign includes posts and users
MATCH (c:Campaign {campaign_id: 'campaign_001'}), (p:Post {platform_post_id: 'post_001'})
MERGE (c)-[:INCLUDES_POST {relevance_score: 0.95, detection_confidence: 0.88}]->(p);

MATCH (c:Campaign {campaign_id: 'campaign_001'}), (u:User {platform_user_id: 'user_001'})
MERGE (c)-[:INVOLVES_USER {participation_score: 0.82, role: 'amplifier'}]->(u);

// Narrative cluster contains posts
MATCH (n:NarrativeCluster {cluster_id: 'cluster_001'}), (p:Post {platform_post_id: 'post_001'})
MERGE (n)-[:CONTAINS_POST {cluster_distance: 0.15, assignment_confidence: 0.92}]->(p);

// User coordination relationships (detected suspicious coordination)
MATCH (u1:User {platform_user_id: 'user_001'}), (u2:User {platform_user_id: 'user_002'})
MERGE (u1)-[:COORDINATES_WITH {
    coordination_score: 0.65,
    evidence_posts: ['post_001', 'post_002'],
    detection_method: 'temporal_similarity',
    confidence: 0.78
}]->(u2);

// Post similarity relationships
MATCH (p1:Post {platform_post_id: 'post_001'}), (p2:Post {platform_post_id: 'post_002'})
MERGE (p1)-[:SIMILAR_TO {
    similarity_score: 0.45,
    similarity_type: 'semantic'
}]->(p2);

// ============================================================================
// USEFUL GRAPH QUERIES FOR ANALYSIS
// ============================================================================

// Query to find potential bot networks
// MATCH (u:User)-[:COORDINATES_WITH]-(other:User)
// WHERE u.bot_likelihood_score > 0.7 AND other.bot_likelihood_score > 0.7
// RETURN u, other, collect(u.username) as potential_bot_network;

// Query to find posts in coordinated campaigns with high toxicity
// MATCH (c:Campaign)-[:INCLUDES_POST]->(p:Post)
// WHERE p.toxicity_score > 0.7 AND c.campaign_score > 80
// RETURN c.name, p.text, p.toxicity_score, p.stance_score
// ORDER BY p.toxicity_score DESC;

// Query to find hashtag co-occurrence patterns
// MATCH (p:Post)-[:CONTAINS_HASHTAG]->(h1:Hashtag),
//       (p)-[:CONTAINS_HASHTAG]->(h2:Hashtag)
// WHERE h1 <> h2 AND h1.toxicity_avg > 0.6 AND h2.toxicity_avg > 0.6
// RETURN h1.name, h2.name, count(p) as co_occurrences
// ORDER BY co_occurrences DESC;

// Query to find influential spreaders in campaigns
// MATCH (c:Campaign)-[:INVOLVES_USER]->(u:User)-[:POSTED]->(p:Post)
// WHERE c.campaign_score > 75
// RETURN u.username, u.followers_count, count(p) as posts_in_campaign,
//        avg(p.engagement_count) as avg_engagement
// ORDER BY u.followers_count DESC;

// Query to trace narrative evolution
// MATCH path = (n1:NarrativeCluster)-[:EVOLVES_TO*1..3]->(n2:NarrativeCluster)
// WHERE n1.avg_toxicity > 0.6
// RETURN path, length(path) as evolution_steps;

// ============================================================================
// GRAPH DATA SCIENCE PROJECTIONS
// ============================================================================

// Create a projection for community detection
// CALL gds.graph.project(
//     'user-coordination-network',
//     'User',
//     {
//         COORDINATES_WITH: {
//             properties: ['coordination_score']
//         }
//     }
// );

// Create a projection for centrality analysis
// CALL gds.graph.project(
//     'influence-network',
//     ['User', 'Post'],
//     {
//         POSTED: {},
//         RETWEETED: {},
//         FOLLOWS: {}
//     }
// );

// ============================================================================
// PERIODIC MAINTENANCE QUERIES
// ============================================================================

// Update hashtag usage counts
// MATCH (h:Hashtag)<-[:CONTAINS_HASHTAG]-(p:Post)
// WITH h, count(p) as current_count
// SET h.usage_count = current_count;

// Update user engagement metrics
// MATCH (u:User)-[:POSTED]->(p:Post)
// WITH u, avg(p.engagement_count) as avg_engagement, count(p) as post_count
// SET u.avg_engagement = avg_engagement, u.total_posts = post_count;

// Clean up old temporary relationships (older than 30 days)
// MATCH ()-[r:SIMILAR_TO]->()
// WHERE r.created_at < datetime() - duration('P30D')
// DELETE r;

COMMIT;