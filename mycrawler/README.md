# Web Crawler with Tree Structure

این پروژه یک وب کراولر است که ساختار درختی وب‌سایت‌ها را استخراج می‌کند، گزارش‌های مفیدی از آن‌ها تهیه می‌کند و از طریق یک API و افزونه کروم قابل کنترل است.

## ویژگی‌های اصلی

- استخراج ساختار درختی وب‌سایت
- تشخیص لینک‌های داخلی و خارجی
- ذخیره‌سازی داده‌ها در MongoDB
- تولید گزارش‌های متنی و JSON
- مدیریت خودکار گزارش‌ها و دیتابیس‌ها
- نمایش آمار و اطلاعات مفید از فرآیند کراولینگ
- API برای کنترل کراولر و دریافت گزارش‌ها
- افزونه کروم برای مدیریت آسان کراولینگ

## پیش‌نیازها

- Python 3.7+
- Scrapy
- MongoDB
- pymongo
- dnspython
- FastAPI
- Uvicorn

## نصب

1. نصب پکیج‌های مورد نیاز:
```bash
pip install scrapy pymongo dnspython fastapi uvicorn
```

2. نصب و راه‌اندازی MongoDB:
- [دانلود و نصب MongoDB](https://www.mongodb.com/try/download/community)
- اطمینان از اجرای سرویس MongoDB

## ساختار پروژه

```
mycrawler/
├── chrome_extension/   # افزونه کروم
│   ├── js/
│   │   └── popup.js
│   ├── css/
│   │   └── popup.css
│   ├── icons/
│   │   └── icon16.png
│   ├── popup.html
│   └── manifest.json
├── mycrawler/
│   ├── spiders/
│   │   └── link_spider.py
│   ├── items.py
│   ├── middlewares.py
│   ├── pipelines.py
│   └── settings.py
├── reports/
│   ├── index.json
│   └── [domain]_[timestamp]/
│       ├── report.txt
│       └── tree.json
├── api.py              # سرور FastAPI
└── scrapy.cfg
```

## نحوه استفاده

### 1. راه‌اندازی API

در ریشه پروژه، دستور زیر را اجرا کنید:
```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

### 2. نصب و استفاده از افزونه کروم

1. مرورگر کروم را باز کنید و به `chrome://extensions/` بروید.
2. حالت توسعه‌دهنده (Developer mode) را فعال کنید.
3. روی دکمه `Load unpacked` کلیک کنید.
4. پوشه `chrome_extension` را انتخاب کنید.

حالا می‌توانید از آیکون افزونه در نوار ابزار کروم برای:
- وارد کردن URL و شروع کراولینگ
- مشاهده وضعیت کراولینگ
- مشاهده لیست گزارش‌های قبلی
- انتخاب و مشاهده جزئیات هر گزارش

### 3. اجرای مستقیم کراولر (اختیاری)

می‌توانید کراولر را مستقیماً از طریق خط فرمان نیز اجرا کنید:
```bash
scrapy crawl link_spider -a start_url=https://example.com
```

#### پارامترهای اختیاری (برای اجرای مستقیم):
- `-a start_url`: آدرس شروع کراولینگ
- `-a max_depth`: حداکثر عمق کراولینگ (پیش‌فرض: 3)
- `-a max_pages`: حداکثر تعداد صفحات (پیش‌فرض: 100)

## خروجی‌ها

### گزارش‌های متنی
- اطلاعات کلی کراولینگ
- آمار و ارقام
- ساختار درختی سایت
- صفحات خطا
- استثناهای اسپایدر

### گزارش‌های JSON
- ساختار درختی کامل
- اطلاعات آماری
- لینک‌های داخلی و خارجی

### MongoDB
- ذخیره‌سازی داده‌ها در دیتابیس منحصر به فرد برای هر اجرا
- نام دیتابیس: `webcrawler_[domain]_[timestamp]`
- دو کالکشن:
  - `pages`: اطلاعات صفحات
  - `tree_structure`: ساختار درختی

## مدیریت گزارش‌ها

- هر اجرای کراولر یک پوشه جدید در `reports` ایجاد می‌کند
- نام پوشه: `[domain]_[timestamp]`
- فایل `index.json` شامل اطلاعات تمام گزارش‌ها است
- گزارش‌ها بر اساس زمان مرتب می‌شوند (جدیدترین اول)

## مثال خروجی (افزونه کروم)

افزونه کروم اطلاعات زیر را برای هر گزارش نمایش می‌دهد:
- دامنه وب‌سایت
- تاریخ و زمان گزارش
- تعداد صفحات کراول شده
- تعداد لینک‌های داخلی و خارجی
- حداکثر عمق کراول
- زمان اجرای کراولینگ
- آمار کدهای وضعیت HTTP
- لیست صفحات خطا (در صورت وجود)

## مثال خروجی (گزارش متنی)
```
Web Crawler Report
=================

Timestamp: 2024-03-15T14:30:22
Base Domain: example.com
Database: webcrawler_example_com_20240315_143022
Total Pages Visited: 100
Internal Links: 200
External Links: 50

Crawl Statistics:
----------------
Total Requests: 300
Total Response Size: 1024.00 KB
Maximum Depth Reached: 3
...

Site Structure:
---------------
https://example.com
├── /about
│   ├── /team
│   └── /history
└── /products
    ├── /product1
    └── /product2
```

### ساختار درختی در MongoDB
```json
{
  "url": "https://example.com",
  "external": false,
  "children": [
    {
      "url": "/about",
      "external": false,
      "children": [
        {
          "url": "/team",
          "external": false,
          "children": []
        },
        {
          "url": "/history",
          "external": false,
          "children": []
        }
      ]
    },
    {
      "url": "https://external.com",
      "external": true,
      "children": []
    }
  ]
}
```

## نکات مهم

1. اطمینان از اجرای MongoDB قبل از شروع کراولینگ.
2. اطمینان از اجرای API (`uvicorn api:app ...`) قبل از استفاده از افزونه کروم.
3. تنظیم محدودیت‌های مناسب در `settings.py` (مانند `MAX_DEPTH`, `MAX_PAGES`) برای جلوگیری از کراولینگ بیش از حد.
4. بررسی گزارش‌ها و آمار برای بهینه‌سازی تنظیمات.
5. استفاده از افزونه کروم یا `index.json` برای دسترسی به گزارش‌های قبلی.

## توسعه‌دهندگان

- mm.shakerian
