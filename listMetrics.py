import sage_data_client
import pandas as pd

def listMetrics(vsn):
    print(f"Finding all available metrics for node {vsn} in the last 5 minutes...")
    try:
        # Querying without a 'name' filter to see all metrics for this node
        df = sage_data_client.query(
            start="-5m",
            filter={"vsn": vsn}
        )
        if df.empty:
            print(f"No data found for node {vsn} recently.")
        else:
            metrics = df['name'].unique()
            print(f"Available metrics for {vsn}:")
            for m in sorted(metrics):
                print(f"  - {m}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Using W077 which we saw was active in quickTest.py
    listMetrics("W077")
