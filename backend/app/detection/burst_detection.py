"""
Burst Detection Module
Detects temporal anomalies and coordinated bursts in posting activity
using Kleinberg's burst detection algorithm and statistical methods
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from scipy import stats
from scipy.signal import find_peaks
import math
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)

class BurstDetector:
    """Detects burst activity patterns in social media posts"""
    
    def __init__(self):
        # Kleinberg algorithm parameters
        self.s_factor = 2.0  # State transition cost factor
        self.gamma = 1.0     # Burst strength threshold
        
        # Z-score parameters
        self.z_threshold = 2.5  # Z-score threshold for anomaly detection
        self.window_size = 24   # Hours for rolling window analysis
        
        # Burst categories
        self.burst_types = {
            'low': (2.0, 3.0),      # Low intensity burst
            'medium': (3.0, 4.0),   # Medium intensity burst
            'high': (4.0, 6.0),     # High intensity burst
            'extreme': (6.0, float('inf'))  # Extreme burst
        }
    
    def detect_bursts(self, posts: List[Dict[str, Any]], 
                     time_window_hours: int = 24) -> Dict[str, Any]:
        """
        Detect burst patterns in posting activity
        
        Args:
            posts: List of post dictionaries with timestamp information
            time_window_hours: Time window for burst detection analysis
            
        Returns:
            Dict containing burst events, statistics, and anomalies
        """
        if not posts:
            return self._empty_burst_result()
        
        logger.info(f"Analyzing {len(posts)} posts for burst patterns")
        
        # Prepare time series data
        time_series = self._prepare_time_series(posts, time_window_hours)
        
        if len(time_series) < 3:
            return self._empty_burst_result()
        
        # Detect bursts using multiple methods
        kleinberg_bursts = self._kleinberg_burst_detection(time_series)
        zscore_anomalies = self._zscore_anomaly_detection(time_series)
        peak_bursts = self._peak_detection(time_series)
        
        # Analyze burst characteristics
        burst_analysis = self._analyze_burst_characteristics(
            posts, kleinberg_bursts, zscore_anomalies, peak_bursts
        )
        
        # Generate coordination indicators
        coordination_indicators = self._detect_coordination_patterns(posts, burst_analysis)
        
        return {
            'total_posts': len(posts),
            'time_span_hours': time_window_hours,
            'kleinberg_bursts': kleinberg_bursts,
            'zscore_anomalies': zscore_anomalies,
            'peak_bursts': peak_bursts,
            'burst_analysis': burst_analysis,
            'coordination_indicators': coordination_indicators,
            'time_series': time_series.to_dict() if hasattr(time_series, 'to_dict') else time_series
        }
    
    def _prepare_time_series(self, posts: List[Dict], window_hours: int) -> pd.DataFrame:
        """Prepare time series data from posts"""
        try:
            # Extract timestamps
            timestamps = []
            for post in posts:
                if 'posted_at' in post:
                    if isinstance(post['posted_at'], str):
                        # Parse ISO format
                        timestamp = pd.to_datetime(post['posted_at'])
                        timestamps.append(timestamp)
                    elif isinstance(post['posted_at'], datetime):
                        timestamps.append(pd.to_datetime(post['posted_at']))
            
            if not timestamps:
                return pd.DataFrame()
            
            # Create DataFrame
            df = pd.DataFrame({'timestamp': timestamps})
            df = df.sort_values('timestamp')
            
            # Resample to hourly bins
            df.set_index('timestamp', inplace=True)
            hourly_counts = df.resample('H').size()
            
            # Fill missing hours with 0
            start_time = hourly_counts.index.min()
            end_time = hourly_counts.index.max()
            full_range = pd.date_range(start=start_time, end=end_time, freq='H')
            hourly_counts = hourly_counts.reindex(full_range, fill_value=0)
            
            # Create time series DataFrame
            time_series = pd.DataFrame({
                'timestamp': hourly_counts.index,
                'count': hourly_counts.values
            })
            
            return time_series
            
        except Exception as e:
            logger.error(f"Error preparing time series: {str(e)}")
            return pd.DataFrame()
    
    def _kleinberg_burst_detection(self, time_series: pd.DataFrame) -> List[Dict]:
        """Implement Kleinberg's burst detection algorithm"""
        try:
            if len(time_series) < 3:
                return []
            
            counts = time_series['count'].values
            timestamps = time_series['timestamp'].values
            
            # Calculate burst states using Kleinberg algorithm
            n = len(counts)
            if n < 2:
                return []
            
            # Calculate base rate
            total_events = np.sum(counts)
            total_time = n
            base_rate = total_events / total_time if total_time > 0 else 0
            
            if base_rate == 0:
                return []
            
            # Define states (0 = normal, 1+ = burst levels)
            num_states = 3
            rates = [base_rate * (self.s_factor ** i) for i in range(num_states)]
            
            # Dynamic programming for optimal state sequence
            costs = np.full((n, num_states), float('inf'))
            paths = np.zeros((n, num_states), dtype=int)
            
            # Initialize first time step
            for state in range(num_states):
                if counts[0] > 0:
                    costs[0, state] = -counts[0] * math.log(rates[state]) + rates[state]
                else:
                    costs[0, state] = rates[state]
            
            # Fill DP table
            for t in range(1, n):
                for curr_state in range(num_states):
                    for prev_state in range(num_states):
                        # Transition cost
                        transition_cost = 0
                        if curr_state > prev_state:
                            transition_cost = (curr_state - prev_state) * self.gamma
                        
                        # Emission cost
                        if counts[t] > 0:
                            emission_cost = -counts[t] * math.log(rates[curr_state]) + rates[curr_state]
                        else:
                            emission_cost = rates[curr_state]
                        
                        total_cost = costs[t-1, prev_state] + transition_cost + emission_cost
                        
                        if total_cost < costs[t, curr_state]:
                            costs[t, curr_state] = total_cost
                            paths[t, curr_state] = prev_state
            
            # Backtrack to find optimal path
            states = np.zeros(n, dtype=int)
            states[-1] = np.argmin(costs[-1, :])
            
            for t in range(n-2, -1, -1):
                states[t] = paths[t+1, states[t+1]]
            
            # Extract burst periods
            bursts = []
            burst_start = None
            
            for i, state in enumerate(states):
                if state > 0 and burst_start is None:
                    burst_start = i
                elif state == 0 and burst_start is not None:
                    bursts.append({
                        'start_time': timestamps[burst_start],
                        'end_time': timestamps[i-1],
                        'duration_hours': i - burst_start,
                        'intensity': np.mean(states[burst_start:i]),
                        'total_posts': np.sum(counts[burst_start:i]),
                        'method': 'kleinberg'
                    })
                    burst_start = None
            
            # Handle case where burst continues to end
            if burst_start is not None:
                bursts.append({
                    'start_time': timestamps[burst_start],
                    'end_time': timestamps[-1],
                    'duration_hours': n - burst_start,
                    'intensity': np.mean(states[burst_start:]),
                    'total_posts': np.sum(counts[burst_start:]),
                    'method': 'kleinberg'
                })
            
            return bursts
            
        except Exception as e:
            logger.error(f"Error in Kleinberg burst detection: {str(e)}")
            return []
    
    def _zscore_anomaly_detection(self, time_series: pd.DataFrame) -> List[Dict]:
        """Detect anomalies using z-score method"""
        try:
            if len(time_series) < 3:
                return []
            
            counts = time_series['count'].values
            timestamps = time_series['timestamp'].values
            
            # Calculate rolling statistics
            window_size = min(self.window_size, len(counts) // 2)
            if window_size < 2:
                window_size = 2
            
            # Rolling mean and std
            rolling_mean = pd.Series(counts).rolling(window=window_size, center=True).mean()
            rolling_std = pd.Series(counts).rolling(window=window_size, center=True).std()
            
            # Handle NaN values
            rolling_mean = rolling_mean.fillna(np.mean(counts))
            rolling_std = rolling_std.fillna(np.std(counts))
            
            # Calculate z-scores
            z_scores = np.abs((counts - rolling_mean) / (rolling_std + 1e-8))
            
            # Find anomalies
            anomalies = []
            anomaly_indices = np.where(z_scores > self.z_threshold)[0]
            
            for idx in anomaly_indices:
                anomalies.append({
                    'timestamp': timestamps[idx],
                    'count': counts[idx],
                    'z_score': z_scores[idx],
                    'expected': rolling_mean.iloc[idx],
                    'method': 'zscore'
                })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error in z-score anomaly detection: {str(e)}")
            return []
    
    def _peak_detection(self, time_series: pd.DataFrame) -> List[Dict]:
        """Detect peaks in posting activity"""
        try:
            if len(time_series) < 3:
                return []
            
            counts = time_series['count'].values
            timestamps = time_series['timestamp'].values
            
            # Find peaks
            mean_count = np.mean(counts)
            std_count = np.std(counts)
            
            # Set minimum height for peaks
            min_height = max(mean_count + 2 * std_count, np.max(counts) * 0.3)
            
            # Find peaks with minimum height and distance
            peaks, properties = find_peaks(
                counts,
                height=min_height,
                distance=2,  # Minimum 2 hours between peaks
                prominence=std_count
            )
            
            # Create peak objects
            peak_bursts = []
            for peak_idx in peaks:
                peak_bursts.append({
                    'timestamp': timestamps[peak_idx],
                    'count': counts[peak_idx],
                    'height': properties['peak_heights'][list(peaks).index(peak_idx)],
                    'prominence': properties['prominences'][list(peaks).index(peak_idx)],
                    'method': 'peak_detection'
                })
            
            return peak_bursts
            
        except Exception as e:
            logger.error(f"Error in peak detection: {str(e)}")
            return []
    
    def _analyze_burst_characteristics(self, posts: List[Dict], 
                                     kleinberg_bursts: List[Dict],
                                     zscore_anomalies: List[Dict],
                                     peak_bursts: List[Dict]) -> Dict[str, Any]:
        """Analyze characteristics of detected bursts"""
        analysis = {
            'burst_summary': {
                'kleinberg_bursts': len(kleinberg_bursts),
                'zscore_anomalies': len(zscore_anomalies),
                'peak_bursts': len(peak_bursts)
            },
            'intensity_distribution': {},
            'temporal_patterns': {},
            'content_analysis': {}
        }
        
        # Analyze Kleinberg burst intensities
        if kleinberg_bursts:
            intensities = [burst['intensity'] for burst in kleinberg_bursts]
            analysis['intensity_distribution'] = {
                'mean_intensity': np.mean(intensities),
                'max_intensity': np.max(intensities),
                'std_intensity': np.std(intensities)
            }
            
            # Categorize burst levels
            burst_levels = {}
            for burst in kleinberg_bursts:
                level = self._categorize_burst_intensity(burst['intensity'])
                burst_levels[level] = burst_levels.get(level, 0) + 1
            
            analysis['intensity_distribution']['burst_levels'] = burst_levels
        
        # Analyze temporal patterns
        all_burst_times = []
        for burst in kleinberg_bursts:
            all_burst_times.append(burst['start_time'])
        
        if all_burst_times:
            analysis['temporal_patterns'] = self._analyze_temporal_patterns(all_burst_times)
        
        # Content analysis during bursts
        analysis['content_analysis'] = self._analyze_burst_content(posts, kleinberg_bursts)
        
        return analysis
    
    def _categorize_burst_intensity(self, intensity: float) -> str:
        """Categorize burst intensity level"""
        for level, (min_val, max_val) in self.burst_types.items():
            if min_val <= intensity < max_val:
                return level
        return 'low'
    
    def _analyze_temporal_patterns(self, burst_times: List[datetime]) -> Dict[str, Any]:
        """Analyze temporal patterns in burst timing"""
        if not burst_times:
            return {}
        
        # Convert to pandas datetime if needed
        burst_times = pd.to_datetime(burst_times)
        
        # Hour of day distribution
        hours = [t.hour for t in burst_times]
        hour_dist = dict(Counter(hours))
        
        # Day of week distribution
        days = [t.weekday() for t in burst_times]
        day_dist = dict(Counter(days))
        
        # Time intervals between bursts
        if len(burst_times) > 1:
            intervals = [(burst_times[i+1] - burst_times[i]).total_seconds() / 3600 
                        for i in range(len(burst_times)-1)]
            interval_stats = {
                'mean_interval_hours': np.mean(intervals),
                'std_interval_hours': np.std(intervals),
                'min_interval_hours': np.min(intervals),
                'max_interval_hours': np.max(intervals)
            }
        else:
            interval_stats = {}
        
        return {
            'hour_distribution': hour_dist,
            'day_distribution': day_dist,
            'interval_statistics': interval_stats
        }
    
    def _analyze_burst_content(self, posts: List[Dict], bursts: List[Dict]) -> Dict[str, Any]:
        """Analyze content characteristics during bursts"""
        burst_content = {
            'hashtag_analysis': {},
            'author_analysis': {},
            'platform_analysis': {},
            'language_analysis': {}
        }
        
        # Get posts during burst periods
        burst_posts = []
        for burst in bursts:
            start_time = pd.to_datetime(burst['start_time'])
            end_time = pd.to_datetime(burst['end_time'])
            
            for post in posts:
                post_time = pd.to_datetime(post.get('posted_at'))
                if start_time <= post_time <= end_time:
                    burst_posts.append(post)
        
        if not burst_posts:
            return burst_content
        
        # Hashtag analysis
        all_hashtags = []
        for post in burst_posts:
            hashtags = post.get('hashtags', [])
            all_hashtags.extend(hashtags)
        
        if all_hashtags:
            hashtag_counts = Counter(all_hashtags)
            burst_content['hashtag_analysis'] = {
                'top_hashtags': hashtag_counts.most_common(10),
                'unique_hashtags': len(set(all_hashtags)),
                'total_hashtag_uses': len(all_hashtags)
            }
        
        # Author analysis
        authors = [post.get('author', {}).get('username', 'unknown') for post in burst_posts]
        author_counts = Counter(authors)
        burst_content['author_analysis'] = {
            'unique_authors': len(set(authors)),
            'top_authors': author_counts.most_common(10),
            'posts_per_author': len(burst_posts) / len(set(authors)) if authors else 0
        }
        
        # Platform analysis
        platforms = [post.get('platform', 'unknown') for post in burst_posts]
        platform_counts = Counter(platforms)
        burst_content['platform_analysis'] = dict(platform_counts)
        
        # Language analysis
        languages = [post.get('language', 'unknown') for post in burst_posts]
        language_counts = Counter(languages)
        burst_content['language_analysis'] = dict(language_counts)
        
        return burst_content
    
    def _detect_coordination_patterns(self, posts: List[Dict], 
                                    burst_analysis: Dict) -> Dict[str, Any]:
        """Detect patterns indicating coordinated behavior"""
        coordination = {
            'suspected_coordination': False,
            'coordination_score': 0.0,
            'indicators': [],
            'evidence': {}
        }
        
        # Check for coordination indicators
        indicators = []
        score = 0.0
        
        # 1. Synchronized posting patterns
        if burst_analysis.get('temporal_patterns', {}).get('interval_statistics'):
            intervals = burst_analysis['temporal_patterns']['interval_statistics']
            if intervals.get('std_interval_hours', float('inf')) < 1.0:
                indicators.append('synchronized_timing')
                score += 0.3
        
        # 2. Repetitive hashtag usage
        hashtag_analysis = burst_analysis.get('content_analysis', {}).get('hashtag_analysis', {})
        if hashtag_analysis:
            top_hashtags = hashtag_analysis.get('top_hashtags', [])
            if top_hashtags and top_hashtags[0][1] > len(posts) * 0.5:
                indicators.append('repetitive_hashtags')
                score += 0.2
        
        # 3. Small number of highly active authors
        author_analysis = burst_analysis.get('content_analysis', {}).get('author_analysis', {})
        if author_analysis:
            posts_per_author = author_analysis.get('posts_per_author', 0)
            if posts_per_author > 5:
                indicators.append('hyperactive_authors')
                score += 0.3
        
        # 4. Burst intensity indicators
        intensity_dist = burst_analysis.get('intensity_distribution', {})
        if intensity_dist.get('max_intensity', 0) > 4.0:
            indicators.append('extreme_burst_intensity')
            score += 0.2
        
        coordination['coordination_score'] = min(1.0, score)
        coordination['suspected_coordination'] = score > 0.5
        coordination['indicators'] = indicators
        coordination['evidence'] = {
            'burst_analysis': burst_analysis,
            'threshold_exceeded': score > 0.5
        }
        
        return coordination
    
    def _empty_burst_result(self) -> Dict[str, Any]:
        """Return empty result when no bursts detected"""
        return {
            'total_posts': 0,
            'time_span_hours': 0,
            'kleinberg_bursts': [],
            'zscore_anomalies': [],
            'peak_bursts': [],
            'burst_analysis': {},
            'coordination_indicators': {
                'suspected_coordination': False,
                'coordination_score': 0.0,
                'indicators': [],
                'evidence': {}
            },
            'time_series': {}
        }
    
    def detect_hashtag_bursts(self, posts: List[Dict], hashtag: str) -> Dict[str, Any]:
        """Detect bursts for a specific hashtag"""
        # Filter posts containing the hashtag
        hashtag_posts = [
            post for post in posts 
            if hashtag.lower() in [h.lower() for h in post.get('hashtags', [])]
        ]
        
        if not hashtag_posts:
            return self._empty_burst_result()
        
        result = self.detect_bursts(hashtag_posts)
        result['hashtag'] = hashtag
        result['hashtag_posts'] = len(hashtag_posts)
        
        return result
    
    def compare_burst_patterns(self, posts_a: List[Dict], posts_b: List[Dict]) -> Dict[str, Any]:
        """Compare burst patterns between two sets of posts"""
        bursts_a = self.detect_bursts(posts_a)
        bursts_b = self.detect_bursts(posts_b)
        
        comparison = {
            'dataset_a': bursts_a,
            'dataset_b': bursts_b,
            'comparison_metrics': {}
        }
        
        # Compare burst counts
        comparison['comparison_metrics']['burst_count_diff'] = (
            len(bursts_a['kleinberg_bursts']) - len(bursts_b['kleinberg_bursts'])
        )
        
        # Compare average intensities
        intensity_a = np.mean([b['intensity'] for b in bursts_a['kleinberg_bursts']]) if bursts_a['kleinberg_bursts'] else 0
        intensity_b = np.mean([b['intensity'] for b in bursts_b['kleinberg_bursts']]) if bursts_b['kleinberg_bursts'] else 0
        
        comparison['comparison_metrics']['intensity_diff'] = intensity_a - intensity_b
        
        # Compare coordination scores
        coord_a = bursts_a['coordination_indicators']['coordination_score']
        coord_b = bursts_b['coordination_indicators']['coordination_score']
        
        comparison['comparison_metrics']['coordination_diff'] = coord_a - coord_b
        
        return comparison

def create_burst_detector() -> BurstDetector:
    """Factory function to create a burst detector instance"""
    return BurstDetector()

# Example usage
if __name__ == "__main__":
    detector = BurstDetector()
    
    # Generate sample time series data
    import random
    from datetime import datetime, timedelta
    
    base_time = datetime.now() - timedelta(days=2)
    sample_posts = []
    
    for i in range(100):
        # Create burst around hour 12 and 36
        if 10 <= i <= 15 or 34 <= i <= 39:
            count = random.randint(15, 25)  # Burst period
        else:
            count = random.randint(1, 5)    # Normal period
        
        for j in range(count):
            sample_posts.append({
                'posted_at': base_time + timedelta(hours=i, minutes=random.randint(0, 59)),
                'platform': 'twitter',
                'hashtags': ['#india', '#crisis'] if 10 <= i <= 15 else ['#india'],
                'author': {'username': f'user_{random.randint(1, 20)}'}
            })
    
    result = detector.detect_bursts(sample_posts)
    
    print("Burst Detection Results:")
    print(f"Total posts analyzed: {result['total_posts']}")
    print(f"Kleinberg bursts detected: {len(result['kleinberg_bursts'])}")
    print(f"Z-score anomalies: {len(result['zscore_anomalies'])}")
    print(f"Peak bursts: {len(result['peak_bursts'])}")
    print(f"Coordination suspected: {result['coordination_indicators']['suspected_coordination']}")
    print(f"Coordination score: {result['coordination_indicators']['coordination_score']:.2f}")
    
    for i, burst in enumerate(result['kleinberg_bursts']):
        print(f"\nBurst {i+1}:")
        print(f"  Start: {burst['start_time']}")
        print(f"  Duration: {burst['duration_hours']} hours")
        print(f"  Intensity: {burst['intensity']:.2f}")
        print(f"  Posts: {burst['total_posts']}")