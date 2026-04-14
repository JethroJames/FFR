"""
Test client for Teacher Model API
"""

import os
import requests
import json
import time
from typing import Dict, Any

# Server configuration
SERVER_URL = "http://localhost:8000"

def test_health_check():
    """Test health check endpoint"""
    try:
        response = requests.get(f"{SERVER_URL}/health")
        if response.status_code == 200:
            print("✓ Health check passed")
            print(f"  Response: {response.json()}")
            return True
        else:
            print(f"✗ Health check failed with status {response.status_code}")
            return False
    except requests.ConnectionError:
        print("✗ Cannot connect to server. Is it running?")
        return False
    except Exception as e:
        print(f"✗ Health check error: {e}")
        return False

def test_analysis_endpoint():
    """Test analysis endpoint with sample data"""
    
    # Load test data
    try:
        with open("test.json", "r") as f:
            test_samples = json.load(f)
        
        if not test_samples:
            print("✗ No test samples found")
            return False
            
        sample = test_samples[0]
        
        # Prepare request
        request_data = {
            "problem_id": sample["problem_id"],
            "question": sample["question"],
            "video_path": os.path.join(os.getenv("VIDEO_DATA_PATH", ""), sample['video_path']),
            "student_response": sample["model_rollout_result"],
            "student_score": sample["model_rollout_score"],
            "ground_truth": sample["standard_answer"],
            "incorrect_only": True,
            "nframes": 8
        }
        
        print("\n✓ Sending analysis request...")
        print(f"  Problem ID: {request_data['problem_id']}")
        print(f"  Question: {request_data['question'][:100]}...")
        print(f"  Video: {request_data['video_path'].split('/')[-1]}")
        
        start_time = time.time()
        response = requests.post(
            f"{SERVER_URL}/analyze",
            json=request_data,
            timeout=60  # Client timeout slightly higher than server timeout
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✓ Analysis completed in {elapsed:.2f} seconds")
            
            if result["success"]:
                print("  Status: SUCCESS")
                print(f"  Problem ID: {result.get('problem_id', 'N/A')}")
                if result.get("data"):
                    data = result["data"]
                    print(f"  Error Classification: {data.get('error_classification', 'N/A')}")
                    print(f"  Parse Success: {data.get('parse_success', False)}")
                    if data.get('metadata'):
                        print(f"  Model Used: {data['metadata'].get('model_used', 'N/A')}")
            else:
                print(f"  Status: FAILED")
                print(f"  Error: {result.get('error', 'Unknown error')}")
                
            return result["success"]
        else:
            print(f"\n✗ Request failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
    except requests.Timeout:
        print("\n✗ Request timeout (exceeded 60 seconds)")
        return False
    except requests.ConnectionError:
        print("\n✗ Cannot connect to server")
        return False
    except FileNotFoundError:
        print("✗ test.json file not found")
        return False
    except Exception as e:
        print(f"\n✗ Test error: {e}")
        return False

def test_timeout_behavior():
    """Test timeout behavior with a simulated long request"""
    print("\n--- Testing Timeout Behavior ---")
    print("Note: This test will intentionally wait for timeout...")
    
    # Create a request that might timeout
    request_data = {
        "problem_id": "test_timeout_001",
        "question": "Test timeout question",
        "video_path": "/path/to/nonexistent/video.mp4",  # This might cause delays
        "student_response": "Test response",
        "student_score": 0.0,
        "ground_truth": "Test answer",
        "incorrect_only": False,
        "nframes": 32  # Higher frame count might take longer
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{SERVER_URL}/analyze",
            json=request_data,
            timeout=60
        )
        elapsed = time.time() - start_time
        
        result = response.json()
        if not result["success"] and "timeout" in result.get("error", "").lower():
            print(f"✓ Timeout handling works correctly (after {elapsed:.2f}s)")
            print(f"  Error message: {result['error']}")
        else:
            print(f"Response received in {elapsed:.2f}s")
            
    except Exception as e:
        print(f"✗ Timeout test error: {e}")

def main():
    """Run all tests"""
    print("=" * 50)
    print("Teacher Model API Test Client")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n--- Test 1: Health Check ---")
    health_ok = test_health_check()
    
    if not health_ok:
        print("\n⚠ Server is not running. Please start it with:")
        print("  uvicorn server:app --host 0.0.0.0 --port 8000")
        return
    
    # Test 2: Analysis endpoint
    print("\n--- Test 2: Analysis Endpoint ---")
    analysis_ok = test_analysis_endpoint()
    
    # Test 3: Timeout behavior (optional)
    # Uncomment to test timeout behavior
    # test_timeout_behavior()
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    print(f"  Health Check: {'✓ PASS' if health_ok else '✗ FAIL'}")
    print(f"  Analysis Test: {'✓ PASS' if analysis_ok else '✗ FAIL'}")
    print("=" * 50)

if __name__ == "__main__":
    main()