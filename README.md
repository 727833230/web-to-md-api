# Web-to-Markdown API — 网页转结构化 Markdown 接口

基于 FastAPI + trafilatura，将网页内容提取并转为结构化 Markdown。

## 接口

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/convert` | POST | 提取网页并返回 Markdown |

## 使用示例

```bash
curl -X POST https://your-api-url/convert \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/article",
    "options": {
      "include_links": true,
      "include_images": false,
      "include_tables": true
    }
  }'
```

## 响应格式

```json
{
  "url": "https://example.com/article",
  "title": "页面标题",
  "markdown": "# 标题\n\n正文内容...",
  "metadata": {
    "description": "页面描述",
    "author": "作者",
    "date": "2024-01-01",
    "sitename": "站点名"
  },
  "word_count": 1234,
  "status": "ok"
}
```

## 部署

### Railway（推荐）

1. 推送到 GitHub
2. 在 Railway 选择 Deploy from GitHub repo
3. Railway 自动识别 Dockerfile 构建部署

### Render

1. 推送到 GitHub
2. 在 Render → New Web Service → 连接 GitHub
3. Render 自动识别 `render.yaml`
