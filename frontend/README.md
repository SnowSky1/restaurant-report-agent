# Restaurant Report Agent Frontend 0.0.0

Next.js 经营分析工作台。它通过 FastAPI 获取 LangGraph 分析结果，展示位置、交通、商业环境、天气、竞品与 CompeteAI 情景模拟。

## 使用

```powershell
copy .env.example .env.local
npm install
npm run dev -- --hostname 127.0.0.1 --port 3000
```

设置页可调整后端地址、默认分析半径、显示主题和可选 API 访问令牌；访问令牌只保留在当前标签会话。高德 Web 服务和 LLM 密钥只配置在后端；地图 JSAPI Key 通过 `NEXT_PUBLIC_AMAP_MAPS_API_KEY` 提供给浏览器。

## 验证

```powershell
npm test
npm run lint
npm run build
npm audit --omit=dev
```
