import pandas as pd
import numpy as np
import random
import os

OUTPUT_FILE = "activity_logs.csv"

def generate_logs(n_normal=1000, n_anom=50, output_path=OUTPUT_FILE):
    data = []
    
    # Generate Normal Data
    # Hour: 9am - 6pm (09-18)
    # Size: 1-50 MB
    for _ in range(n_normal):
        hour = int(np.random.normal(14, 2)) # mean 14 (2pm), std 2
        hour = max(9, min(18, hour))
        
        size_mb = max(1, int(np.random.lognormal(2, 0.5))) # ~7MB avg
        
        data.append({
            "hour": hour,
            "download_mb": size_mb,
            "failed_logins": np.random.poisson(0.1),
            "role_mismatch": 0,
            "label": 0 # Normal
        })

    # Generate Anomalies
    # Hour: Night time (22 - 05)
    # Size: 100-1000 MB
    for _ in range(n_anom):
        if random.random() > 0.5:
            hour = random.choice([22, 23, 0, 1, 2, 3, 4, 5]) 
        else:
            hour = random.randint(9, 18) # Normal time, but huge size

        size_mb = random.randint(100, 1000)
        
        data.append({
            "hour": hour,
            "download_mb": size_mb,
            "failed_logins": np.random.poisson(3),
            "role_mismatch": 1 if random.random() > 0.7 else 0,
            "label": 1 # Anomaly
        })
        
    df = pd.DataFrame(data)
    
    # Save to CSV
    # Ensure directory exists
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} logs to {output_path}")
    print(df.head())
    return output_path

if __name__ == "__main__":
    generate_logs(output_path=os.path.join(os.path.dirname(__file__), "../data/activity_logs.csv"))
