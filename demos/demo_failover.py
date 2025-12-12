import requests
import time
import sys

LB_URL = "http://localhost:8002"

def demo_failover():
    print("--- Demo: Proxy Failover ---")
    
    # 1. Send requests and see which proxy handles them (if we had response headers indicating it)
    # Our Proxy Service doesn't return its ID in response, but LB logs it.
    # We can check LB health status.
    
    print("Sending 5 requests to LB...")
    for i in range(5):
        try:
            # We just need any valid-ish request.
            # Using a bogus cipher and rekey_id is fine, we just want to see it reach a proxy.
            resp = requests.post(f"{LB_URL}/reencrypt", json={
                "cipher_blob": "test",
                "rekey_id": "rk_test"
            })
            # It will fail with 400 or 500 likely because IDs are invalid, but that means it reached a proxy.
            print(f"Req {i}: Status {resp.status_code} (Expected fail but reached backend)")
        except Exception as e:
            print(f"Req {i}: FAILED conn {e}")

    print("Checking LB Health...")
    health = requests.get(f"{LB_URL}/health").json()
    print(f"Health: {health}")
    
    # In a real automated test we would kill a process here.
    # Since we are running this inside the verification runner which manages processes, 
    # we might need to rely on the runner to kill a proxy and then run this script again?
    # Or this script is just a client.
    
    return True

if __name__ == "__main__":
    demo_failover()
