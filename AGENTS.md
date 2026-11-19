# 回收組與系統工程組協作規則

- 預設使用繁體中文回覆。
- 每次新對話開始時，先讀取並遵循 `/Users/zhangbaihan/.codex/skills/i-have-adhd/SKILL.md`；除非使用者說 `stop adhd mode` 或 `normal mode`，持續套用 ADHD 模式。
- 回收組 repo：<https://github.com/8twrzkxd4f-dev/ROCAFA-Recycle->，本工作區即為其本機 checkout。
- 系統工程組 repo：<https://github.com/jack580322d-eng/rocafarocket>，本機 checkout 位於 `/Users/zhangbaihan/Documents/ChatGPT/rocafarocket`。
- 開始專案工作前，先確認兩個 checkout 的工作目錄狀態，再各自執行 `git pull --ff-only`，讀取最新系統工程資料後才進行設計或修改。首次使用尚未存在的 checkout 時先 clone。
- 如有未提交修改、分支分歧或權限問題，保留現有內容並說明阻礙；不得為同步而強制覆蓋、重設或自動捨棄修改。
- 兩組 repo 分開維護，不把系統工程組的 checkout 複製或巢狀加入回收組 repo。
