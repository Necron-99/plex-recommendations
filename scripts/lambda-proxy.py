#!/usr/bin/env python3
"""
Simple proxy script to call Lambda function and serve recommendations
"""

import json
import boto3
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

# AWS Configuration
AWS_REGION = "us-east-1"
LAMBDA_FUNCTION_NAME = "plex-analyzer"

class LambdaProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.handle_request()
    
    def do_POST(self):
        self.handle_request()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def handle_request(self):
        try:
            print(f"Handling request: {self.command} {self.path}")
            
            # Initialize Lambda client
            lambda_client = boto3.client('lambda', region_name=AWS_REGION)
            
            # Call Lambda function
            response = lambda_client.invoke(
                FunctionName=LAMBDA_FUNCTION_NAME,
                InvocationType='RequestResponse',
                Payload=json.dumps({})
            )
            
            # Parse response
            payload = json.loads(response['Payload'].read())
            print(f"Lambda response: {payload}")
            
            # Send response
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            self.wfile.write(json.dumps(payload).encode())
            
        except Exception as e:
            print(f"Error in proxy: {e}")
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            error_response = {
                "error": "Failed to get recommendations",
                "message": str(e)
            }
            self.wfile.write(json.dumps(error_response).encode())

def run_proxy(port=8080):
    server = HTTPServer(('localhost', port), LambdaProxyHandler)
    print(f"🚀 Lambda proxy running on http://localhost:{port}")
    print("📡 This will call your Lambda function directly")
    print("🌐 Open your website and update the URL to use this proxy")
    server.serve_forever()

if __name__ == "__main__":
    run_proxy()
