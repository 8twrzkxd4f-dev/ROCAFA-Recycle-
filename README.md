# ROCAFA 火箭競賽回收組

圓形雙傘回收系統的設計資料、Python 模擬器、3D 概念模型與測試紀錄。

第一次接手請先閱讀 [回收組專案新手指南](回收組專案新手指南.md)。

## 專案內容

| 路徑 | 內容 |
| --- | --- |
| [回收組專案新手指南.md](回收組專案新手指南.md) | 專案背景、接手步驟與實體測試方向 |
| [output/documents/](output/documents/) | 圓形雙傘回收系統規格表（Word） |
| [output/parachute-python/](output/parachute-python/) | 裁片與 3D 介面、1D／6DOF 模擬、V&V、CFD／FSI 準備包、測試與基準結果 |
| [output/parachute-3d/](output/parachute-3d/) | 主傘、導引傘與並排比較 OBJ 模型，以及模型產生程式 |
| [tmp/](tmp/) | 文件產生程式、文件排版檢查圖片、參考報告文字與逐頁圖片；保留原始工作紀錄 |

## 啟動模擬器

需要 Python 3；模擬器僅使用標準函式庫，無需安裝 Python 套件。

```bash
git clone https://github.com/8twrzkxd4f-dev/ROCAFA-Recycle-.git
cd ROCAFA-Recycle-/output/parachute-python
python3 app.py
```

在瀏覽器開啟 <http://127.0.0.1:8765>，以 `Ctrl+C` 停止。若連接埠已被使用，可設定 `PARACHUTE_PORT`。

## 執行檢查

在 `output/parachute-python` 目錄執行既有 Python 測試：

```bash
python3 -m unittest -v
```

重新產生 OBJ 模型需要 Node.js，從 repo 根目錄執行：

```bash
node output/parachute-3d/build-models.cjs
```

瀏覽器介面測試另需 Playwright 與 Chromium。先啟動模擬器，在另一個終端機的 `output/parachute-python` 目錄執行：

```bash
npm install --no-save --package-lock=false playwright
npx playwright install chromium
node test_ui.cjs
```

此測試會更新該目錄的桌面／手機截圖與測試下載 ZIP。詳細模型假設與驗證範圍請見 [模擬器說明](output/parachute-python/README.md) 及 [V_AND_V.md](output/parachute-python/V_AND_V.md)。

## 文件與工作紀錄

規格表成品可直接下載開啟；其產生程式為 `tmp/build_parachute_doc.py`，重新產生需另安裝 `python-docx`，並準備程式指定的字型。`tmp/docx_fonts.conf` 是原 macOS 環境的排版檢查設定。

`tmp` 保留歷次工作紀錄，包含中間版本的排版圖片；最新文件以 `output/documents` 成品為準。系統檔、Python 快取、本機套件與環境憑證由 `.gitignore` 排除。

## 目前狀態

雙傘尺寸、回收質量、開傘高度及模型參數仍需依最新火箭狀態確認。3D 模型是幾何示意；動態模型尚未以本火箭實測資料標定，模擬與準備包不代表已完成實體驗證、CFD／FSI 求解或競賽驗收。
