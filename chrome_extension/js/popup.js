document.addEventListener('DOMContentLoaded', function() {
  const urlInput = document.getElementById('url');
  const startButton = document.getElementById('start');
  const statusDiv = document.getElementById('status');
  const reportDiv = document.getElementById('report');
  const loadingSpinner = document.getElementById('loading');
  const totalReportsSpan = document.getElementById('totalReports');
  const lastUpdateSpan = document.getElementById('lastUpdate');
  const reportListDiv = document.getElementById('reportList');

  // تابع برای به‌روزرسانی لیست گزارش‌ها
  async function updateReportList() {
    try {
      // اضافه کردن پارامتر زمان برای جلوگیری از کش شدن
      const timestamp = Date.now();
      const response = await fetch(`http://localhost:8000/reports/index.json?t=${timestamp}`);
      if (response.ok) {
        const data = await response.json();
        totalReportsSpan.textContent = data.reports.length;
        if (data.reports.length > 0) {
          const latestReport = data.reports[0];
          lastUpdateSpan.textContent = new Date(latestReport.timestamp).toLocaleString('fa-IR');
          
          // پاک کردن لیست قبلی
          reportListDiv.innerHTML = '';
          
          // اضافه کردن گزارش‌ها به لیست
          data.reports.forEach((report, index) => {
            const reportItem = document.createElement('div');
            reportItem.className = 'report-item';
            reportItem.innerHTML = `
              <div class="d-flex justify-content-between align-items-center">
                <div>
                  <strong>${report.domain}</strong>
                  <div class="small text-muted">
                    ${new Date(report.timestamp).toLocaleString('fa-IR')}
                  </div>
                </div>
                <div class="text-muted small">
                  ${report.total_pages} صفحه
                </div>
              </div>
            `;
            
            // اضافه کردن رویداد کلیک
            reportItem.addEventListener('click', () => {
              // حذف کلاس active از همه آیتم‌ها
              document.querySelectorAll('.report-item').forEach(item => {
                item.classList.remove('active');
              });
              // اضافه کردن کلاس active به آیتم انتخاب شده
              reportItem.classList.add('active');
              // نمایش اطلاعات گزارش
              displayReport(report);
            });
            
            reportListDiv.appendChild(reportItem);
          });
        }
      }
    } catch (error) {
      console.error('Error fetching reports:', error);
    }
  }

  // تابع برای نمایش اطلاعات یک گزارش
  function displayReport(report) {
    // تابع کمکی برای فرمت کردن بایت‌ها
    function formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }

    let reportText = `گزارش کراولینگ:\n`;
    reportText += `=================\n\n`;
    reportText += `دامنه: ${report.domain}\n`;
    reportText += `آدرس شروع: ${report.start_url}\n`; 
    reportText += `زمان گزارش: ${new Date(report.timestamp).toLocaleString('fa-IR')}\n\n`; 
    
    reportText += `آمار صفحات:\n`;
    reportText += `------------\n`;
    reportText += `صفحات بازدید شده (داخلی): ${report.total_pages}\n`;
    reportText += `لینک‌های داخلی یافت شده: ${report.internal_links}\n`;
    reportText += `لینک‌های خارجی یافت شده: ${report.external_links}\n\n`;
    
    reportText += `آمار کلی کراولینگ:\n`;
    reportText += `-------------------\n`;
    reportText += `تعداد کل درخواست‌ها: ${report.total_requests}\n`;
    reportText += `حجم کل پاسخ‌ها: ${formatBytes(report.total_response_size)}\n`;
    reportText += `حداکثر عمق پیمایش: ${report.max_depth}\n`;
    reportText += `تعداد URLهای تکراری فیلتر شده: ${report.duplicate_urls}\n`;
    reportText += `زمان کل اجرا: ${report.elapsed_time.toFixed(2)} ثانیه\n\n`;
    
    reportText += `کدهای وضعیت HTTP:\n`;
    reportText += `------------------\n`;
    if (Object.keys(report.status_codes).length > 0) {
        for (const [code, count] of Object.entries(report.status_codes)) {
            reportText += `  - وضعیت ${code}: ${count} صفحه\n`;
        }
    } else {
        reportText += `  (موردی یافت نشد)\n`;
    }
    reportText += `\n`;
    
    reportText += `صفحات دارای خطا (>=400):\n`;
    reportText += `-------------------------\n`;
    if (report.error_pages && report.error_pages.length > 0) {
      report.error_pages.forEach(page => {
        reportText += `  - ${page.url} (کد: ${page.status})\n`;
      });
    } else {
        reportText += `  (موردی یافت نشد)\n`;
    }
    reportText += `\n`;

    reportText += `استثناهای اسپایدر:\n`;
    reportText += `------------------\n`;
    if (report.spider_exceptions && Object.keys(report.spider_exceptions).length > 0) {
        for (const [exc_type, count] of Object.entries(report.spider_exceptions)) {
            reportText += `  - ${exc_type}: ${count} مورد\n`;
        }
    } else {
        reportText += `  (موردی یافت نشد)\n`;
    }
    
    reportDiv.textContent = reportText;
  }

  // به‌روزرسانی اولیه لیست گزارش‌ها
  updateReportList();

  startButton.addEventListener('click', async function() {
    const url = urlInput.value.trim();
    if (!url) {
      statusDiv.textContent = 'لطفا یک URL وارد کنید';
      statusDiv.className = 'status-badge badge bg-danger';
      return;
    }

    try {
      statusDiv.textContent = 'در حال کراول کردن...';
      statusDiv.className = 'status-badge badge bg-primary';
      loadingSpinner.style.display = 'block';
      reportDiv.textContent = '';

      const response = await fetch('http://localhost:8000/start_crawl', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ url: url }),
      });

      if (!response.ok) {
        throw new Error(`خطای HTTP! وضعیت: ${response.status}`);
      }

      const data = await response.json();

      if (data.status === 'success') {
        statusDiv.textContent = 'کراولینگ با موفقیت انجام شد';
        statusDiv.className = 'status-badge badge bg-success';
        
        // به‌روزرسانی لیست گزارش‌ها
        await updateReportList();
      } else {
        throw new Error(data.detail || 'خطا در کراولینگ');
      }
    } catch (error) {
      statusDiv.textContent = `خطا: ${error.message}`;
      statusDiv.className = 'status-badge badge bg-danger';
      reportDiv.textContent = '';
      console.error('Error:', error);
    } finally {
      loadingSpinner.style.display = 'none';
    }
  });
});