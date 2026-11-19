# 功能规格：番茄钟「预计结束时间」实时计算

> 本文档是给另一个模型/工程师执行并测试用的完整规格。目标文件只有一个：
> `build/app.template.html`（改完跑 `python build/build.py` 重新生成 `index.html`）。
> 不要直接改 `index.html`（它是生成物，会被覆盖）。

---

## 1. 需求（已与用户确认）

在**设置页**（`#screen-setup`）的「循环次数」下方，新增一行实时计算的「预计结束时间」。

- **计算范围**：本次番茄钟**全部轮次结束**的时刻。
- **是否计入休息**：计入。结束时刻 = 当前时间 + 专注时长×轮次 + 休息时长×(轮次−1)。
- **显示位置与更新方式**：设置在设置页、**实时刷新**——既随参数变动即时重算，也随当前时间每秒跳动（跨分钟后分钟数 +1）。
- **目标日期模式**：不处理（目标日期模式本身即倒数到固定时刻，无需此功能）。切换到目标日期模式时隐藏该行。
- **纯前端**：不引入任何依赖、不联网，与现有单文件/离线约束一致。

---

## 2. 计算规则（必须精确一致）

设：
- `W` = 专注时长（分钟，`S.workMin`）
- `B` = 每轮之间休息（分钟，`S.breakMin`）
- `C` = 循环次数（`S.cycles`）
- `now` = 当前时间（`Date.now()`，毫秒）

总耗时（分钟）：

```
totalMin = W * C + B * (C - 1)
```

预计结束时间戳：

```
endMs = Date.now() + totalMin * 60 * 1000
```

> 注意：休息只在「两轮之间」存在，所以是 `C - 1` 次休息。当 `C = 1` 时没有休息，`totalMin = W`。当 `B = 0`（不休息）时公式自然退化为 `W * C`，无需特判。

---

## 3. 界面改动

### 3.1 HTML 结构（在 `#pomodoro-fields` 内部、循环次数字段之后追加）

当前结构（文件约第 245–253 行）：

```html
<div class="field">
  <label>循环次数</label>
  <div class="stepper"> ... </div>
</div>
```

在该 `<div class="field">`（循环次数）**之后、`</div>`（`#pomodoro-fields` 结束，约第 254 行）之前**插入：

```html
<div class="field" id="eta-field">
  <label>预计结束</label>
  <div class="eta">
    <span class="eta-time" id="eta-time">--:--</span>
    <span class="eta-note" id="eta-note"></span>
  </div>
</div>
```

- `#eta-time`：显示预计结束的**时:分**（`HH:MM`，24 小时制，补零，如 `14:35`）。
- `#eta-note`：辅助说明，默认显示总耗时，如 `共 110 分钟`；可选。

### 3.2 CSS（追加到 `.stepper` 相关样式之后，约第 87 行后）

```css
.eta{display:flex;align-items:baseline;gap:12px}
.eta-time{font-size:26px;letter-spacing:.06em;color:#fff;font-variant-numeric:tabular-nums}
.eta-note{font-size:12px;color:var(--dim);letter-spacing:.08em}
#eta-field{display:none}   /* 默认隐藏，番茄模式才显示 */
```

> 隐藏/显示的开关用 CSS 类控制，不要用 inline `style.display` 硬编码（与现有 `pomodoroFields` 的 `setMode` 逻辑保持一致、易维护）。

---

## 4. 逻辑改动（JavaScript，均在 `(function(){ ... })()` 内）

### 4.1 新增 DOM 引用（放在现有 `var cycVal = ...` 附近，约第 350 行）

```js
var etaField = $('eta-field'), etaTime = $('eta-time'), etaNote = $('eta-note');
```

### 4.2 新增工具函数（放在 `fmtClock` 附近，约第 419 行后）

```js
function pad2(n) { return n < 10 ? '0' + n : '' + n; }

function updateEta() {
  if (S.mode !== 'pomodoro') { etaField.style.display = 'none'; return; }
  etaField.style.display = 'block';   // 注意：必须显式 'block'，不能用 ''（空串会回落 CSS 的 display:none）
  var totalMin = S.workMin * S.cycles + S.breakMin * (S.cycles - 1);
  var endMs = Date.now() + totalMin * 60 * 1000;
  var d = new Date(endMs);
  etaTime.textContent = pad2(d.getHours()) + ':' + pad2(d.getMinutes());
  etaNote.textContent = '共 ' + totalMin + ' 分钟';
}
```

> ⚠️ **已知坑**：`#eta-field` 的 CSS 默认是 `display:none`，若番茄模式用 `style.display = ''`（空字符串）去"恢复显示"，空串会让元素回落到样式表的 `display:none`，导致字段永远不显示。**必须显式写 `style.display = 'block'`**。

### 4.3 触发时机（关键，保证「实时刷新」）

`updateEta()` 需要在以下所有时机被调用：

1. **专注时长变化**：`bindChips(durChips, ...)` 的回调（约第 478 行）末尾、`durCustom` 的 `input` 监听（约第 490 行）里。
2. **休息时长变化**：`bindChips(breakChips, ...)` 回调（约第 479 行）、`breakCustom` 的 `input` 监听（约第 500 行）里。
3. **循环次数变化**：`setCycle(n)` 函数（约第 481–485 行）末尾。
4. **模式切换**：`setMode(mode)` 函数（约第 456–465 行）末尾——用于隐藏/显示（目标日期模式隐藏）。
5. **初始化**：`syncControlsFromState()` 之后（初始化流程里，约第 959 行 `syncControlsFromState();` 之后）调用一次，保证进入页面即有值。
6. **每秒跟随当前时间**：加一个 `setInterval`，每秒调用 `updateEta()`，使「分钟」随时间自然进位。

最省事的做法：在以上每个函数末尾都调用 `updateEta()`，并在初始化处加：

```js
setInterval(updateEta, 1000);
```

> 建议把 `updateEta` 做成幂等、无副作用（只读写自身状态和 DOM），这样在任意地方重复调用都安全。

---

## 5. 边界与一致性要求

- `C=1` 时休息为 0 次，`totalMin = W`（公式已天然满足）。
- `B=0`（不休息）时 `totalMin = W*C`，`eta-note` 仍正确显示。
- 跨午夜：`getHours()` 在 24:00 会回到 `00`，属正常表现，无需特殊处理（显示 `00:xx` 即可）。
- 目标日期模式：`updateEta` 开头 `if (S.mode !== 'pomodoro')` 隐藏并 `return`，不得计算或显示。
- 不得引入任何外部库/网络请求；保持纯黑底白字风格与现有 `tabular-nums` 数字对齐。
- `saveSettings()` / `loadSettings()` 不需要改动（预计结束时间是派生值，不持久化）。

---

## 6. 改动文件清单

| 文件 | 改动 |
|---|---|
| `build/app.template.html` | ① 追加 HTML（3.1）② 追加 CSS（3.2）③ 新增 DOM 引用与函数（4.1、4.2）④ 各回调/函数末尾调用 `updateEta()`（4.3）⑤ 初始化处 `setInterval` + 首次调用 |
| `build/build.py` | **无需改动**（构建脚本只做内联，与新功能无关） |
| `index.html` | 构建后自动生成，**不要手改** |

构建命令（在项目根目录 `flip-pomodoro/` 下）：

```bash
python build/build.py
```

---

## 7. 测试用例（供验证）

> 测试方式：用无头 Chrome 或直接双击 `index.html`，通过 URL 参数注入初始值，或用浏览器控制台手动断言。时间不可控，建议用「固定参数 + 观察字符串」的方式核对分钟数。

### TC-E1：默认值正确
参数：`workMin=25, breakMin=5, cycles=4`。
期望 `totalMin = 25*4 + 5*3 = 100 + 15 = 115` 分钟。
断言：`#eta-note` 文本为「共 115 分钟」；`#eta-time` = 当前时间 + 115 分钟后的 `HH:MM`。

### TC-E2：单轮无休息
`workMin=25, breakMin=5, cycles=1`。
期望 `totalMin = 25`，note 显示「共 25 分钟」。

### TC-E3：不休息
`workMin=25, breakMin=0, cycles=4`。
期望 `totalMin = 100`，note 显示「共 100 分钟」。

### TC-E4：目标日期模式隐藏
切换到「目标日期」模式。
期望 `#eta-field` 隐藏（`style.display === 'none'` 或元素不可见），不显示任何结束时间。

### TC-E5：参数联动实时更新
页面加载后，点「循环次数」的 `＋` 或 `−`。
期望 `#eta-time` / `#eta-note` 立即变化，且与手算一致。

### TC-E6：跨分钟自然进位（可选）
观察约 60 秒（或改小时间单位自测）。
期望 `#eta-time` 的分钟随真实时间前进而 +1，无跳变、无卡死。

### TC-E7：无控制台报错
加载页面、切换模式、调节参数、开始专注后返回设置页。
期望 Console 无 `ReferenceError` / `TypeError`，`updateEta` 每次调用无异常。

---

## 8. 验收标准

1. 番茄模式下设置页显示「预计结束 HH:MM」及「共 N 分钟」。
2. 任意参数变动后立即重算且数值正确（对照 4.2 公式手算）。
3. 目标日期模式下该行隐藏。
4. 不联网、无新依赖，`python build/build.py` 构建成功，`index.html` 仍为单文件。
5. 纯黑底白字风格、数字 `tabular-nums` 对齐与现有 UI 一致。
