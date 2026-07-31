# 餐饮分析前端 · 设计风格规范（Design Style Guide）

> 这份文档**记录这套前端"已建成、且确认喜欢"的设计语言**,作为后续新增页面/组件的统一参照。
> 与 `D:\workspace\Agent\.cursor\rules\apple-design.mdc`(设计契约/理想)互补:`.mdc` 是"应该怎么做",本文是"现在实际是怎么做的、并以此为准"。
> **令牌唯一事实源**:`src/app/globals.css`(`@theme` + `:root` + 暗色 `@media`)。改风格先改这里。

---

## 0. 风格定位（一句话）

**苹果系统级（Apple system-native）的浅色仪表盘**:`#f5f5f7` 灰白底 + 纯白圆角卡片 + 官方 systemColor 语义色 + SF 字体 + 软环境光阴影 + framer 弹簧动效。克制、留白充足、信息层级靠"大号粗体数字 + 灰色注脚"建立。明暗双模式,深色为纯黑 OLED 风。

设计三原则:
1. **内容呼吸** —— 大留白、约束容器宽度(`max-w-6xl`)、分区用 `space-y-8`。
2. **柔和真实** —— 圆角 + 软阴影模拟环境光,不用硬边框/硬投影;材质半透明。
3. **有生命的交互** —— 状态切换走 framer 弹簧(spring),不用线性过渡;入场逐项编排。

---

## 1. 颜色系统

全部为 CSS 变量,浅色定义在 `:root`,深色在 `@media (prefers-color-scheme: dark)` 整体重映射(值取苹果官方 iOS 明暗色板)。Tailwind 里以 `text-system-blue` / `bg-system-gray-6` 等使用。

### 基底
| 令牌 | 浅色 | 深色 | 用途 |
|---|---|---|---|
| `--background` | `#f5f5f7` | `#000000` | 页面底色(apple.com 标志性灰白 / OLED 纯黑) |
| `--foreground` | `#1d1d1f` | `#f5f5f7` | 主文字 |
| `--card-bg` | `#ffffff` | `#1c1c1e` | 卡片底 |
| `--glass-bg` | `rgba(255,255,255,.72)` | `rgba(30,30,30,.72)` | 玻璃材质底(顶栏) |
| `--glass-border` | `rgba(0,0,0,.1)` | `rgba(255,255,255,.1)` | 描边/分隔线 |

### 语义色（Apple System Colors）
| 令牌 | 浅色 | 深色 |
|---|---|---|
| `--system-blue` | `#007aff` | `#0a84ff` |
| `--system-green` | `#34c759` | `#32d74b` |
| `--system-indigo` | `#5856d6` | `#5e5ce6` |
| `--system-orange` | `#ff9500` | `#ff9f0a` |
| `--system-pink` | `#ff2d55` | `#ff375f` |
| `--system-purple` | `#af52de` | `#bf5af2` |
| `--system-red` | `#ff3b30` | `#ff453a` |
| `--system-teal` | `#5ac8fa` | `#64d2ff` |
| `--system-yellow` | `#ffcc00` | `#ffd60a` |

### 中性灰阶
| 令牌 | 浅色 | 深色 | 典型用途 |
|---|---|---|---|
| `--system-gray` | `#8e8e93` | `#8e8e93` | 次要文字/注脚/未选中态 |
| `--system-gray-2` | `#aeaeb2` | `#636366` | |
| `--system-gray-3` | `#c7c7cc` | `#48484a` | |
| `--system-gray-4` | `#d1d1d6` | `#3a3a3c` | 空态图标 |
| `--system-gray-5` | `#e5e5ea` | `#2c2c2e` | hover 底 |
| `--system-gray-6` | `#f2f2f7` | `#1c1c1e` | 填充块/hover 底/空态容器 |

### 用色规范
- **强调色 = 蓝**(`system-blue`):主按钮、链接、选中态、折线主色、品牌字 "AI"。
- **语义色按含义固定映射**(见 §9 图标),不随意换色。
- 正文永远 `foreground`,注脚永远 `system-gray`;**不要**用纯黑 `#000`/纯灰当文字。
- 卡片永远 `card-bg`,不要给卡片再叠背景色(英雄区渐变除外)。

---

## 2. 字体排版

```css
--font-sans: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
--font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
```
- **原生 SF 字体栈**:苹果设备直接命中 San Francisco,其它系统优雅降级。**不引入 Inter / Google Fonts**(国内会超时白屏,且原生更正宗)。
- `body` 开启 `-webkit-font-smoothing: antialiased` + `text-rendering: optimizeLegibility`。
- 标题统一加 `tracking-tight`(负字距),贴合 SF 大字号紧排特征。

### 字号阶梯（当前实际在用的层级，建议沿用)
| 角色 | Tailwind | 说明 |
|---|---|---|
| 页面大标题 | `text-3xl font-bold tracking-tight` | 如店名、报告页 H1 |
| 区块标题 | `text-2xl font-bold` / `CardTitle = text-lg font-semibold tracking-tight` | |
| KPI 数字 | `text-2xl font-bold`(超大统计 `text-3xl`) | 配 `text-sm` 单位后缀 |
| 正文 | 默认(≈`text-base`) | |
| 标签/描述 | `text-sm`(`text-system-gray`) | 表单 label、卡片描述 |
| 注脚/元信息 | `text-xs text-system-gray` | KPI 副说明、坐标值 |
| 等宽数值 | `font-mono` | 经纬度等 |

---

## 3. 材质与玻璃（Materials）

```css
.glass {                /* 顶栏、侧栏背景、模态遮罩层 */
  background-color: var(--glass-bg);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--glass-border);
}
```
- 半透明 + 20px 模糊,用于**导航/悬浮层**(随内容滚动透出底色),不用于实体内容卡片。
- 输入框用轻玻璃:`bg-white/50 dark:bg-black/50 backdrop-blur-sm`。
- 模态遮罩:`backdrop-blur-sm` + 弹簧缩放入场(见 §7)。

> **现状特征(可选增强)**:`.glass` 目前只有 `blur`,未加 `saturate(180%)`。真 HIG 材质常叠 `saturate` 让背后颜色更鲜活。当前"清淡玻璃"是本套风格的既定特征;若想更"浓"的苹果材质,可在 `.glass` 加一行 `saturate(180%)`——属增强项,非缺陷。

---

## 4. 形状与圆角（Radii）

| 元素 | 圆角 | 值 |
|---|---|---|
| 内容卡片 | `rounded-3xl` | 24px(= `.glass-card` 的 1.5rem) |
| 输入框 / 按钮 / 导航项 / 小按钮 | `rounded-xl` | 12px |
| 图标容器 / 头像 / 空态方块 | `rounded-2xl` | 16px |
| 圆形头像/小圆点 | `rounded-full` | |
| 图表 Tooltip | 12px | 内联 |

口诀:**外层越大越圆(卡片 24),内层交互件统一 12,装饰方块 16。**

---

## 5. 阴影与高度（Elevation）

```
默认卡片:  shadow = 0 4px 24px rgba(0,0,0,0.04)   /* 软、低、像环境光 */
hover 抬升: shadow = 0 8px 32px rgba(0,0,0,0.08)   /* .glass-card:hover 提供 */
按钮:       shadow-md / shadow-sm
```
- 阴影**软而散**,模拟环境光,而非硬投影——这是"苹果感"的关键之一。
- 深色模式下卡片靠 `card-bg #1c1c1e` 与纯黑 `#000` 的明度差 + `glass-border` 分离(阴影在纯黑上几乎不可见)。

> **现状特征(可选增强)**:`Card.tsx` 当前把默认阴影内联(`shadow-[0_4px_24px_rgba(0,0,0,0.04)]`),与 `.glass-card` 工具类**各写一份**;hover 抬升仅 `.glass-card` 有。若想让所有卡片获得 hover 抬升,可让 `Card` 复用 `.glass-card` 或补 `hover:shadow-[...]`——增强项。

---

## 6. 布局与间距（Layout & Spacing）

### 应用骨架(`layout.tsx`)
```
<body> 竖向 flex, min-h-screen
 ├─ Navbar      sticky top-0 z-50 .glass  h-14  px-4 md:px-6
 └─ <div flex flex-1 overflow-hidden>
     ├─ Sidebar  hidden md:flex  w-64  border-r  bg-background/50  px-4 py-6   (md 以下隐藏)
     └─ <main flex-1 overflow-y-auto p-4 md:p-8>
         └─ <div mx-auto max-w-6xl>  {页面内容}
```
- **约束容器**:正文最大宽 `max-w-6xl` 居中。
- **页边距**:`p-4`(移动)→ `md:p-8`(桌面)。
- **分区节奏**:页面级用 `space-y-8`;卡片网格 `gap-4`;卡片内距 `p-6`(英雄区 `p-6 md:p-8`)。

### 常用栅格
- KPI 卡行:`grid gap-4 md:grid-cols-2 lg:grid-cols-4`(4 联卡)。
- 图表区:`grid gap-4 lg:grid-cols-7`,主图 `col-span-4` + 副图 `col-span-3`(4:3 黄金比)。
- 双栏内容:`grid gap-4 md:grid-cols-2`。

---

## 7. 动效（Motion · framer-motion）

> 规则:**状态变化一律用 spring,不用 linear/ease**;入场逐项编排;退场用"模糊溶解"。

### 标准弹簧参数(全站统一)
```ts
transition: { type: "spring", stiffness: 300, damping: 24 }   // 卡片/内容；模态用 damping: 25
```

### 入场编排(列表/网格逐项淡入上移)
```ts
const container = { hidden:{opacity:0}, show:{opacity:1, transition:{ staggerChildren:0.1 }} };
const item      = { hidden:{opacity:0, y:20}, show:{opacity:1, y:0, transition:{type:"spring",stiffness:300,damping:24}} };
// 父 motion.div variants={container} initial="hidden" animate="show"，子 motion.div variants={item}
```

### 三态切换(`AnimatePresence mode="wait"`)
- **加载态**:`initial/animate opacity`,退场 `exit={{opacity:0, scale:0.98, filter:"blur(4px)"}}` `duration:0.4`(模糊溶解)。
- **内容态**:`initial={{opacity:0,y:20}} animate={{opacity:1,y:0}} duration:0.5`;二级区块再 `delay:0.4` spring 入场。
- **空态**:仅 `opacity` 淡入。

### 骨架屏(加载占位)
```tsx
<motion.div animate={{rotate:360}} transition={{repeat:Infinity, duration:1, ease:"linear"}}>
  <Loader2 className="h-10 w-10 text-system-blue" />
</motion.div>
// 配文案：标题 text-lg font-medium + 说明 text-sm text-system-gray
```

### 模态(MapSelector)
遮罩 `backdrop-blur-sm` 淡入 + 弹层弹簧缩放入场(spring 300/25)。

> **现状特征(可选增强)**:点击反馈目前用 CSS(主按钮 `active:scale-95`、导航 `transition-colors`),未用 framer `whileTap`。契约理想是 `whileTap={{scale:0.96}}`。当前 CSS 方案是既定做法;若要更"弹"的按压手感,抽一个共享 `Button` 用 `whileTap` 即可——增强项。

---

## 8. 组件配方（Component Recipes）

### 8.1 Card 系统(`components/ui/Card.tsx`)
```
Card         : rounded-3xl  border-[var(--glass-border)]  bg-[var(--card-bg)]  text-foreground  shadow-[0_4px_24px_rgba(0,0,0,0.04)]
CardHeader   : flex flex-col space-y-1.5 p-6
CardTitle    : <h3> font-semibold leading-none tracking-tight text-lg
CardDescription : <p> text-sm text-system-gray
CardContent  : p-6 pt-0
CardFooter   : flex items-center p-6 pt-0
```

### 8.2 KPI 指标卡(首页/总览四联卡)
```tsx
<Card>
  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
    <CardTitle className="text-sm font-medium">{标题}</CardTitle>
    <Icon className="h-4 w-4 text-system-{语义色}" />
  </CardHeader>
  <CardContent>
    <div className="text-2xl font-bold">{大数字}<span className="text-sm font-normal text-system-gray ml-1">{单位}</span></div>
    <p className="text-xs text-system-gray mt-1 truncate">{副说明}</p>
  </CardContent>
</Card>
```

### 8.3 英雄/操作区卡片(首页表单容器)
`border-none shadow-sm bg-gradient-to-br from-system-blue/10 to-transparent` —— 淡蓝渐变、无边、浅阴影,与下方内容卡区分。

### 8.4 输入控件
```
输入框 : w-full px-4 py-2.5 rounded-xl border border-[var(--glass-border)]
         bg-white/50 dark:bg-black/50 backdrop-blur-sm
         focus:outline-none focus:ring-2 focus:ring-system-blue/50 transition-all
label  : text-sm font-medium text-foreground   （上方 space-y-2）
图标按钮: px-3 py-2.5 rounded-xl bg-white/80 dark:bg-system-gray-6 border-[var(--glass-border)]
         hover:bg-white dark:hover:bg-system-gray-5 text-system-blue shadow-sm transition-colors
```

### 8.5 主按钮（Primary）
```
px-8 py-3 rounded-xl bg-system-blue text-white font-medium shadow-md
hover:bg-blue-600 active:scale-95 disabled:opacity-50 transition-all
```

### 8.6 侧栏导航项(`Sidebar.tsx`)
```
基础  : flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200
选中  : bg-system-blue text-white shadow-sm   （图标也转白）
未选  : text-system-gray hover:bg-system-gray-6 hover:text-foreground
```
> 现状特征:选中态为**实心蓝填充**(偏通用后台风)。苹果侧栏更常用半透明 tint(`bg-system-blue/10` + `text-system-blue`)。当前实心是既定风格;想更原生可改 tint——增强项。

### 8.7 顶栏(`Navbar.tsx`)
`sticky top-0 z-50 .glass` + `h-14`;品牌字 `Restaurant` + 蓝色 `AI`;右侧导航 `text-sm font-medium text-system-gray hover:text-foreground transition-colors`。

### 8.8 空态(Empty State)
```tsx
<div className="flex flex-col items-center justify-center h-[50vh] text-system-gray gap-4">
  <div className="w-16 h-16 rounded-2xl bg-system-gray-6 flex items-center justify-center">
    <Icon className="h-8 w-8 text-system-gray-4" />
  </div>
  <p>{引导文案}</p>
</div>
```

### 8.9 列表行(竞品/地铁/公交等)
图标(`rounded` 容器或裸 lucide)+ 主名(`font-medium`)+ 地址(`text-xs text-system-gray`,带 📍)左对齐;评分/距离右对齐(数值 + 灰色小标签)。

---

## 9. 图标（lucide-react）

- 库:`lucide-react`,**线性细描边**风格,贴合苹果。
- 尺寸:行内/卡头 `h-4 w-4`;按钮内 `h-5 w-5`;空态/骨架 `h-8`~`h-10`。
- **语义色固定映射**(沿用,勿乱换):

| 维度 | 图标 | 颜色 |
|---|---|---|
| 竞争强度/风险 | `AlertTriangle` | `system-orange` |
| 交通/趋势向好 | `TrendingUp` | `system-green` |
| 客流/人群 | `Users` | `system-blue` |
| 天气 | `Sun` / `CloudSun` | `system-yellow` |
| 位置 | `MapPin` | 随上下文 |
| 报告/总览 | `FileText` | |
| 设置 | `Settings` | |

---

## 10. 图表风格（recharts · `components/ui/Chart.tsx`）

- **调色板**(分类色,按序取):
  ```ts
  ['#007aff', '#34c759', '#ff9500', '#5856d6', '#ff2d55', '#5ac8fa']
  ```
- **折线**:`type="monotone"`(平滑)、主色 `#007aff`、`strokeWidth:3`;数据点 `r:4` 蓝填充 + `card-bg` 描边,`activeDot r:6`;入场 `animationDuration:1500 ease-out`。
- **坐标轴**:去掉轴线/刻度线(`axisLine={false} tickLine={false}`),刻度文字 `system-gray 12px`;网格 `CartesianGrid 3 3 vertical={false} stroke=glass-border`(只留水平虚线)。
- **饼/环图**:甜甜圈 `innerRadius:60 outerRadius:80`、`paddingAngle:5`、`stroke="none"`,中心可叠大号百分比文字。
- **Tooltip**:`rounded 12px` + `border glass-border` + `bg card-bg` + `shadow 0 4px 24px rgba(0,0,0,.08)` + `color foreground`——与卡片同语言。
- **容器**:`ResponsiveContainer width="100%" height="100%"`,**外层须给确定高度**(用固定 px 高的 div 包裹,避免 `flex-1`+`h-100%` 塌缩导致不渲染)。

---

## 11. Do / Don't

**Do**
- 颜色/字体/圆角/阴影一律走 §1–§5 的令牌,新组件复用 `Card` 与上面的配方。
- 状态变化用 spring(300/24);列表入场用 `staggerChildren:0.1`。
- 大号粗体数字 + 灰色注脚建立层级;多留白。
- 深浅双模式同时验收(用系统外观切换或 Playwright `colorScheme`)。

**Don't**
- 别引入 Inter/Google Fonts(白屏 + 不正宗)。
- 别用硬边框 + 硬投影;别给文字用纯黑/纯灰。
- 别用 linear/ease 做状态切换。
- 别在没有确定高度的 `flex-1` 容器里直接放 `ResponsiveContainer height="100%"`。
- 别新造一套色值——缺色先往 `globals.css` 加令牌。

---

## 12. 现状与契约的差异（诚实备注 · 均为"可选增强",非缺陷)

本套风格已建成且确认采用。以下是与 `apple-design.mdc`(理想契约)的几处差异,记录在案,想进一步提纯苹果质感时再做:

1. `.glass` 未加 `saturate(180%)` —— 玻璃偏清淡。
2. `Card.tsx` 内联阴影、未复用 `.glass-card` —— 默认卡片无 hover 抬升。
3. 点击反馈用 CSS `active:scale-95`,未用 framer `whileTap(0.96)`。
4. 侧栏选中态为实心蓝,非半透明 tint。
5. 字号阶梯为"按需使用"而非集中定义的 type scale(本文 §2 已替你归纳成事实标准)。
6. 暗色仅跟随系统 `prefers-color-scheme`,无应用内主题切换。

---

### 复用方式
- 新页面:套用 §6 骨架 + §8 组件配方 + §1 令牌即可与现有页面浑然一体。
- 想把本规范变成 AI 可遵循的"开发契约",可将本文要点同步进 `.cursor/rules/`(与 `apple-design.mdc` 并存:一个写"实现现状/事实标准",一个写"设计理想")。

*本文基于对 `globals.css` / `Chart.tsx` / `Card.tsx` / `Navbar.tsx` / `Sidebar.tsx` / `layout.tsx` / `page.tsx` 的逐文件审阅,以及 8 个页面明暗两套实机截图整理而成。*
