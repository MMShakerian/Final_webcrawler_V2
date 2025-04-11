# Web Crawler with Tree Structure

این پروژه یک وب کراولر است که ساختار درختی وب‌سایت‌ها را استخراج می‌کند و گزارش‌های مفیدی از آن‌ها تهیه می‌کند.

## ویژگی‌های اصلی

- استخراج ساختار درختی وب‌سایت
- تشخیص لینک‌های داخلی و خارجی
- ذخیره‌سازی داده‌ها در MongoDB
- تولید گزارش‌های متنی و JSON
- مدیریت خودکار گزارش‌ها و دیتابیس‌ها
- نمایش آمار و اطلاعات مفید از فرآیند کراولینگ

## پیش‌نیازها

- Python 3.7+
- Scrapy
- MongoDB
- pymongo
- dnspython

## نصب

1. نصب پکیج‌های مورد نیاز:
```bash
pip install scrapy pymongo dnspython
```

2. نصب و راه‌اندازی MongoDB:
- [دانلود و نصب MongoDB](https://www.mongodb.com/try/download/community)
- اطمینان از اجرای سرویس MongoDB

## ساختار پروژه

```
mycrawler/
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
└── scrapy.cfg
```

## نحوه استفاده

1. اجرای کراولر:
```bash
scrapy crawl link_spider -a start_url=https://example.com
```

2. پارامترهای اختیاری:
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

## مثال خروجی

### گزارش متنی
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

1. اطمینان از اجرای MongoDB قبل از شروع کراولینگ
2. تنظیم محدودیت‌های مناسب برای جلوگیری از کراولینگ بیش از حد
3. بررسی گزارش‌ها و آمار برای بهینه‌سازی تنظیمات
4. استفاده از `index.json` برای دسترسی به گزارش‌های قبلی

## توسعه‌دهندگان

- [نام توسعه‌دهنده]

## مجوز

این پروژه تحت مجوز [نام مجوز] منتشر شده است. 