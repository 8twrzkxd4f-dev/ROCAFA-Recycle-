# 實作與驗證紀錄 — 2026-10-29

## 已實作

| 層級 | 目前能力 | 未完成部分 |
|---|---|---|
| 1D | 有限質量、ISA 密度、smoothstep 充氣、雙傘時序、收口參數、氣動力歷程 | added mass、傘繩拉直衝擊、量測充氣律標定 |
| 6DOF | 單剛體位置/速度/四元數/角速度、固定側風、偏置受力及旋轉阻尼 | 氣動係數隨攻角變化、雙剛體相對鐘擺、9DOF、實驗穩定性驗證 |
| CFD | 可匯出概念球冠薄面與求解設定，匯入三層以上網格結果 | 外部求解器、實際飛行形狀、邊界/湍流/多孔設定、流場結果 |
| FSI | 材料欄位、試驗模板、建模流程、求解器中立準備包 | 求解器授權、材料完整數據、折疊/接觸設定、雙向求解與實驗對標 |

上述輸出皆不可解讀為結構飛行放行依據。開傘「衝擊載荷」不等同超音速「震波」。數值方法也不能一概假定為顯式 ALE；使用 ICFD 時須依版本確認其流體與結構求解設定。

## 軟體 Verification

16 項 Python 單元測試通過，包含原有穩態公式、零高度初始速度、速度平方阻力律、自由落體解析解、主傘/地面事件、收口時序、6DOF 對稱退化為 1D、左右風對稱、未落地狀態、輸入檢查、CSV 插值/禁止外插、網格資料及 ZIP 完整性。

無頭瀏覽器端到端測試通過：裁片尺寸同步、1D、6DOF、時間步長敏感度、合成 CSV 比對、網格匯入、ZIP 下載及 390 px 手機版無水平溢出，無 JavaScript 執行錯誤。桌面與手機截圖已檢視。

合成 CSV 只用於程式測試，沒有被當成實測驗證。尚未取得本火箭的實驗曲線，因此 Validation 狀態為「未完成」。

## 預設參數的示例數值

質量 19.471 kg，最高點 3361 m，主傘 450 m 觸發，兩傘 Cd 分別 0.8／0.75、面積 6.05／2.12 m²，兩傘充氣時間均假設 1 s，主傘不收口，主傘觸發時導引傘阻力停用，無風。

| Δt (s) | 模型氣動力峰值 (N) | 垂直落地速度 (m/s) |
|---|---:|---:|
| 0.04 | 411.7492 | 8.026889 |
| 0.02 | 411.8323 | 8.026889 |
| 0.01 | 411.9376 | 8.026889 |

最後兩層峰值相對差約 0.0256%。這是時間步長敏感度資訊，不是已驗證的開傘最大張力；1 s 充氣假設改變就會改變載荷。預設在最高點後約 244.97 s 到地面，未包含上升段。

## 如何取得求解器

1. 先詢問指導老師、學校計算中心或力學/航太實驗室，確認 LS-DYNA Research 或 Fluent、Mechanical、System Coupling 的實際授權與遠端工作站。
2. 若是競賽團隊，查看 Ansys 學生團隊合作方案；授權內容需向對方確認。
3. 自學可用 LS-DYNA Student。查詢日官方列 Windows、128K 節點/元素與最多 4 核心；不能保證足夠完整 3D 多孔傘 FSI。
4. 無商業授權可先用 OpenFOAM 做固定幾何 CFD。Mac 官方提供 Docker 路線，需另確認電腦架構/版本。完整 FSI 還需結構求解器與耦合（例如 preCICE），不能把安裝 OpenFOAM 等同具備完整降落傘 FSI。

來源：
- https://ansys.synopsys.com/academic/students/ansys-ls-dyna-student
- https://www.ansys.com/content/dam/web/academic/ansys-student-team-partnerships-guide.pdf
- https://www.openfoam.com/download/openfoam-installation-on-mac-using-docker
- https://precice.org/adapter-openfoam-overview
- https://www.dynalook.com/conferences/international-conf-2010/Simulation-5-3.pdf
- https://www.dynalook.com/conferences/12th-european-ls-dyna-conference-2019/fluid-structure-interaction/le-garrec_dynas.pdf
- https://lsdyna.ansys.com/wp-content/uploads/attachments/generalized-porous-media-flow-in-icfd-ls-dyna-fsi-free-surface-rtm-and-parachute-modeling.pdf
