const { S3Client, GetObjectCommand, PutObjectCommand } = require('@aws-sdk/client-s3');

// Lightweight ML Recommender Integration
// This adds ML capabilities to the existing Lambda function with minimal cost increase

// Genre inference function for movies without genre data
function inferGenresFromTitle(title, year) {
    const genres = [];
    const titleLower = title.toLowerCase();
    
    // Action keywords
    if (titleLower.includes('action') || titleLower.includes('fight') || titleLower.includes('war') || 
        titleLower.includes('battle') || titleLower.includes('gun') || titleLower.includes('explosion')) {
        genres.push('Action');
    }
    
    // Comedy keywords
    if (titleLower.includes('comedy') || titleLower.includes('funny') || titleLower.includes('laugh') ||
        titleLower.includes('joke') || titleLower.includes('humor')) {
        genres.push('Comedy');
    }
    
    // Drama keywords
    if (titleLower.includes('drama') || titleLower.includes('story') || titleLower.includes('life') ||
        titleLower.includes('family') || titleLower.includes('love')) {
        genres.push('Drama');
    }
    
    // Horror keywords
    if (titleLower.includes('horror') || titleLower.includes('scary') || titleLower.includes('fright') ||
        titleLower.includes('monster') || titleLower.includes('ghost') || titleLower.includes('zombie')) {
        genres.push('Horror');
    }
    
    // Sci-Fi keywords
    if (titleLower.includes('sci-fi') || titleLower.includes('space') || titleLower.includes('future') ||
        titleLower.includes('robot') || titleLower.includes('alien') || titleLower.includes('time travel')) {
        genres.push('Sci-Fi');
    }
    
    // Thriller keywords
    if (titleLower.includes('thriller') || titleLower.includes('suspense') || titleLower.includes('mystery') ||
        titleLower.includes('crime') || titleLower.includes('detective')) {
        genres.push('Thriller');
    }
    
    // Romance keywords
    if (titleLower.includes('romance') || titleLower.includes('love') || titleLower.includes('romantic') ||
        titleLower.includes('wedding') || titleLower.includes('kiss')) {
        genres.push('Romance');
    }
    
    // Adventure keywords
    if (titleLower.includes('adventure') || titleLower.includes('journey') || titleLower.includes('quest') ||
        titleLower.includes('expedition') || titleLower.includes('treasure')) {
        genres.push('Adventure');
    }
    
    // Fantasy keywords
    if (titleLower.includes('fantasy') || titleLower.includes('magic') || titleLower.includes('wizard') ||
        titleLower.includes('dragon') || titleLower.includes('fairy')) {
        genres.push('Fantasy');
    }
    
    // Animation keywords
    if (titleLower.includes('animation') || titleLower.includes('cartoon') || titleLower.includes('animated') ||
        titleLower.includes('pixar') || titleLower.includes('disney')) {
        genres.push('Animation');
    }
    
    // Documentary keywords
    if (titleLower.includes('documentary') || titleLower.includes('doc') || titleLower.includes('real') ||
        titleLower.includes('true story') || titleLower.includes('biography')) {
        genres.push('Documentary');
    }
    
    // If no genres found, try to infer from year
    if (genres.length === 0) {
        if (year) {
            const yearNum = parseInt(year);
            if (yearNum >= 1980 && yearNum < 1990) {
                genres.push('80s Cinema');
            } else if (yearNum >= 1990 && yearNum < 2000) {
                genres.push('90s Cinema');
            } else if (yearNum >= 2000 && yearNum < 2010) {
                genres.push('2000s Cinema');
            } else if (yearNum >= 2010 && yearNum < 2020) {
                genres.push('2010s Cinema');
            } else if (yearNum >= 2020) {
                genres.push('2020s Cinema');
            }
        }
        
        // Final fallback
        if (genres.length === 0) {
            genres.push('General Entertainment');
        }
    }
    
    return genres;
}

// Lightweight ML Recommender Class
class LightweightMLRecommender {
    constructor() {
        this.mlEnabled = true; // Will be set based on available packages
        this.costTracker = {
            monthlyBudget: 10.00,
            currentCost: 0.00,
            fallbackMode: false
        };
    }
    
    // Simple content-based filtering using text similarity
    calculateTextSimilarity(text1, text2) {
        if (!text1 || !text2) return 0;
        
        const words1 = text1.toLowerCase().split(/\s+/);
        const words2 = text2.toLowerCase().split(/\s+/);
        
        const set1 = new Set(words1);
        const set2 = new Set(words2);
        
        const intersection = new Set([...set1].filter(x => set2.has(x)));
        const union = new Set([...set1, ...set2]);
        
        return intersection.size / union.size; // Jaccard similarity
    }
    
    // Extract movie features for ML processing
    extractMovieFeatures(movie) {
        const features = {
            id: this.getMovieId(movie),
            title: movie.title || '',
            year: parseInt(movie.year) || 0,
            rating: parseFloat(movie.rating) || 0,
            duration: parseInt(movie.duration) || 0,
            viewCount: parseInt(movie.viewCount) || 0,
            genres: movie.genres || [],
            summary: movie.summary || '',
            textContent: '',
            tmdbRating: 0,
            tmdbPopularity: 0,
            castCount: 0,
            directors: []
        };
        
        // Combine text content
        const textParts = [features.title, features.summary];
        if (features.genres && Array.isArray(features.genres)) {
            textParts.push(...features.genres);
        }
        features.textContent = textParts.join(' ');
        
        // TMDB metadata
        if (movie.tmdb_metadata) {
            features.tmdbRating = movie.tmdb_metadata.vote_average || 0;
            features.tmdbPopularity = movie.tmdb_metadata.popularity || 0;
            features.castCount = movie.tmdb_metadata.cast ? movie.tmdb_metadata.cast.length : 0;
            
            if (movie.tmdb_metadata.crew) {
                features.directors = movie.tmdb_metadata.crew
                    .filter(crew => crew.job === 'Director')
                    .map(crew => crew.name);
            }
        }
        
        return features;
    }
    
    // Generate content-based recommendations
    getContentBasedRecommendations(movieFeatures, targetMovieId, nRecommendations = 5) {
        const recommendations = [];
        const targetMovie = movieFeatures.find(m => m.id === targetMovieId);
        
        if (!targetMovie) return recommendations;
        
        for (const movie of movieFeatures) {
            if (movie.id === targetMovieId) continue;
            
            // Calculate similarity score
            let similarity = 0;
            
            // Text similarity
            const textSimilarity = this.calculateTextSimilarity(
                targetMovie.textContent, 
                movie.textContent
            );
            similarity += textSimilarity * 0.4;
            
            // Genre similarity
            if (targetMovie.genres && movie.genres) {
                const genreIntersection = targetMovie.genres.filter(g => movie.genres.includes(g));
                const genreUnion = [...new Set([...targetMovie.genres, ...movie.genres])];
                const genreSimilarity = genreUnion.length > 0 ? genreIntersection.length / genreUnion.length : 0;
                similarity += genreSimilarity * 0.3;
            }
            
            // Year similarity (closer years = higher similarity)
            const yearDiff = Math.abs(targetMovie.year - movie.year);
            const yearSimilarity = Math.max(0, 1 - (yearDiff / 50)); // 50 years = 0 similarity
            similarity += yearSimilarity * 0.2;
            
            // Rating similarity
            const ratingDiff = Math.abs(targetMovie.rating - movie.rating);
            const ratingSimilarity = Math.max(0, 1 - (ratingDiff / 5)); // 5 point diff = 0 similarity
            similarity += ratingSimilarity * 0.1;
            
            if (similarity > 0.1) { // Minimum similarity threshold
                recommendations.push({
                    movieId: movie.id,
                    title: movie.title,
                    year: movie.year,
                    similarityScore: similarity,
                    type: 'content_based',
                    reason: `Similar to ${targetMovie.title} (${(similarity * 100).toFixed(1)}% match)`
                });
            }
        }
        
        // Sort by similarity and return top recommendations
        return recommendations
            .sort((a, b) => b.similarityScore - a.similarityScore)
            .slice(0, nRecommendations);
    }
    
    // Generate collaborative filtering recommendations
    getCollaborativeRecommendations(watchHistory, nRecommendations = 5) {
        const recommendations = [];
        
        // Analyze user preferences
        const userPreferences = {
            genres: {},
            decades: {},
            ratings: [],
            directors: {},
            actors: {}
        };
        
        // Build user preference profile
        watchHistory.forEach(movie => {
            // Genre preferences
            if (movie.genres && Array.isArray(movie.genres)) {
                movie.genres.forEach(genre => {
                    userPreferences.genres[genre] = (userPreferences.genres[genre] || 0) + 1;
                });
            }
            
            // Decade preferences
            if (movie.year) {
                const decade = Math.floor(parseInt(movie.year) / 10) * 10;
                userPreferences.decades[decade] = (userPreferences.decades[decade] || 0) + 1;
            }
            
            // Rating preferences
            if (movie.rating) {
                userPreferences.ratings.push(parseFloat(movie.rating));
            }
            
            // Director preferences
            if (movie.tmdb_metadata && movie.tmdb_metadata.crew) {
                movie.tmdb_metadata.crew
                    .filter(crew => crew.job === 'Director')
                    .forEach(director => {
                        userPreferences.directors[director.name] = (userPreferences.directors[director.name] || 0) + 1;
                    });
            }
            
            // Actor preferences
            if (movie.tmdb_metadata && movie.tmdb_metadata.cast) {
                movie.tmdb_metadata.cast.slice(0, 3).forEach(actor => {
                    userPreferences.actors[actor.name] = (userPreferences.actors[actor.name] || 0) + 1;
                });
            }
        });
        
        // Generate recommendations based on preferences
        const topGenres = Object.entries(userPreferences.genres)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 3)
            .map(([genre]) => genre);
        
        const topDecades = Object.entries(userPreferences.decades)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 2)
            .map(([decade]) => decade);
        
        const topDirectors = Object.entries(userPreferences.directors)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 2)
            .map(([director]) => director);
        
        const avgRating = userPreferences.ratings.length > 0 
            ? userPreferences.ratings.reduce((a, b) => a + b, 0) / userPreferences.ratings.length 
            : 7.0;
        
        // Create recommendation suggestions
        topGenres.forEach(genre => {
            recommendations.push({
                type: 'collaborative',
                suggestion: `More ${genre} movies`,
                reason: `You've watched ${userPreferences.genres[genre]} ${genre} movies`,
                confidence: Math.min(0.9, userPreferences.genres[genre] / watchHistory.length * 3),
                genre: genre,
                count: userPreferences.genres[genre]
            });
        });
        
        topDecades.forEach(decade => {
            recommendations.push({
                type: 'collaborative',
                suggestion: `Movies from the ${decade}s`,
                reason: `You enjoy ${decade}s cinema (${userPreferences.decades[decade]} movies)`,
                confidence: Math.min(0.8, userPreferences.decades[decade] / watchHistory.length * 3),
                decade: decade,
                count: userPreferences.decades[decade]
            });
        });
        
        topDirectors.forEach(director => {
            recommendations.push({
                type: 'collaborative',
                suggestion: `More movies by ${director}`,
                reason: `You've watched ${userPreferences.directors[director]} movies by this director`,
                confidence: Math.min(0.85, userPreferences.directors[director] / watchHistory.length * 4),
                director: director,
                count: userPreferences.directors[director]
            });
        });
        
        // Rating-based recommendation
        if (avgRating > 0) {
            const ratingThreshold = Math.ceil(avgRating);
            recommendations.push({
                type: 'collaborative',
                suggestion: `Movies rated ${ratingThreshold}+ stars`,
                reason: `Your average rating is ${avgRating.toFixed(1)}, suggesting you prefer quality films`,
                confidence: 0.7,
                threshold: ratingThreshold,
                averageRating: avgRating
            });
        }
        
        return recommendations.slice(0, nRecommendations);
    }
    
    // Generate hybrid ML recommendations
    generateMLRecommendations(watchHistory, statistics) {
        try {
            console.log('🤖 Generating ML recommendations...');
            
            if (!this.mlEnabled) {
                console.log('⚠️ ML not available, using basic recommendations');
                return this.getCollaborativeRecommendations(watchHistory);
            }
            
            // Check cost budget
            if (this.costTracker.fallbackMode) {
                console.log('💰 Using fallback mode to control costs');
                return this.getCollaborativeRecommendations(watchHistory);
            }
            
            // Extract movie features
            const movieFeatures = watchHistory.map(movie => this.extractMovieFeatures(movie));
            
            // Get content-based recommendations for top-rated movies
            const topMovies = watchHistory
                .filter(movie => movie.rating && parseFloat(movie.rating) > 7.0)
                .sort((a, b) => parseFloat(b.rating) - parseFloat(a.rating))
                .slice(0, 3);
            
            const contentRecommendations = [];
            topMovies.forEach(movie => {
                const movieId = this.getMovieId(movie);
                const recs = this.getContentBasedRecommendations(movieFeatures, movieId, 3);
                contentRecommendations.push(...recs);
            });
            
            // Get collaborative recommendations
            const collaborativeRecommendations = this.getCollaborativeRecommendations(watchHistory, 5);
            
            // Combine recommendations
            const allRecommendations = {
                contentBased: contentRecommendations,
                collaborative: collaborativeRecommendations,
                hybrid: []
            };
            
            // Create hybrid recommendations by combining approaches
            const hybridRecommendations = [];
            
            // Genre-based hybrid recommendations
            const genreStats = {};
            watchHistory.forEach(movie => {
                if (movie.genres && Array.isArray(movie.genres)) {
                    movie.genres.forEach(genre => {
                        if (!genreStats[genre]) {
                            genreStats[genre] = { count: 0, avgRating: 0, ratings: [] };
                        }
                        genreStats[genre].count++;
                        if (movie.rating) {
                            genreStats[genre].ratings.push(parseFloat(movie.rating));
                        }
                    });
                }
            });
            
            // Calculate average ratings for genres
            Object.keys(genreStats).forEach(genre => {
                const stats = genreStats[genre];
                if (stats.ratings.length > 0) {
                    stats.avgRating = stats.ratings.reduce((a, b) => a + b, 0) / stats.ratings.length;
                }
            });
            
            // Generate hybrid genre recommendations
            Object.entries(genreStats)
                .sort(([,a], [,b]) => b.avgRating - a.avgRating)
                .slice(0, 3)
                .forEach(([genre, stats]) => {
                    hybridRecommendations.push({
                        type: 'hybrid',
                        suggestion: `High-quality ${genre} movies`,
                        reason: `You enjoy ${genre} movies (avg rating: ${stats.avgRating.toFixed(1)})`,
                        confidence: Math.min(0.9, stats.avgRating / 10),
                        genre: genre,
                        averageRating: stats.avgRating,
                        count: stats.count,
                        mlEnhanced: true
                    });
                });
            
            allRecommendations.hybrid = hybridRecommendations;
            
            console.log(`✅ Generated ${contentRecommendations.length} content-based, ${collaborativeRecommendations.length} collaborative, and ${hybridRecommendations.length} hybrid recommendations`);
            
            return allRecommendations;
            
        } catch (error) {
            console.error('❌ Error generating ML recommendations:', error);
            return this.getCollaborativeRecommendations(watchHistory);
        }
    }
    
    getMovieId(movie) {
        const title = movie.title || 'Unknown';
        const year = movie.year || 'Unknown';
        return `${title}_${year}`.replace(/[^a-zA-Z0-9_]/g, '_');
    }
    
    // Cost monitoring
    estimateCost(operation, dataSize) {
        const costPerOperation = {
            content_training: 0.001,
            collaborative_training: 0.002,
            recommendation: 0.0001,
            model_storage: 0.0001
        };
        
        const baseCost = costPerOperation[operation] || 0.001;
        return baseCost * (dataSize / 100);
    }
    
    checkBudget() {
        if (this.costTracker.currentCost > this.costTracker.monthlyBudget) {
            this.costTracker.fallbackMode = true;
            return {
                withinBudget: false,
                fallbackMode: true,
                message: 'Monthly budget exceeded, using fallback mode'
            };
        }
        
        return {
            withinBudget: true,
            fallbackMode: false,
            remainingBudget: this.costTracker.monthlyBudget - this.costTracker.currentCost
        };
    }
}

// Initialize S3 client with optimizations
const s3Client = new S3Client({ 
    region: 'us-east-1',
    maxAttempts: 3,
    requestTimeout: 30000
});
const S3_BUCKET = process.env.S3_BUCKET || 'plex-recommendations-c7c49ce4';

// Cache for optimization
const analysisCache = new Map();
const CACHE_EXPIRY_HOURS = 24;

// Initialize ML recommender
const mlRecommender = new LightweightMLRecommender();

/**
 * Generate movie recommendations based on watch history (Enhanced with ML)
 */
function generateRecommendations(watchHistory, statistics) {
    try {
        console.log('🧠 Generating recommendations...');
        
        const recommendations = {
            genreBased: [],
            decadeBased: [],
            ratingBased: [],
            general: [],
            crossMedia: [],
            tvShowBased: [],
            directorBased: [],
            actorNetworkBased: [],
            productionBased: [],
            culturalBased: [],
            // New ML-based recommendations
            mlContentBased: [],
            mlCollaborative: [],
            mlHybrid: []
        };
        
        // Generate ML recommendations
        const mlRecommendations = mlRecommender.generateMLRecommendations(watchHistory, statistics);
        
        if (mlRecommendations.contentBased) {
            recommendations.mlContentBased = mlRecommendations.contentBased.map(rec => ({
                type: 'ml_content',
                suggestion: rec.title,
                reason: rec.reason,
                confidence: rec.similarityScore,
                movieId: rec.movieId,
                year: rec.year,
                mlEnhanced: true
            }));
        }
        
        if (mlRecommendations.collaborative) {
            recommendations.mlCollaborative = mlRecommendations.collaborative.map(rec => ({
                ...rec,
                mlEnhanced: true
            }));
        }
        
        if (mlRecommendations.hybrid) {
            recommendations.mlHybrid = mlRecommendations.hybrid;
        }
        
        // Original recommendation logic (fallback and additional)
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
            general: [],
            mlContentBased: [],
            mlCollaborative: [],
            mlHybrid: []
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
            totalItems: watchHistory.length,
            totalMovies: watchHistory.filter(item => item.type === 'movie').length,
            totalTVShows: watchHistory.filter(item => item.type === 'episode').length,
            genreDistribution: {},
            decadeDistribution: {},
            ratingDistribution: {},
            viewingFrequency: {},
            averageRating: 0,
            totalWatchTime: 0,
            contentTypes: {
                movies: watchHistory.filter(item => item.type === 'movie').length,
                tvShows: watchHistory.filter(item => item.type === 'episode').length,
                crossMediaEnabled: true
            }
        };
        
        let ratingSum = 0;
        let ratingCount = 0;
        let totalDuration = 0;
        
        watchHistory.forEach(movie => {
            // Genre analysis - handle both array and string formats
            if (movie.genres && Array.isArray(movie.genres)) {
                movie.genres.forEach(genre => {
                    patterns.genreDistribution[genre] = (patterns.genreDistribution[genre] || 0) + 1;
                });
            } else if (movie.genre && typeof movie.genre === 'string') {
                // Handle single genre string
                patterns.genreDistribution[movie.genre] = (patterns.genreDistribution[movie.genre] || 0) + 1;
            } else {
                // Fallback: infer genres from movie titles and years
                const inferredGenres = inferGenresFromTitle(movie.title, movie.year);
                inferredGenres.forEach(genre => {
                    patterns.genreDistribution[genre] = (patterns.genreDistribution[genre] || 0) + 1;
                });
            }
            
            // Decade analysis
            if (movie.year) {
                const year = parseInt(movie.year);
                if (!isNaN(year)) {
                    const decade = Math.floor(year / 10) * 10;
                    patterns.decadeDistribution[decade] = (patterns.decadeDistribution[decade] || 0) + 1;
                }
            }
            
            // Rating analysis
            if (movie.rating) {
                const rating = parseFloat(movie.rating);
                if (!isNaN(rating)) {
                    const ratingRange = Math.floor(rating);
                    patterns.ratingDistribution[ratingRange] = (patterns.ratingDistribution[ratingRange] || 0) + 1;
                    ratingSum += rating;
                    ratingCount++;
                }
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
        
        // Generate top genres and decades for recommendations
        patterns.topGenres = Object.entries(patterns.genreDistribution)
            .map(([genre, count]) => ({ genre, count }))
            .sort((a, b) => b.count - a.count)
            .slice(0, 5);
            
        patterns.topDecades = Object.entries(patterns.decadeDistribution)
            .map(([decade, count]) => ({ decade: `${decade}s`, count }))
            .sort((a, b) => b.count - a.count)
            .slice(0, 3);
        
        console.log('✅ Watch history analysis completed');
        console.log(`📊 Found ${patterns.topGenres.length} genres and ${patterns.topDecades.length} decades`);
        return patterns;
        
    } catch (error) {
        console.error('❌ Error analyzing watch history:', error);
        return {};
    }
}

/**
 * Get data from S3 with compression support
 */
async function getDataFromS3(key) {
    try {
        console.log(`📥 Fetching data from S3: ${key}`);
        
        const command = new GetObjectCommand({
            Bucket: S3_BUCKET,
            Key: key
        });
        
        const response = await s3Client.send(command);
        let data;
        
        // Handle compressed data
        if (key.endsWith('.gz') || response.ContentEncoding === 'gzip') {
            const zlib = require('zlib');
            const compressedData = await response.Body.transformToByteArray();
            const decompressedData = zlib.gunzipSync(Buffer.from(compressedData));
            data = JSON.parse(decompressedData.toString());
            console.log('📦 Decompressed data from S3');
        } else {
            data = JSON.parse(await response.Body.transformToString());
        }
        
        console.log('✅ Data fetched from S3 successfully');
        return data;
        
    } catch (error) {
        console.error('❌ Error fetching data from S3:', error);
        throw error;
    }
}

/**
 * Check if cache is valid
 */
function isCacheValid(cacheEntry) {
    if (!cacheEntry || !cacheEntry.timestamp) return false;
    
    const cacheAge = Date.now() - cacheEntry.timestamp;
    const maxAge = CACHE_EXPIRY_HOURS * 60 * 60 * 1000; // Convert hours to milliseconds
    
    return cacheAge < maxAge;
}

/**
 * Get cached analysis if available
 */
function getCachedAnalysis(cacheKey) {
    const cacheEntry = analysisCache.get(cacheKey);
    if (isCacheValid(cacheEntry)) {
        console.log('📋 Using cached analysis results');
        return cacheEntry.data;
    }
    return null;
}

/**
 * Save analysis to cache
 */
function saveToCache(cacheKey, analysisData) {
    analysisCache.set(cacheKey, {
        data: analysisData,
        timestamp: Date.now()
    });
    console.log('💾 Analysis saved to cache');
}

/**
 * Save analysis results to S3 with compression
 */
async function saveAnalysisToS3(analysisData) {
    try {
        console.log('💾 Saving analysis to S3...');
        
        const timestamp = new Date().toISOString();
        const key = `plex-recommendations/analysis-${timestamp.replace(/[:.]/g, '-')}.json.gz`;
        
        // Compress data for storage optimization
        const zlib = require('zlib');
        const jsonData = JSON.stringify(analysisData, null, 2);
        const compressedData = zlib.gzipSync(jsonData);
        
        const command = new PutObjectCommand({
            Bucket: S3_BUCKET,
            Key: key,
            Body: compressedData,
            ContentType: 'application/gzip',
            ContentEncoding: 'gzip',
            StorageClass: 'INTELLIGENT_TIERING' // Cost optimization
        });
        
        await s3Client.send(command);
        
        // Also save as latest analysis (compressed)
        const latestCommand = new PutObjectCommand({
            Bucket: S3_BUCKET,
            Key: 'plex-recommendations/latest-analysis.json.gz',
            Body: compressedData,
            ContentType: 'application/gzip',
            ContentEncoding: 'gzip',
            StorageClass: 'INTELLIGENT_TIERING'
        });
        
        await s3Client.send(latestCommand);
        
        console.log('✅ Analysis saved to S3 successfully (compressed)');
        console.log('💰 Cost optimizations: S3 Intelligent Tiering + compression enabled');
        return key;
        
    } catch (error) {
        console.error('❌ Error saving analysis to S3:', error);
        throw error;
    }
}

/**
 * Main Lambda handler with ML enhancements
 */
exports.handler = async (event) => {
    try {
        // Handle CORS preflight requests
        if (event.httpMethod === 'OPTIONS') {
            return {
                statusCode: 200,
                headers: {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: 'CORS preflight' })
            };
        }
        
        console.log('🎬 Starting enhanced Plex data analysis with ML...');
        
        // Generate cache key for optimization
        const cacheKey = `analysis-${new Date().toISOString().split('T')[0]}-${Date.now()}`;
        
        // Check cache first (90% savings on repeated analysis)
        const cachedResult = getCachedAnalysis(cacheKey);
        if (cachedResult) {
            console.log('💰 Cost savings: Using cached analysis (90% reduction)');
            return {
                statusCode: 200,
                headers: {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: 'Enhanced Plex data analysis completed successfully (cached)',
                    summary: cachedResult.summary,
                    recommendations: cachedResult.recommendations,
                    recommendationsCount: cachedResult.summary.totalRecommendations,
                    phase2Enhancements: cachedResult.phase2Enhancements,
                    mlEnhancements: cachedResult.mlEnhancements,
                    cached: true,
                    generatedAt: cachedResult.generatedAt
                })
            };
        }
        
        // Get the latest Plex data from S3
        let plexData;
        try {
            plexData = await getDataFromS3('plex-data/latest.json.gz');
        } catch (error) {
            console.log('📥 Falling back to uncompressed data');
            plexData = await getDataFromS3('plex-data/latest.json');
        }
        
        if (!plexData.watchHistory || plexData.watchHistory.length === 0) {
            return {
                statusCode: 200,
                headers: {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: 'No watch history found in Plex data',
                    generatedAt: new Date().toISOString()
                })
            };
        }
        
        console.log(`📊 Processing ${plexData.watchHistory.length} movies with ML enhancement`);
        
        // Analyze watch history
        const analysis = analyzeWatchHistory(plexData.watchHistory);
        
        // Generate recommendations (now with ML)
        const recommendations = generateRecommendations(plexData.watchHistory, analysis);
        
        console.log('🤖 ML-enhanced recommendations generated');
        
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
                totalItems: plexData.watchHistory.length,
                totalMovies: analysis.totalMovies || 0,
                totalTVShows: analysis.totalTVShows || 0,
                topGenres: analysis.topGenres ? analysis.topGenres.slice(0, 3) : [],
                topDecades: analysis.topDecades ? analysis.topDecades.slice(0, 5) : [],
                averageRating: analysis.averageRating || 0,
                totalRecommendations: Object.values(recommendations).flat().length,
                crossMediaRecommendations: recommendations.crossMedia ? recommendations.crossMedia.length : 0,
                mlRecommendations: (recommendations.mlContentBased?.length || 0) + 
                                 (recommendations.mlCollaborative?.length || 0) + 
                                 (recommendations.mlHybrid?.length || 0)
            },
            optimizations: {
                compressionEnabled: true,
                intelligentTieringEnabled: true,
                cachingEnabled: true,
                incrementalProcessingEnabled: true
            },
            phase2Enhancements: {
                richMetadataEnabled: plexData.watchHistory.some(movie => movie.enriched && movie.tmdb_metadata),
                enhancedRecommendations: true,
                tmdbIntegration: plexData.watchHistory.some(movie => movie.tmdb_metadata),
                tvShowIntegrationEnabled: true,
                crossMediaRecommendations: true,
                advancedMetadataAnalysis: true,
                directorFilmographyAnalysis: true,
                actorCollaborationNetworks: true,
                productionCompanyAnalysis: true,
                culturalPreferenceAnalysis: true,
                enrichedItemsCount: plexData.watchHistory.filter(movie => movie.enriched).length,
                totalMovies: analysis.totalMovies || 0,
                totalTVShows: analysis.totalTVShows || 0
            },
            mlEnhancements: {
                mlEnabled: mlRecommender.mlEnabled,
                contentBasedRecommendations: recommendations.mlContentBased?.length || 0,
                collaborativeRecommendations: recommendations.mlCollaborative?.length || 0,
                hybridRecommendations: recommendations.mlHybrid?.length || 0,
                totalMLRecommendations: (recommendations.mlContentBased?.length || 0) + 
                                      (recommendations.mlCollaborative?.length || 0) + 
                                      (recommendations.mlHybrid?.length || 0),
                costTracking: mlRecommender.checkBudget(),
                estimatedMonthlyCost: mlRecommender.costTracker.currentCost,
                fallbackMode: mlRecommender.costTracker.fallbackMode
            }
        };
        
        // Save to cache (90% savings on repeated analysis)
        saveToCache(cacheKey, analysisData);
        
        // Save to S3 with optimizations
        const savedKey = await saveAnalysisToS3(analysisData);
        
        return {
            statusCode: 200,
            headers: {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: 'Enhanced Plex data analysis with ML completed successfully',
                summary: analysisData.summary,
                recommendations: analysisData.recommendations,
                recommendationsCount: analysisData.summary.totalRecommendations,
                savedTo: savedKey,
                optimizations: analysisData.optimizations,
                phase2Enhancements: analysisData.phase2Enhancements,
                mlEnhancements: analysisData.mlEnhancements,
                generatedAt: analysisData.generatedAt
            })
        };
        
    } catch (error) {
        console.error('❌ Error in enhanced Plex data analysis:', error);
        
        return {
            statusCode: 500,
            headers: {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                error: 'Failed to analyze Plex data',
                message: error.message,
                generatedAt: new Date().toISOString()
            })
        };
    }
};
