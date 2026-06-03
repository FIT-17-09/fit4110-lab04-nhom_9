# Chạy A7 Notification Service bằng Docker

Hướng dẫn này giúp bạn build và chạy ứng dụng cục bộ bằng Docker, đồng thời sử dụng Postman/Newman để kiểm thử API.

## Bước 1: Build Docker Image
Chạy lệnh sau để tạo Docker image:
```bash
make build
# Hoặc lệnh thuần: docker build -t fit4110/notification-service:lab04 .
```

## Bước 2: Chạy Docker Container
Sau khi build xong, khởi động container:
```bash
make run
# Hoặc lệnh thuần: docker run --rm --name fit4110-notify-lab04 -p 8000:8000 --env-file .env.example fit4110/notification-service:lab04
```
*Lưu ý: Dịch vụ chạy dưới quyền non-root (appuser).*

## Bước 3: Kiểm tra trạng thái
Mở trình duyệt hoặc dùng cURL gọi API `/health`:
```bash
curl http://localhost:8000/health
```
Bạn sẽ nhận được phản hồi `{ "status": "ok", "service": "notification-service" }`.

## Bước 4: Chạy Postman Newman Tests
Kiểm tra API bằng các test case đã định nghĩa:
```bash
make test-docker
# Hoặc: npm run test:local
```

Kết quả (report) sẽ được lưu trong thư mục `reports/`.

## Bước 5: Tắt Container
```bash
make stop
# Hoặc: docker stop fit4110-notify-lab04
```
