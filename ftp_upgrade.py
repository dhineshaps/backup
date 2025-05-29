from fastapi import FastAPI, HTTPException, Depends
from ftplib import FTP, error_perm
from typing import Generator
import os

app = FastAPI()

# ✅ Environment-based config (or replace with constants)
FTP_HOST = os.getenv("ZOS_FTP_HOST", "your.zos.host")
FTP_USER = os.getenv("ZOS_FTP_USER", "your_user")
FTP_PASS = os.getenv("ZOS_FTP_PASS", "your_password")


# ✅ FTP connection as a FastAPI dependency
def ftp_connection() -> Generator[FTP, None, None]:
    ftp = FTP(FTP_HOST)
    ftp.login(FTP_USER, FTP_PASS)
    ftp.sendcmd("SITE FILETYPE=JES")
    ftp.sendcmd("SITE JESOWNER=*")
    try:
        yield ftp
    finally:
        ftp.quit()


# ✅ Get latest job ID for a job name
def find_latest_job_id(ftp: FTP, job_name: str) -> str | None:
    try:
        ftp.sendcmd(f"SITE JESJOBNAME={job_name}")
        jobs = []
        ftp.retrlines("LIST", jobs.append)
        job_ids = [line.split()[0] for line in jobs if job_name in line]
        job_ids.sort(reverse=True)
        return job_ids[0] if job_ids else None
    except error_perm as e:
        print(f"FTP LIST error: {e}")
        return None


# ✅ Download the job log and save to file
def download_job_log(ftp: FTP, job_id: str) -> str:
    lines = []
    ftp.retrlines(f"RETR {job_id}", lines.append)
    filename = f"{job_id}.txt"
    with open(filename, "w") as f:
        f.write("\n".join(lines))
    return filename


# ✅ FastAPI endpoint
@app.get("/joblog/")
def get_job_log(job_name: str, ftp: FTP = Depends(ftp_connection)):
    job_id = find_latest_job_id(ftp, job_name)
    if not job_id:
        raise HTTPException(status_code=404, detail=f"No job found with name {job_name}")
    try:
        filename = download_job_log(ftp, job_id)
        return {
            "status": "success",
            "job_id": job_id,
            "file_saved": filename
        }
    except error_perm as e:
        raise HTTPException(status_code=500, detail=f"FTP error: {str(e)}")
