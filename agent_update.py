import os
import random
from datetime import datetime

def run_test():
    print("Testing system WITHOUT API...")
    
    date_str = datetime.now().strftime("%B %d, %Y %H:%M:%S")
    random_id = random.randint(1000, 9999)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <body style="background:black;color:cyan;font-family:monospace;padding:50px;">
        <h1>SYSTEM TEST SUCCESSFUL</h1>
        <p>This update was made without an API Key to test permissions.</p>
        <p>TIME: {date_str}</p>
        <p>TEST_ID: {random_id}</p>
    </body>
    </html>
    """
    
    try:
        with open("index.html", "w") as f:
            f.write(html_content)
        print("Successfully wrote to index.html")
    except Exception as e:
        print(f"FAILED TO WRITE FILE: {e}")
        exit(1)

if __name__ == "__main__":
    run_test()
