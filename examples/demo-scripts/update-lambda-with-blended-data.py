#!/usr/bin/env python3
"""
Update Lambda function to use blended data from multiple Plex sources
"""

import json
import boto3
import glob
import os
from datetime import datetime

def find_latest_blended_data():
    """Find the most recent blended data file"""
    pattern = "blended-plex-data-*.json"
    files = glob.glob(pattern)
    
    if not files:
        print("❌ No blended data files found. Run enhanced-data-blender.py first.")
        return None
    
    # Get the most recent file
    latest_file = max(files, key=os.path.getctime)
    print(f"📊 Found latest blended data: {latest_file}")
    return latest_file

def upload_blended_data_to_s3(blended_file: str, s3_bucket: str):
    """Upload blended data to S3 for Lambda to access"""
    try:
        s3 = boto3.client('s3')
        
        # Upload the blended data
        s3_key = f"plex-recommendations/{blended_file}"
        s3.upload_file(blended_file, s3_bucket, s3_key)
        print(f"☁️ Uploaded blended data to S3: s3://{s3_bucket}/{s3_key}")
        
        # Also upload as the main data file for Lambda
        main_key = "plex-recommendations/current-plex-data.json"
        s3.upload_file(blended_file, s3_bucket, main_key)
        print(f"☁️ Uploaded as main data file: s3://{s3_bucket}/{main_key}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error uploading to S3: {e}")
        return False

def update_lambda_environment(s3_bucket: str):
    """Update Lambda environment variables to use blended data"""
    try:
        lambda_client = boto3.client('lambda')
        
        # Get current configuration
        response = lambda_client.get_function_configuration(FunctionName='plex-analyzer')
        current_env = response.get('Environment', {}).get('Variables', {})
        
        # Update environment variables
        updated_env = current_env.copy()
        updated_env.update({
            'S3_BUCKET': s3_bucket,
            'USE_BLENDED_DATA': 'true',
            'DATA_SOURCE': 'blended',
            'LAST_UPDATED': datetime.now().isoformat()
        })
        
        # Update Lambda configuration
        lambda_client.update_function_configuration(
            FunctionName='plex-analyzer',
            Environment={'Variables': updated_env}
        )
        
        print("✅ Lambda environment updated to use blended data")
        return True
        
    except Exception as e:
        print(f"❌ Error updating Lambda environment: {e}")
        return False

def test_lambda_with_blended_data():
    """Test the Lambda function with blended data"""
    try:
        lambda_client = boto3.client('lambda')
        
        print("🧪 Testing Lambda function with blended data...")
        response = lambda_client.invoke(
            FunctionName='plex-analyzer',
            Payload='{}'
        )
        
        # Read the response
        payload = json.loads(response['Payload'].read())
        
        if payload.get('statusCode') == 200:
            body = json.loads(payload.get('body', '{}'))
            summary = body.get('summary', {})
            
            print("✅ Lambda function test successful!")
            print(f"📊 Results:")
            print(f"   - Total movies: {summary.get('totalMovies', 0)}")
            print(f"   - Total recommendations: {summary.get('totalRecommendations', 0)}")
            print(f"   - ML recommendations: {summary.get('mlRecommendations', 0)}")
            
            return True
        else:
            print(f"❌ Lambda function test failed: {payload}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Lambda function: {e}")
        return False

def main():
    print("🔄 Updating Lambda with Enhanced Blended Data")
    print("=" * 50)
    
    s3_bucket = "plex-recommendations-c7c49ce4"
    
    # Find latest blended data
    blended_file = find_latest_blended_data()
    if not blended_file:
        return
    
    # Upload to S3
    if not upload_blended_data_to_s3(blended_file, s3_bucket):
        return
    
    # Update Lambda environment
    if not update_lambda_environment(s3_bucket):
        return
    
    # Test Lambda function
    if not test_lambda_with_blended_data():
        return
    
    print("\n🎉 Lambda function successfully updated with blended data!")
    print("🚀 Your recommendations should now be much more accurate and comprehensive.")
    print("🌍 Visit https://plex.robertconsulting.net to see the improved recommendations.")

if __name__ == "__main__":
    main()
