const { S3Client, GetObjectCommand, PutObjectCommand } = require('@aws-sdk/client-s3');

// Initialize S3 client
const s3Client = new S3Client({ region: 'us-east-1' });
const S3_BUCKET = 'robert-consulting-cache';

/**
 * Generate movie recommendations based on watch history
 */
function generateRecommendations(watchHistory, statistics) {
    try {
        console.log('🧠 Generating recommendations...');
        
        const recommendations = {
            genreBased: [],
            decadeBased: [],
            ratingBased: [],
            general: []
        };
        
        // Genre-based recommendations
        if (statistics.topGenres && statistics.topGenres.length > 0) {
            statistics.topGenres.forEach(genreData => {
                recommendations.genreBased.push({
                    type: 'genre',
                    suggestion: `More ${genreData.genre} movies`,
                    reason: `You've watched ${genreData.count} ${genreData.genre} movies`,
                    confidence: Math.min(0.9, genreData.count / statistics.totalMovies * 2),
                    genre: genreData.genre,
                    count: genreData.count
                });
            });
        }
        
        // Decade-based recommendations
        if (statistics.topDecades && statistics.topDecades.length > 0) {
            statistics.topDecades.forEach(decadeData => {
                recommendations.decadeBased.push({
                    type: 'decade',
                    suggestion: `Movies from the ${decadeData.decade}s`,
                    reason: `You enjoy ${decadeData.decade}s cinema (${decadeData.count} movies)`,
                    confidence: Math.min(0.8, decadeData.count / statistics.totalMovies * 3),
                    decade: decadeData.decade,
                    count: decadeData.count
                });
            });
        }
        
        // Rating-based recommendations
        if (statistics.averageRating > 0) {
            const ratingThreshold = Math.ceil(statistics.averageRating);
            recommendations.ratingBased.push({
                type: 'rating',
                suggestion: `Movies rated ${ratingThreshold}+ stars`,
                reason: `Your average rating is ${statistics.averageRating}, suggesting you prefer quality films`,
                confidence: 0.7,
                threshold: ratingThreshold,
                averageRating: statistics.averageRating
            });
        }
        
        // General recommendations
        recommendations.general = [
            {
                type: 'general',
                suggestion: 'Explore similar movies to your favorites',
                reason: 'Based on your viewing patterns',
                confidence: 0.6
            },
            {
                type: 'general',
                suggestion: 'Try movies from your preferred decades',
                reason: 'You seem to enjoy certain time periods',
                confidence: 0.5
            },
            {
                type: 'general',
                suggestion: 'Check out highly-rated films in your favorite genres',
                reason: 'Combine your genre preferences with quality ratings',
                confidence: 0.8
            }
        ];
        
        console.log('✅ Generated recommendations successfully');
        return recommendations;
        
    } catch (error) {
        console.error('❌ Error generating recommendations:', error);
        return {
            genreBased: [],
            decadeBased: [],
            ratingBased: [],
            general: []
        };
    }
}

/**
 * Analyze watch history for patterns
 */
function analyzeWatchHistory(watchHistory) {
    try {
        console.log('📊 Analyzing watch history patterns...');
        
        if (!watchHistory || watchHistory.length === 0) {
            return {};
        }
        
        // Analyze viewing patterns
        const patterns = {
            totalMovies: watchHistory.length,
            genreDistribution: {},
            decadeDistribution: {},
            ratingDistribution: {},
            viewingFrequency: {},
            averageRating: 0,
            totalWatchTime: 0
        };
        
        let ratingSum = 0;
        let ratingCount = 0;
        let totalDuration = 0;
        
        watchHistory.forEach(movie => {
            // Genre analysis
            movie.genres.forEach(genre => {
                patterns.genreDistribution[genre] = (patterns.genreDistribution[genre] || 0) + 1;
            });
            
            // Decade analysis
            if (movie.year) {
                const decade = Math.floor(movie.year / 10) * 10;
                patterns.decadeDistribution[decade] = (patterns.decadeDistribution[decade] || 0) + 1;
            }
            
            // Rating analysis
            if (movie.rating) {
                const ratingRange = Math.floor(movie.rating);
                patterns.ratingDistribution[ratingRange] = (patterns.ratingDistribution[ratingRange] || 0) + 1;
                ratingSum += movie.rating;
                ratingCount++;
            }
            
            // Duration analysis
            if (movie.duration) {
                totalDuration += movie.duration;
            }
            
            // Viewing frequency (by month)
            if (movie.viewedAt) {
                const date = new Date(movie.viewedAt);
                const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
                patterns.viewingFrequency[monthKey] = (patterns.viewingFrequency[monthKey] || 0) + 1;
            }
        });
        
        patterns.averageRating = ratingCount > 0 ? ratingSum / ratingCount : 0;
        patterns.totalWatchTime = totalDuration; // in minutes
        
        console.log('✅ Watch history analysis completed');
        return patterns;
        
    } catch (error) {
        console.error('❌ Error analyzing watch history:', error);
        return {};
    }
}

/**
 * Get data from S3
 */
async function getDataFromS3(key) {
    try {
        console.log(`📥 Fetching data from S3: ${key}`);
        
        const command = new GetObjectCommand({
            Bucket: S3_BUCKET,
            Key: key
        });
        
        const response = await s3Client.send(command);
        const data = JSON.parse(await response.Body.transformToString());
        
        console.log('✅ Data fetched from S3 successfully');
        return data;
        
    } catch (error) {
        console.error('❌ Error fetching data from S3:', error);
        throw error;
    }
}

/**
 * Save analysis results to S3
 */
async function saveAnalysisToS3(analysisData) {
    try {
        console.log('💾 Saving analysis to S3...');
        
        const timestamp = new Date().toISOString();
        const key = `plex-recommendations/analysis-${timestamp.replace(/[:.]/g, '-')}.json`;
        
        const command = new PutObjectCommand({
            Bucket: S3_BUCKET,
            Key: key,
            Body: JSON.stringify(analysisData, null, 2),
            ContentType: 'application/json'
        });
        
        await s3Client.send(command);
        
        // Also save as latest analysis
        const latestCommand = new PutObjectCommand({
            Bucket: S3_BUCKET,
            Key: 'plex-recommendations/latest-analysis.json',
            Body: JSON.stringify(analysisData, null, 2),
            ContentType: 'application/json'
        });
        
        await s3Client.send(latestCommand);
        
        console.log('✅ Analysis saved to S3 successfully');
        return key;
        
    } catch (error) {
        console.error('❌ Error saving analysis to S3:', error);
        throw error;
    }
}

/**
 * Main Lambda handler
 */
exports.handler = async (event) => {
    try {
        console.log('🎬 Starting Plex data analysis...');
        
        // Get the latest Plex data from S3
        const plexData = await getDataFromS3('plex-data/latest.json');
        
        if (!plexData.watchHistory || plexData.watchHistory.length === 0) {
            return {
                statusCode: 200,
                body: JSON.stringify({
                    message: 'No watch history found in Plex data',
                    generatedAt: new Date().toISOString()
                })
            };
        }
        
        console.log(`📊 Processing ${plexData.watchHistory.length} movies`);
        
        // Analyze watch history
        const analysis = analyzeWatchHistory(plexData.watchHistory);
        
        // Generate recommendations
        const recommendations = generateRecommendations(plexData.watchHistory, plexData.statistics);
        
        // Prepare analysis data
        const analysisData = {
            generatedAt: new Date().toISOString(),
            sourceData: {
                exportedAt: plexData.exportedAt,
                totalMovies: plexData.watchHistory.length,
                dateRange: plexData.statistics.dateRange
            },
            analysis: analysis,
            recommendations: recommendations,
            summary: {
                totalMovies: plexData.watchHistory.length,
                topGenres: plexData.statistics.topGenres.slice(0, 3),
                topDecades: plexData.statistics.topDecades.slice(0, 2),
                averageRating: plexData.statistics.averageRating,
                totalRecommendations: Object.values(recommendations).flat().length
            }
        };
        
        // Save to S3
        const savedKey = await saveAnalysisToS3(analysisData);
        
        return {
            statusCode: 200,
            body: JSON.stringify({
                message: 'Plex data analysis completed successfully',
                summary: analysisData.summary,
                recommendationsCount: analysisData.summary.totalRecommendations,
                savedTo: savedKey,
                generatedAt: analysisData.generatedAt
            })
        };
        
    } catch (error) {
        console.error('❌ Error in Plex data analysis:', error);
        
        return {
            statusCode: 500,
            body: JSON.stringify({
                error: 'Failed to analyze Plex data',
                message: error.message,
                generatedAt: new Date().toISOString()
            })
        };
    }
};
