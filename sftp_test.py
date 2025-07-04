import paramiko
import os
import time
import datetime

hostname = 'your_mainframe_hostname'
port = 22
username = 'your_uss_username'
password = 'your_uss_password'
remote_dir = '/u/user/sftp_test'
test_dir = './small_test_files'
os.makedirs(test_dir, exist_ok=True)

# Create 10 small test files (1KB each)
for i in range(10):
    with open(f"{test_dir}/file_{i}.txt", "w", encoding="utf-8") as f:
        f.write(f"This is test file {i}\n" * 20)

ssh_client = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh_client.connect(hostname, port, username, password)
    sftp = ssh_client.open_sftp()

    print("🚀 Starting 10-minute traffic generation...")
    end_time = datetime.datetime.now() + datetime.timedelta(minutes=10)
    iteration = 0

    while datetime.datetime.now() < end_time:
        iteration += 1
        print(f"\n🔁 Iteration {iteration}")
        
        for file in os.listdir(test_dir):
            local_path = os.path.join(test_dir, file)
            remote_path = f"{remote_dir}/{file}"
            
            sftp.put(local_path, remote_path)
            print(f"  ✅ Uploaded: {file}")
            
            download_path = os.path.join(test_dir, f"dl_{file}")
            sftp.get(remote_path, download_path)
            print(f"  ⬇️ Downloaded: {file}")

        time.sleep(1)  # small pause to reduce CPU stress

    print("\n✅ Done: 10-minute traffic generation completed.")

except Exception as e:
    print(f"❌ Error: {e}")
finally:
    if 'sftp' in locals():
        sftp.close()
    ssh_client.close()
