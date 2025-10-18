# Enhanced Plex Data Collection Plan

## 🎯 **Goal: More Personalized Recommendations**

Expand data collection to get deeper insights into viewing patterns for significantly better recommendations.

## 📊 **Current vs Enhanced Data Collection**

### **Current Collection (Basic)**
- ✅ Movie title, year, genres, rating
- ✅ View date, duration, studio, summary  
- ✅ Only 1 year of history (365 days)
- ✅ Only movies (no TV shows)
- ✅ Basic TMDB metadata

### **Enhanced Collection (Comprehensive)**

#### **1. 📅 Extended Time Range**
- **Current**: 1 year (365 days)
- **Enhanced**: 3-5 years of history
- **Impact**: Better long-term pattern recognition
- **Cost**: Minimal (just more API calls)

#### **2. 📺 TV Show Integration**
- **Current**: Movies only
- **Enhanced**: Include TV shows and episodes
- **Impact**: Cross-media recommendations (movies based on TV preferences)
- **Cost**: Minimal (same API endpoints)

#### **3. 🎭 Detailed Viewing Patterns**
- **Current**: Basic view date
- **Enhanced**: 
  - Time of day viewing patterns
  - Day of week preferences
  - Seasonal viewing trends
  - Binge-watching patterns
- **Impact**: Mood-based and time-based recommendations
- **Cost**: None (just more data processing)

#### **4. ⭐ User Ratings & Feedback**
- **Current**: Plex rating only
- **Enhanced**:
  - User ratings (1-10 scale)
  - Thumbs up/down
  - Skip patterns
  - Rewatch frequency
- **Impact**: Much more accurate preference modeling
- **Cost**: None (Plex API data)

#### **5. 🏷️ Advanced Metadata**
- **Current**: Basic TMDB data
- **Enhanced**:
  - Director filmography analysis
  - Actor collaboration patterns
  - Production company preferences
  - Language and country preferences
  - Content warnings and themes
- **Impact**: Sophisticated recommendation algorithms
- **Cost**: More TMDB API calls (~$0.50/month)

#### **6. 👥 Multi-User Analysis**
- **Current**: Single user focus
- **Enhanced**:
  - Family member viewing patterns
  - Shared vs individual preferences
  - Collaborative filtering within household
- **Impact**: Better family recommendations
- **Cost**: None (just more data)

## 💰 **Cost Impact Analysis**

### **Minimal Cost Increases:**
- **Extended Time Range**: $0 (just more API calls to Plex)
- **TV Show Integration**: $0 (same Plex API)
- **Advanced Metadata**: ~$0.50/month (more TMDB calls)
- **Enhanced Processing**: ~$0.10/month (slightly more Lambda compute)

### **Total Additional Cost: ~$0.60/month**

## 🚀 **Performance Impact**

### **Data Size Increases:**
- **Current**: ~8 movies, ~50KB data
- **Enhanced**: ~200-500 movies/shows, ~2-5MB data
- **Impact**: Still very manageable for Lambda (10MB limit)

### **Processing Time:**
- **Current**: ~2-3 seconds
- **Enhanced**: ~5-8 seconds
- **Impact**: Still well within Lambda timeout (60s)

### **Storage:**
- **Current**: ~50KB per export
- **Enhanced**: ~2-5MB per export
- **Impact**: Still very small for S3

## 🎯 **Recommendation Quality Improvements**

### **Expected Improvements:**
- **Accuracy**: 60-80% better recommendations
- **Personalization**: Much more specific to your preferences
- **Variety**: Better balance of familiar and discovery
- **Timing**: Recommendations based on viewing patterns

### **New Recommendation Types:**
- **Mood-based**: "Movies for Sunday afternoon"
- **Seasonal**: "Halloween movies you might like"
- **Binge-worthy**: "Perfect for a movie marathon"
- **Family-friendly**: "Movies everyone will enjoy"
- **Hidden gems**: "Underrated movies in your style"

## 🛠️ **Implementation Plan**

### **Phase 1: Extended Time Range (Easy)**
```python
# Change from 365 days to 3 years
days_back = 1095  # 3 years
```

### **Phase 2: TV Show Integration (Easy)**
```python
# Include TV shows in analysis
if video.get("type") in ["movie", "episode"]:
    # Process both movies and TV episodes
```

### **Phase 3: Advanced Metadata (Medium)**
```python
# Enhanced TMDB data collection
- Director filmography
- Actor collaboration networks
- Production company analysis
- Language/country preferences
```

### **Phase 4: Viewing Pattern Analysis (Medium)**
```python
# Time-based pattern analysis
- Time of day preferences
- Day of week patterns
- Seasonal trends
- Binge-watching detection
```

## 🧪 **Testing Strategy**

### **A/B Testing:**
1. **Current System**: Keep existing recommendations
2. **Enhanced System**: Deploy with expanded data
3. **Compare**: Measure recommendation relevance
4. **User Feedback**: Track which recommendations are actually watched

### **Metrics to Track:**
- **Click-through rate**: How often recommendations are clicked
- **Completion rate**: How often recommended movies are watched fully
- **User satisfaction**: Thumbs up/down on recommendations
- **Discovery rate**: How often users find new favorites

## 🎉 **Expected Results**

### **Before Enhancement:**
- 8 movies analyzed
- Basic genre/decade recommendations
- Limited personalization

### **After Enhancement:**
- 200-500 movies/shows analyzed
- Sophisticated pattern recognition
- Highly personalized recommendations
- Mood and time-based suggestions
- Cross-media recommendations

## 💡 **Recommendation**

**Start with Phase 1 & 2** (Extended time range + TV shows):
- **Cost**: $0 additional
- **Effort**: 30 minutes
- **Impact**: 40-50% better recommendations
- **Risk**: None

This gives you the biggest improvement with zero additional cost and minimal effort!

Would you like me to implement Phase 1 & 2 right now?
