---
flag: "-Warray-bounds"
tier: 强制人工定性档
status: 候选（待 FatTank 确认）
---
# -Warray-bounds

- **档位**：强制人工定性档
- **相关案例**：（暂无案例，待补）
- **说明**：命中结构体尾部 `arr[1]` 这种旧式柔性数组写法时，按需看一眼档处理。
