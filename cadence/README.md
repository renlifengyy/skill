# Cadence SKILL: Align segPath segments by pitch

此脚本用于把选中的 `segPath` 线段按固定间距对齐（对齐到指定 pitch 的网格）。

## 使用方法

1. 在 Virtuoso 中加载脚本：

```
load("/path/to/align_segpath.il")
```

2. 选中一个或多个 `segPath` 对象（包含你希望对齐的段）。
3. 运行交互命令：

```
skillAlignSegPathPrompt()
```

或直接传入 pitch：

```
skillAlignSegPathToPitch(0.2)
```

如需确认当前环境中 API 是否可用（并尽早暴露语法或依赖问题），可先执行：

```
skillAlignSegPathCheck()
```

## 行为说明

- 对于垂直段（`x` 坐标相同），将 `x` 对齐到最近的 `pitch` 倍数。
- 对于水平段（`y` 坐标相同），将 `y` 对齐到最近的 `pitch` 倍数。
- 只处理选中的 `segPath` 对象，其他对象不变。
