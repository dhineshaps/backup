from ftplib import FTP

# Replace with your values or use os.getenv()
HOST = "your.mainframe.host"
USER = "your_user"
PASSWORD = "your_password"
JOB_ID = "JOB12345"  # Replace with the job ID you want to fetch

try:
    # Connect and log in
    ftp = FTP(HOST)
    ftp.login(USER, PASSWORD)

    # Switch to JES mode
    ftp.sendcmd("SITE FILETYPE=JES")
    ftp.sendcmd("SITE JESOWNER=*")  # Optional, needed for cross-user access

    # List jobs to verify job visibility
    jobs = []
    ftp.retrlines("LIST", jobs.append)
    print("Jobs in JES spool:")
    for job in jobs:
        print(job)

    # Check if JOB_ID is present
    if not any(JOB_ID in job for job in jobs):
        print(f"\n❌ Job {JOB_ID} not found in spool.")
    else:
        print(f"\n✅ Job {JOB_ID} found. Attempting to retrieve log...")

        output_file = f"{JOB_ID}.txt"
        lines_written = 0

        with open(output_file, "w") as f:
            def handle_line(line):
                nonlocal lines_written
                lines_written += 1
                f.write(line + "\n")

            ftp.retrlines(f"RETR {JOB_ID}", callback=handle_line)

        if lines_written == 0:
            print(f"⚠️ Job {JOB_ID} retrieved, but log was empty.")
        else:
            print(f"✅ Job log saved to {output_file} ({lines_written} lines).")

    ftp.quit()

except Exception as e:
    print(f"\n🔥 Error: {e}")
