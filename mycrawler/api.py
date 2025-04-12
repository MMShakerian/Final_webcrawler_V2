from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import json
import os
from datetime import datetime
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles

class CrawlRequest(BaseModel):
    url: str

app = FastAPI()

# تنظیم CORS برای اجازه دسترسی از افزونه کروم
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # اجازه دسترسی از همه منابع
    allow_credentials=True,
    allow_methods=["*"],  # اجازه همه متدها
    allow_headers=["*"],  # اجازه همه هدرها
)

# سرو کردن فایل‌های استاتیک
app.mount("/reports", StaticFiles(directory="reports"), name="reports")

@app.post("/start_crawl")
async def start_crawl(request: CrawlRequest):
    try:
        url = request.url
        # ایجاد نام منحصر به فرد برای گزارش
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        domain = url.split("//")[-1].split("/")[0].replace(".", "_")
        report_dir = f"reports/{domain}_{timestamp}"
        
        # اجرای اسپایدر
        process = subprocess.Popen(
            ["scrapy", "crawl", "link_spider", "-a", f"start_url={url}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # خواندن خروجی
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Error running spider: {stderr.decode()}")
        
        # خواندن گزارش
        report_path = os.path.join(report_dir, "report.txt")
        if os.path.exists(report_path):
            with open(report_path, "r", encoding="utf-8") as f:
                report_content = f.read()
        else:
            report_content = "No report generated"
        
        return {
            "status": "success",
            "report_dir": report_dir,
            "report": report_content
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 