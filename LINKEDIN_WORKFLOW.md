# راهنمای کامل گردش کار LinkedIn با تایید انسانی

## 🎯 هدف پروژه
سیستم به صورت **خودکار** پست‌های LinkedIn تولید می‌کند، اما **هیچ پستی بدون تایید شما منتشر نمی‌شود**.

---

## 📋 گردش کار هفتگی

### دوشنبه: تولید ایده (Idea)
- Agent موضوعات ترند را تحقیق می‌کند
- یک موضوع برای پست این هفته انتخاب می‌کند
- وضعیت: `idea`
- **هیچ محتوایی تولید نمی‌شود**

### چهارشنبه: تولید پیش‌نویس (Draft)
- Agent بر اساس موضوع انتخابی، محتوای کامل پست را می‌نویسد
- وضعیت به `pending_approval` تغییر می‌کند
- **منتظر تایید شما می‌ماند**

### پنجشنبه/جمعه: بازبینی و تایید (Approval)
- شما پیش‌نویس را در API بررسی می‌کنید
- اگر نیاز به ویرایش داشت، محتوا را اصلاح می‌کنید
- دکمه تایید را می‌زنید
- وضعیت به `approved` تغییر می‌کند

### انتشار خودکار (Publishing)
- پس از تایید، پست به LinkedIn ارسال می‌شود
- وضعیت به `published` تغییر می‌کند
- لینک پست منتشرشده ذخیره می‌شود

---

## 🔧 API Endpoints

### ۱. مشاهده همه پست‌ها
```bash
GET /linkedin/posts
GET /linkedin/posts?status=pending_approval
```

### ۲. مشاهده یک پست خاص
```bash
GET /linkedin/posts/{post_id}
```

### ۳. تولید ایده جدید (دوشنبه)
```bash
POST /linkedin/generate/idea
```
**پاسخ:**
```json
{
  "message": "Post idea generated successfully",
  "post_id": 1,
  "topic": "Why LLMOps is becoming its own discipline",
  "status": "idea"
}
```

### ۴. تولید پیش‌نویس (چهارشنبه)
```bash
POST /linkedin/generate/draft?post_id=1
```
**پاسخ:**
```json
{
  "message": "Post draft generated successfully - awaiting approval",
  "post_id": 1,
  "topic": "Why LLMOps is becoming its own discipline",
  "content": "🚀 Just discovered something amazing about LLMOps...",
  "status": "pending_approval"
}
```

### ۵. ویرایش پیش‌نویس (اختیاری)
```bash
PATCH /linkedin/posts/{post_id}/edit
Content-Type: application/json

{
  "content": "متن ویرایش‌شده شما..."
}
```

### ۶. تایید پست برای انتشار
```bash
POST /linkedin/posts/{post_id}/approve
```
**پاسخ:**
```json
{
  "message": "Post approved successfully - ready for publishing",
  "post_id": 1,
  "status": "approved"
}
```

### ۷. انتشار نهایی در LinkedIn
```bash
POST /linkedin/posts/{post_id}/publish
```
**پاسخ:**
```json
{
  "message": "Post published successfully to LinkedIn",
  "post_id": 1,
  "status": "published",
  "published_at": "2024-08-08T12:22:58.973202+00:00",
  "linkedin_url": "https://www.linkedin.com/feed/update/urn:li:share:1",
  "content": "🚀 Just discovered something amazing..."
}
```

### ۸. حذف پست (فقط قبل از انتشار)
```bash
DELETE /linkedin/posts/{post_id}
```

---

## 🚀 راه‌اندازی سریع

### ۱. نصب وابستگی‌ها
```bash
pip install -r requirements.txt
```

### ۲. پیکربندی محیط
```bash
cp .env.example .env
# ویرایش .env و تنظیم OLLAMA_HOST
```

### ۳. اجرای سرور
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### ۴. دسترسی به Swagger UI
```
http://localhost:8000/docs
```

---

## ⚙️ زمان‌بندی خودکار

### Cron Job (Linux/Mac)
```bash
# ویرایش crontab
crontab -e

# اضافه کردن خطوط زیر:
# دوشنبه ساعت ۹ صبح - تولید ایده
0 9 * * 1 cd /path/to/AI-BrandPilot && python scheduler.py >> logs/scheduler.log 2>&1

# چهارشنبه ساعت ۹ صبح - تولید پیش‌نویس
0 9 * * 3 cd /path/to/AI-BrandPilot && python scheduler.py >> logs/scheduler.log 2>&1
```

### Windows Task Scheduler
1. باز کردن Task Scheduler
2. Create Basic Task
3. تنظیم Trigger: Weekly (Monday & Wednesday at 9 AM)
4. تنظیم Action: `python.exe C:\path\to\scheduler.py`

---

## 🔒 نکات امنیتی

### قبل از انتشار واقعی LinkedIn:
1. **احراز هویت**: اضافه کردن OAuth 2.0 برای LinkedIn API
2. **ذخیره Credentials**: استفاده از `.env` برای LinkedIn API keys
3. **Rate Limiting**: محدود کردن تعداد درخواست‌ها به LinkedIn
4. **Audit Log**: ثبت تمام اقدامات در پایگاه داده

### وضعیت‌های مختلف پست:
- `idea`: فقط موضوع انتخاب شده
- `pending_approval`: پیش‌نویس آماده، منتظر تایید
- `approved`: تاییدشده، آماده انتشار
- `published`: منتشرشده در LinkedIn
- `rejected`: ردشده توسط کاربر (قابل حذف)

---

## 📊 مثال عملی کامل

### مرحله ۱: تولید ایده
```bash
curl -X POST http://localhost:8000/linkedin/generate/idea
```

### مرحله ۲: مشاهده ایده
```bash
curl http://localhost:8000/linkedin/posts/1
```

### مرحله ۳: تولید پیش‌نویس
```bash
curl -X POST "http://localhost:8000/linkedin/generate/draft?post_id=1"
```

### مرحله ۴: بررسی و ویرایش (در صورت نیاز)
```bash
curl -X PATCH http://localhost:8000/linkedin/posts/1/edit \
  -H "Content-Type: application/json" \
  -d '{"content": "متن ویرایش‌شده شما..."}'
```

### مرحله ۵: تایید نهایی
```bash
curl -X POST http://localhost:8000/linkedin/posts/1/approve
```

### مرحله ۶: انتشار
```bash
curl -X POST http://localhost:8000/linkedin/posts/1/publish
```

---

## 🎨 رابط کاربری (پیشنهادی)

برای راحتی بیشتر، می‌توانید یک داشبورد ساده بسازید:

```html
<!-- dashboard.html -->
<!DOCTYPE html>
<html>
<head>
    <title>LinkedIn Post Dashboard</title>
</head>
<body>
    <h1>پست‌های در انتظار تایید</h1>
    <div id="pending-posts"></div>
    
    <script>
        async function loadPendingPosts() {
            const response = await fetch('/linkedin/posts?status=pending_approval');
            const posts = await response.json();
            
            posts.forEach(post => {
                document.getElementById('pending-posts').innerHTML += `
                    <div>
                        <h3>${post.topic}</h3>
                        <p>${post.content}</p>
                        <button onclick="approvePost(${post.id})">✅ تایید</button>
                        <button onclick="editPost(${post.id})">✏️ ویرایش</button>
                        <button onclick="rejectPost(${post.id})">❌ رد</button>
                    </div>
                `;
            });
        }
        
        async function approvePost(id) {
            await fetch(`/linkedin/posts/${id}/approve`, {method: 'POST'});
            alert('پست تایید شد!');
            location.reload();
        }
        
        loadPendingPosts();
    </script>
</body>
</html>
```

---

## ✅ چک‌لیست نهایی قبل از انتشار واقعی

- [ ] نصب و پیکربندی LinkedIn Developer App
- [ ] دریافت OAuth 2.0 credentials
- [ ] تست LinkedIn API در حالت sandbox
- [ ] اضافه کردن retry logic برای خطاهای شبکه
- [ ] تنظیم logging کامل
- [ ] backup از پایگاه داده
- [ ] تست end-to-end با یک پست واقعی

---

## 📞 پشتیبانی

برای هر سوال یا مشکل، لاگ‌های زیر را بررسی کنید:
- `logs/scheduler.log`: خروجی زمان‌بند خودکار
- `data/brandpilot.db`: پایگاه داده SQLite
- `/tmp/server.log`: لاگ‌های سرور FastAPI
