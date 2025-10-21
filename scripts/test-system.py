#!/usr/bin/env python3
"""
System Testing and Validation Script
Tests the current Plex recommendations system and validates TMDB integration
"""

import requests
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

class SystemTester:
    def __init__(self):
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "overall_status": "unknown"
        }
    
    def test_tmdb_api_connection(self) -> Dict[str, Any]:
        """Test TMDB API connection and rate limits"""
        print("🔍 Testing TMDB API connection...")
        
        # Test with a known movie (The Matrix)
        test_url = "https://api.themoviedb.org/3/movie/603"
        test_params = {"api_key": "YOUR_TMDB_API_KEY_HERE"}
        
        try:
            response = requests.get(test_url, params=test_params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "success",
                    "message": "TMDB API connection successful",
                    "movie_title": data.get("title", "Unknown"),
                    "response_time": response.elapsed.total_seconds(),
                    "rate_limit_remaining": response.headers.get("X-RateLimit-Remaining", "Unknown")
                }
            elif response.status_code == 401:
                return {
                    "status": "error",
                    "message": "TMDB API key invalid or missing",
                    "suggestion": "Get API key from https://www.themoviedb.org/settings/api"
                }
            else:
                return {
                    "status": "error",
                    "message": f"TMDB API error: {response.status_code}",
                    "response": response.text[:200]
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": f"Network error connecting to TMDB: {str(e)}",
                "suggestion": "Check internet connection and TMDB API status"
            }
    
    def test_plex_connection(self, plex_server: str, plex_token: str) -> Dict[str, Any]:
        """Test Plex server connection"""
        print("🔍 Testing Plex server connection...")
        
        if plex_server == "your-plex-server:32400" or plex_token == "your_plex_token_here":
            return {
                "status": "error",
                "message": "Plex configuration not set up",
                "suggestion": "Update PLEX_SERVER and PLEX_TOKEN in configuration files"
            }
        
        try:
            url = f"http://{plex_server}/status/sessions"
            headers = {"X-Plex-Token": plex_token}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return {
                    "status": "success",
                    "message": "Plex server connection successful",
                    "response_time": response.elapsed.total_seconds()
                }
            elif response.status_code == 401:
                return {
                    "status": "error",
                    "message": "Plex token invalid",
                    "suggestion": "Get valid token from https://support.plex.tv/articles/204059436/"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Plex server error: {response.status_code}",
                    "response": response.text[:200]
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": f"Network error connecting to Plex: {str(e)}",
                "suggestion": "Check Plex server URL and network connectivity"
            }
    
    def test_aws_s3_connection(self, s3_bucket: str) -> Dict[str, Any]:
        """Test AWS S3 connection"""
        print("🔍 Testing AWS S3 connection...")
        
        if s3_bucket == "your-s3-bucket-name":
            return {
                "status": "error",
                "message": "S3 bucket not configured",
                "suggestion": "Update S3_BUCKET in configuration files"
            }
        
        try:
            import boto3
            from botocore.exceptions import ClientError, NoCredentialsError
            
            s3_client = boto3.client('s3')
            
            # Test bucket access
            response = s3_client.head_bucket(Bucket=s3_bucket)
            
            return {
                "status": "success",
                "message": "S3 bucket access successful",
                "bucket_name": s3_bucket,
                "region": response.get('ResponseMetadata', {}).get('HTTPHeaders', {}).get('x-amz-bucket-region', 'Unknown')
            }
            
        except NoCredentialsError:
            return {
                "status": "error",
                "message": "AWS credentials not configured",
                "suggestion": "Run 'aws configure' or set up AWS credentials"
            }
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucket':
                return {
                    "status": "error",
                    "message": f"S3 bucket '{s3_bucket}' does not exist",
                    "suggestion": "Create the bucket or update S3_BUCKET configuration"
                }
            else:
                return {
                    "status": "error",
                    "message": f"S3 error: {error_code}",
                    "details": str(e)
                }
        except ImportError:
            return {
                "status": "error",
                "message": "boto3 not installed",
                "suggestion": "Install boto3: pip install boto3"
            }
    
    def test_lambda_function(self, lambda_url: str) -> Dict[str, Any]:
        """Test deployed Lambda function"""
        print("🔍 Testing Lambda function...")
        
        if not lambda_url or lambda_url == "your-lambda-url":
            return {
                "status": "error",
                "message": "Lambda function not deployed",
                "suggestion": "Deploy Lambda function using deploy-plex-analyzer.sh"
            }
        
        try:
            response = requests.get(lambda_url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "success",
                    "message": "Lambda function responding",
                    "response_time": response.elapsed.total_seconds(),
                    "has_recommendations": "recommendations" in data,
                    "phase2_enhancements": data.get("phase2Enhancements", {}),
                    "cached": data.get("cached", False)
                }
            else:
                return {
                    "status": "error",
                    "message": f"Lambda function error: {response.status_code}",
                    "response": response.text[:200]
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": f"Network error connecting to Lambda: {str(e)}",
                "suggestion": "Check Lambda function URL and deployment status"
            }
    
    def test_data_export_process(self) -> Dict[str, Any]:
        """Test the data export process"""
        print("🔍 Testing data export process...")
        
        try:
            # Check if the exporter script exists and is executable
            exporter_path = "scripts/plex-data-exporter.py"
            if not os.path.exists(exporter_path):
                return {
                    "status": "error",
                    "message": "Data exporter script not found",
                    "suggestion": "Ensure scripts/plex-data-exporter.py exists"
                }
            
            # Check if required dependencies are installed
            required_packages = ["requests", "boto3", "xml.etree.ElementTree"]
            missing_packages = []
            
            for package in required_packages:
                try:
                    if package == "xml.etree.ElementTree":
                        import xml.etree.ElementTree
                    else:
                        __import__(package)
                except ImportError:
                    missing_packages.append(package)
            
            if missing_packages:
                return {
                    "status": "error",
                    "message": f"Missing required packages: {', '.join(missing_packages)}",
                    "suggestion": f"Install missing packages: pip install {' '.join(missing_packages)}"
                }
            
            return {
                "status": "success",
                "message": "Data export process ready",
                "exporter_script": exporter_path,
                "dependencies": "All required packages available"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error testing data export: {str(e)}",
                "suggestion": "Check script permissions and dependencies"
            }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all system tests"""
        print("🧪 Running comprehensive system tests...")
        print("=" * 60)
        
        # Test TMDB API
        self.test_results["tests"]["tmdb_api"] = self.test_tmdb_api_connection()
        
        # Test Plex connection (with placeholder values for now)
        self.test_results["tests"]["plex_server"] = self.test_plex_connection(
            "your-plex-server:32400", "your_plex_token_here"
        )
        
        # Test S3 connection (with placeholder values for now)
        self.test_results["tests"]["aws_s3"] = self.test_aws_s3_connection("your-s3-bucket-name")
        
        # Test Lambda function (with placeholder URL)
        self.test_results["tests"]["lambda_function"] = self.test_lambda_function("")
        
        # Test data export process
        self.test_results["tests"]["data_export"] = self.test_data_export_process()
        
        # Determine overall status
        all_tests = self.test_results["tests"]
        success_count = sum(1 for test in all_tests.values() if test["status"] == "success")
        total_tests = len(all_tests)
        
        if success_count == total_tests:
            self.test_results["overall_status"] = "all_passing"
        elif success_count > 0:
            self.test_results["overall_status"] = "partial"
        else:
            self.test_results["overall_status"] = "failing"
        
        return self.test_results
    
    def print_test_results(self):
        """Print formatted test results"""
        print("\n" + "=" * 60)
        print("🧪 SYSTEM TEST RESULTS")
        print("=" * 60)
        
        for test_name, result in self.test_results["tests"].items():
            status_icon = "✅" if result["status"] == "success" else "❌"
            print(f"\n{status_icon} {test_name.upper().replace('_', ' ')}")
            print(f"   Status: {result['status']}")
            print(f"   Message: {result['message']}")
            
            if "suggestion" in result:
                print(f"   💡 Suggestion: {result['suggestion']}")
            
            if result["status"] == "success" and "response_time" in result:
                print(f"   ⏱️  Response Time: {result['response_time']:.2f}s")
        
        print(f"\n🎯 OVERALL STATUS: {self.test_results['overall_status'].upper()}")
        
        # Print next steps based on results
        print("\n📋 NEXT STEPS:")
        if self.test_results["overall_status"] == "all_passing":
            print("   🎉 All tests passing! System is ready for use.")
        elif self.test_results["overall_status"] == "partial":
            print("   ⚠️  Some tests failing. Fix configuration issues first.")
        else:
            print("   🚨 System needs configuration. Follow setup guide in SETUP.md")
        
        print(f"\n📊 Test completed at: {self.test_results['timestamp']}")

def main():
    print("🎬 Plex Recommendations System Tester")
    print("=" * 60)
    
    tester = SystemTester()
    results = tester.run_all_tests()
    tester.print_test_results()
    
    # Save results to file
    with open("test-results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Test results saved to: test-results.json")
    
    return 0 if results["overall_status"] in ["all_passing", "partial"] else 1

if __name__ == "__main__":
    sys.exit(main())
