import sage_data_client
import pandas as pd

def quickTest():
    print("Testing connectivity with a simple query (sys.uptime)...")
    try:
        # sys.uptime is generally very reliable
        df = sage_data_client.query(
            start="-5m",
            filter={"name": "sys.uptime"}
        )
        if df.empty:
            print("Query succeeded but returned no data.")
        else:
            print(f"Success! Found {len(df)} uptime records.")
            print(df.tail(3))
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    quickTest()
