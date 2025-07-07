#!/usr/bin/env python
"""
100x Engineer Analyzer Dashboard
This script initializes the backend ProductivityAgent and serves the UI dashboard.
"""

import os
import sys
import json
import asyncio
# Import custom JSON encoder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.utils import EngineerAnalyzerJSONEncoder
from datetime import datetime, timedelta
import http.server
import socketserver
import threading
import webbrowser
from urllib.parse import parse_qs, urlparse

# Add the parent directory to the path so we can import the ProductivityAgent
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create a mock ProductivityAgent class for testing
class MockProductivityAgent:
    """Mock implementation of ProductivityAgent for testing"""
    
    def __init__(self):
        """Initialize the mock agent"""
        self.config = type('Config', (), {'timezone': 'UTC', 'lookback_days': 7})
        print("Mock ProductivityAgent initialized successfully.")
    
    async def initialize(self):
        """Initialize the mock agent"""
        print("Mock ProductivityAgent initialized successfully.")
        return True
    
    async def run_productivity_analysis(self, start_date=None, end_date=None):
        """Run mock productivity analysis"""
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=7)
        
        print(f"Running mock productivity analysis for period: {start_date.date()} to {end_date.date()}")
        
        # Return mock data
        return {
            'timestamp': datetime.now().isoformat(),
            'period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            'scores': [
                {
                    'engineer': "Alice Smith",
                    'total_score': 92.5,
                    'github_score': 95.0,
                    'jira_score': 88.0,
                    'quality_score': 96.0,
                    'collaboration_score': 91.0,
                    'percentile_rank': 99.0,
                    'github_stats': {
                        'prs_created': 12,
                        'prs_reviewed': 18,
                        'commits_made': 45,
                        'lines_added': 1250,
                        'lines_deleted': 580
                    },
                    'jira_stats': {
                        'tickets_completed': 8,
                        'tickets_in_progress': 2,
                        'story_points': 35,
                        'avg_completion_time': "3.2 days"
                    }
                },
                {
                    'engineer': "Bob Johnson",
                    'total_score': 87.3,
                    'github_score': 82.0,
                    'jira_score': 91.0,
                    'quality_score': 89.0,
                    'collaboration_score': 87.0,
                    'percentile_rank': 92.0,
                    'github_stats': {
                        'prs_created': 8,
                        'prs_reviewed': 22,
                        'commits_made': 38,
                        'lines_added': 980,
                        'lines_deleted': 420
                    },
                    'jira_stats': {
                        'tickets_completed': 10,
                        'tickets_in_progress': 1,
                        'story_points': 42,
                        'avg_completion_time': "2.8 days"
                    }
                },
                {
                    'engineer': "Carol Davis",
                    'total_score': 85.1,
                    'github_score': 88.0,
                    'jira_score': 84.0,
                    'quality_score': 85.0,
                    'collaboration_score': 83.0,
                    'percentile_rank': 88.0,
                    'github_stats': {
                        'prs_created': 10,
                        'prs_reviewed': 15,
                        'commits_made': 42,
                        'lines_added': 1100,
                        'lines_deleted': 650
                    },
                    'jira_stats': {
                        'tickets_completed': 7,
                        'tickets_in_progress': 3,
                        'story_points': 32,
                        'avg_completion_time': "3.5 days"
                    }
                }
            ],
            'summary': {
                'executive_summary': "The team has shown strong performance during this period with an average score of 85.5. Alice Smith leads with exceptional GitHub contributions and code quality. Bob Johnson excels in Jira ticket completion. Overall collaboration is strong, with cross-team code reviews increasing by 15% compared to the previous period."
            },
            'github_data': {
                'total_prs': 43,
                'total_commits': 190,
                'total_reviews': 77
            },
            'jira_data': {
                'total_issues': 52,
                'completed_issues': 42
            }
        }
    
    async def cleanup(self):
        """Clean up resources"""
        print("Mock ProductivityAgent cleanup completed")

# Try to import the real ProductivityAgent, fall back to mock if it fails
try:
    from main import ProductivityAgent
    print("Successfully imported ProductivityAgent from main.py")
except ImportError:
    print("Warning: Could not import ProductivityAgent from main.py. Using mock implementation.")
    ProductivityAgent = MockProductivityAgent

# Configuration
PORT = 8081
DASHBOARD_DIR = os.path.dirname(os.path.abspath(__file__))

# Initialize the ProductivityAgent
productivity_agent = None
try:
    productivity_agent = ProductivityAgent()
    print("ProductivityAgent initialized successfully.")
except Exception as e:
    print(f"Error initializing ProductivityAgent: {e}")
    sys.exit(1)

# Initialize the agent asynchronously
async def initialize_agent():
    try:
        await productivity_agent.initialize()
        print("ProductivityAgent initialized successfully.")
        return True
    except Exception as e:
        print(f"Error during agent initialization: {e}")
        return False

# Run the initialization in the event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
initialization_success = loop.run_until_complete(initialize_agent())

if not initialization_success:
    print("Failed to initialize the ProductivityAgent. Exiting.")
    sys.exit(1)

class DashboardRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom request handler for serving the dashboard and handling API requests."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DASHBOARD_DIR, **kwargs)
    
    def do_GET(self):
        """Handle GET requests for static files."""
        return super().do_GET()
    
    def do_POST(self):
        """Handle POST requests for API endpoints."""
        if self.path.startswith('/api/productivity/analyze'):
            self._handle_analyze_request()
        else:
            self.send_error(404, "API endpoint not found")
    
    def _handle_analyze_request(self):
        """Handle requests to run productivity analysis."""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        try:
            request_data = json.loads(post_data)
            start_date_str = request_data.get('start_date')
            end_date_str = request_data.get('end_date')
            
            # Validate dates
            if not start_date_str or not end_date_str:
                self._send_json_response(400, {"error": "Missing start_date or end_date"})
                return
            
            # Parse dates
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
            except ValueError:
                self._send_json_response(400, {"error": "Invalid date format. Use YYYY-MM-DD"})
                return
            
            # Run analysis
            print(f"Running productivity analysis for period: {start_date.date()} to {end_date.date()}")
            
            try:
                # Run the analysis asynchronously
                async def run_analysis():
                    return await productivity_agent.run_productivity_analysis(start_date, end_date)
                
                # Execute the analysis in the event loop
                results = loop.run_until_complete(run_analysis())
                
                # Convert results to JSON-serializable format using custom encoder
                json_results = json.dumps(results, cls=EngineerAnalyzerJSONEncoder)
                json_data = json.loads(json_results)
                
                # Send the results
                self._send_json_response(200, json_data)
            except Exception as e:
                print(f"Error running analysis: {e}")
                self._send_json_response(500, {"error": f"Analysis failed: {str(e)}"})
        
        except json.JSONDecodeError:
            self._send_json_response(400, {"error": "Invalid JSON in request body"})
    
    def _send_json_response(self, status_code, data):
        """Send a JSON response with the given status code and data."""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')  # Allow CORS
        self.end_headers()
        
        # Ensure data is properly JSON serialized
        try:
            if not isinstance(data, str):
                response = json.dumps(data, default=str, cls=EngineerAnalyzerJSONEncoder)
            else:
                response = data
            self.wfile.write(response.encode('utf-8'))
        except Exception as e:
            print(f"Error serializing JSON response: {e}")
            error_response = json.dumps({"error": "Internal server error during JSON serialization"}, cls=EngineerAnalyzerJSONEncoder)
            self.wfile.write(error_response.encode('utf-8'))

def open_browser():
    """Open the web browser to the dashboard URL."""
    webbrowser.open(f'http://localhost:{PORT}')

def main():
    """Main function to start the server and open the browser."""
    import signal
    
    # Create the server
    httpd = socketserver.TCPServer(("", PORT), DashboardRequestHandler)
    
    # Define signal handler for graceful shutdown
    def signal_handler(sig, frame):
        print("\nShutting down server...")
        httpd.shutdown()
        httpd.server_close()
        print("Server stopped.")
        # Clean up the agent
        loop.run_until_complete(productivity_agent.cleanup())
        print("Resources cleaned up. Exiting.")
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
    
    # Start the server in a separate thread so signal handling works properly
    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.daemon = True  # So the thread will exit when the main thread exits
    
    try:
        print(f"Serving 100x Engineer Analyzer Dashboard at http://localhost:{PORT}")
        print("Press Ctrl+C to stop the server.")
        
        # Start the server thread
        server_thread.start()
        
        # Open browser after a short delay
        threading.Timer(1.0, open_browser).start()
        
        # Keep the main thread alive to handle signals
        while server_thread.is_alive():
            server_thread.join(1)  # Check every second if thread is still alive
            
    except Exception as e:
        print(f"\nError: {e}")
        httpd.shutdown()
        httpd.server_close()
        loop.run_until_complete(productivity_agent.cleanup())

if __name__ == "__main__":
    main()