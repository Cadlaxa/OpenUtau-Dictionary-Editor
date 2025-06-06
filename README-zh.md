*[English](./README.md)* **華語**

> [!WARNING]
> 華語版本的自述文件内容并不一定是最新的並且可能存在有翻譯的錯誤，如果華語版本與英文原版有什麽出入的話以英文原版爲準

# OpenUtau辭典編輯器
用於為 OpenUtau 建立和編輯美感的 YAML 辭典的 Python GUI 工具包 🥰😍
<img width="1920" alt="ou dict prev layout" src="https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/6b533bcb-0e2e-4d67-98ff-b4cd6adb94a9">
- 要使用此GUI 工具包，對於 **`Windows`** ，我建議使用便攜式 **`.exe`** 文件，對於 **`MacOs`** 和 **`Linux`** ，我建議使用 **`.pyw`** 檔案並使用 **`Python 版本 3.10 及以上`**，  **`Python 3.9 及以下版本`** 未經測試，可能無法正常運作。
- 在 **`MacOs`** 和 **`Linux`** 安裝必要組件：
  ```
  pip install ruamel.yaml tk requests
  pip install -r requirements.txt
  ```
- pip is not on the path yet do `python get-pip.py` then pip install:
  ```
  python get-pip.py
  ```
---
## 📍 在這裏下載最新版本:
[![Download Latest Release](https://img.shields.io/github/v/release/Cadlaxa/OpenUtau-Dictionary-Editor?style=for-the-badge&label=Download&kill_cache=1)](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/releases)
## 📍 語言支持
- OpenUtau 字典編輯器使用預先格式化的 yaml 檔案進行 GUI 翻譯。 歡迎所有使用者將 `Templates/Localizations/en_US.yaml` 中找到的文字翻譯為其他語言並提交拉取請求。
---
# 功能
## 開啟/附加 YAML 辭典
![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/a0bf596e-01a9-4ec6-bbe2-0d2503972122)
- 透過點擊 **`[開啟YAML檔]`** 按鈕，您可以開啟預製的 OpenUTAU YAML 辭典，以便使用此 GUI 工具包直接編輯它們。 **`[追加YAML檔]`**按鈕的功能是合併多個YAML文件，以便使用者可以將它們合併在一起。
## 從頭開始建立 YAML 辭典
![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/4d4b6537-2622-4c2c-b13e-a9838037ee95)
- 您可以將字素和音素新增到手動輸入部分。 按 **`[新增條目]`** 按鈕會將它們新增至條目檢視器。 使用 **`[刪除條目]`** 按鈕或鍵盤上的刪除按鈕將刪除所選條目。 透過先點選條目，然後對其他條目進行「Shift」+鼠標左鍵，會將其反白顯示，以便使用者可以使用 **`[刪除條目]`** 按鈕或刪除鍵盤按鈕批次刪除條目。
- `注意：如果從頭開始建立辭典，請從 [選擇模板] 中選擇 yaml 模板`
## 使用 G2P 加快辭典編輯/建立速度
![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/d4f2a6e7-2df5-4736-884d-073bd8a2f8e6)
- 您可以在“其他”標籤上開啟“G2P建議”，當您在單字條目上輸入單字時，它會自動產生音素
- 目前 G2p 模型與 [Openutau](https://github.com/stakira/OpenUtau) + Millefeuille French G2p model by [UFR](https://utaufrance.com/) 相同
## 使用 OpenUtau YAML 模板或自訂模板
![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/7079a076-8933-44e2-8428-939c52da749a)
- 使用 [選擇模板] ，使用者可以選擇 OpenUtau YAML 模板來建立辭典。 此外，使用者還可以新增自己的模板，將其放置在 **`[Templates]`** 資料夾中，以便 GUI 工具包將透過 templates.ini 識別這些檔案並使用它們來建立辭典。
- `提示：如果您要從頭開始建立自訂辭典，請從模板資料夾新增模板，以便您可以在[模板選擇]上使用它並新增條目，如果您已經建立了自訂辭典，只需將它們匯入編輯器即可使用 'Current Template' ，以便將條目新增至目前匯入的 yaml 檔案中，並仍保留自訂符號`
## 對條目進行排序
![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/532b16b8-eebf-423a-b974-9460e577831e)
- 使用者可以按字母順序對條目進行排序 **`A-Z`** 或 **`Z-A`**
## 將 CMUdict 轉換為 OU YAML 辭典
![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/2ecf2317-435b-427a-8535-c53dc83150cd)
- 將 CMUdict.txt 轉換為功能性 OpenUTAU 詞典的函數。 請注意，CMUdict 不得有 **`;;;`**，否則 GUI 工具包會引發錯誤。
## 編輯符號並將其儲存為模板
![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/6cde7d0b-1ad2-457d-9170-ae9d3ca2aa96)
- 使用者可以透過點擊 **`編輯符號`** 來編輯yaml字典的符號，新增或刪除符號（音素和音素類型）並儲存以供將來使用。
## 使用條目檢視器
![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/6f37b8d4-dff0-4408-9a20-954a245eeeea)
- 在條目檢視器中，使用者可以透過點擊、刪除、新增和排列條目來與條目互動。
- ### 點擊要編輯的條目
![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/2b85b200-d856-479f-840c-239ed4e2ecd5)
 - 使用者可以透過「Ctrl」+ 鼠標左鍵和「Shift」+ 鼠標左鍵來選擇檢視器中的多個條目。
- ## 雙擊儲存格直接輸入編輯
  ![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/ee821fe7-19cf-4967-8d3d-087915805b74)
  - 透過雙擊所選條目或“右鍵>編輯”，使用者可以直接編輯該條目。
- ### 拖曳條目以更改其位置
![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/d131a01c-e4e7-489d-aa57-37aaa6d406c9)
 - 使用者可以拖放條目以手動更改其位置。
## 使用正規表示式函數
![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/8623971c-fcd2-42ff-83a7-5cce092e9123)
- 使用者可以使用正規表示式搜尋和替換來取代字素或音素。
## 保存和導入辭典
- 目前創建/編輯的辭典有3種保存格式：
  - **`OpenUtau YAML 格式`**
  - ![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/a5259363-fd50-4dc1-ad5b-446fb2faba4a)
  - ![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/d90fe642-791d-4507-884b-dd6761631814)
  - **`CMUDICT 格式`**
  - ![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/d50030be-793f-488a-9327-0e5933b05d0c)
  - ![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/f7720ada-6693-4c8d-a19f-0193d75f9711)
  - **`Synthv 格式`**
  - ![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/d06fc7cf-3206-47e9-9c1d-c135d39d6663)
  - ![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/5396f87c-4481-46d2-b115-d77c066fb311)
## 改變主題和顏色色調
![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/54450466-81e2-4e2f-9cc2-135d97602121)
- 使用者可以隨意更改 GUI 工具包的主題和顏色。 目前有 **`23`** 顏色可供選擇，與其 **`淺色`** 和 **`深色`** 主題相對應。
---
- 此 GUI 工具包的其他功能包括自動為字素和音素的特殊字元`' '`、淺色模式和深色模式主題、條目排序、刪除數字重音符號、使音素小寫等等。


# 變更日誌
---
**`(6/6/25)`**
- 現在支援替換音素列表
- 正規表示式替換錯誤修復
- 支援CSV和TSV檔案的拖放和匯出
- 在地化更新程式
- 錯誤修復

**`(4/8/25)`**
- 改進的使用者介面強調色
- 更新在地化
- 錯誤修復
- CMUDict 匯入現在支援 TSV 和 CSV，並為重複的字素添加編號後綴

**`(3/14/25)`**
- 程式碼優化
- 能夠載入外部 G2P

**`(9/14/24)`**
- 將資料轉儲到 json 時確保 ascii 為 false
- G2p 組合框現在按字母順序排列
- 在符號編輯器上新增對 Diffsinger 音素替換條目的支持
- 修復了 YAML 轉儲
- 新增範本儲存視窗
- 為符號編輯器新增條目拖曳
- 字體修復
- 「導入CMUdict」 現在支援製表符而不是 2 個空格單字-音素分離
- 新增「取得符號」功能（取得詞條編輯器上的音素，並將音素類型新增至符號編輯器並猜測音素類型）
- 修正了處理時編號音素出現 int-str 錯誤的問題
- 正確的 YAML 區塊樣式
- 修改模板機制
- 將「附加 YAML 檔案」修改為「附加辭典」（現在支援所有目前辭典格式）
- 新增工具提示和工具提示切換
- 新增快取清理器
- 更新在地化
- 修復複製和貼上功能以首先驗證 YAML 條目
- 新增了俄語 HHSKT G2p - @Megageorgio
- 程式碼修復

**`(8/03/24)`**
- 新增檔案拖放檔案支援直接開啟它們
- 新增「開啟方式」功能，無需先開啟應用程式即可編輯辭典文件
- 從曲目中取得歌詞，並將其新增至樹狀圖視圖中，其中包含來自所選 G2p 模型的預測音素
- 導入聲庫yaml辭典（僅當GUI用作OpenUtau插件時才能使用）
- 修復引用字素的貼上功能
- 新增了從錄音單功能重新產生 YAML 模板
- 單獨的「外掛」標籤
- 新增了語音系統替換（使用者可以透過編輯「Templates」資料夾中的「phoneme systems.csv」來新增其他語音系統）
- 修改正規表示式對話框
- 將預設 G2p 狀態變更為 true
- 更新在地化並修復程式碼
- 修復載入視窗和儲存視窗延遲
- 將他加祿語重新翻譯為菲律賓語

**`(24/7/24)`**
- 正規表示式尋找和取代現在直接迭代和編輯 self.dictionary（保存字素和音素的資料）而不是樹視圖
- [JA Monophone G2P] 加入缺少的音素@lottev1991
- 修正了 JA Monophone G2P 將字素拆分為音素的問題
- 修復了樹狀圖視圖上的字體

**`(7/21/24)`**
- 固定下載速度
- 微小的使用者介面更改
- 使用"DarkDetect"模組透過'System'單選按鈕跟隨系統主題選項
- 用於顯示「Readme.md」檔案的「What's New」視窗（使用「tkhtmlview」和「markdown2」模組）
- 更新在地化

**`(7/13/24)`**
- 修正了 Cmudict 錯誤訊息以顯示錯誤行而不是僅顯示單字
- 更新在地化
- 修改某些 ui 元素的`Light Mode`顏色強調
- 修復`Light Mode`上的樹視圖選擇顏色
- 效能修復

**`(7/09/24)`**
- 雙擊或「輸入」按鈕直接編輯條目
- 直接條目編輯的 G2P 建議按鈕
- 更新在地化 (@zout)
- 複製輸入功能現在可以透過系統剪貼簿複製數據
- 貼上功能現在可以將資料貼到系統剪貼簿（僅接受 yaml 和 cmudict 格式）
- 修正了 G2p 組合框，更改模型時也會自動更新音素條目
- 改進了樹視圖效能，尤其是在較大的辭典檔案上
- 修改拖曳訊息 UI
- 新的鍵盤快速鍵：[`Enter` = 新增條目/符號，`Ctrl/Command + f` = 搜索，`Ctrl/Command + h` = 取代窗口，`Esc` = 關閉視窗]
- 新的 5 個主題：（`Sunny Yellow`、`Yellow Green`、`Payne's Grey`、`Sky Magenta`、`Light See Green`）
- 更新在地化 + 新在地化（'French'、'Russian'）
- 新增訊息框的在地化
- 在「右鍵」上顯示上下文選單（僅適用於條目編輯器）
- 修正了 G2p 建議上的空白組合框
- G2p 建議開關現在也保存在 `settings.ini` 中
- 將預設主題和色調設定為“Mint Dark”
- 在開啟「條目檢視器」的情況下關閉「主 GUI」將提示一則訊息，而不是立即關閉 GUI
- 程式碼修復和清理

**`(28/6/24)`**
- 新增了 G2p 建議
    - Arpabet-plus G2p (@Cadlaxa)
    - French G2p
    - German G2p (@LotteV)
    - Italian G2p
    - Japanese Monophone G2p (@LotteV)
    - Millefeuille G2p (@UFR)
    - Portuguese G2p
    - Russian G2p
    - Spanish G2p (@LotteV)
- 修正了使用 g2p 建議輸入時的單字和輸入錯誤
- 修正了輸入視窗的批次載入效能
- 更新在地化
- 準備11 個新主題：(`Sunny Yellow`, `Moonstone`, `Beaver`, `Dark Red`, `Liver`, `Yellow Green`, `Payne's Gray`, `Hunter Green`, `Sky Magenta`, `Light See Green`, `Middle Green Yellow`)
- 修復鍵盤綁定，使其不與其他系統重疊
- 改進搜尋功能以選擇最接近的值，而不是過濾它們，點擊「搜尋」按鈕將迭代最接近的搜尋值

**`(21/6/24)`**
- 修復了不同語言的字形
- 新增下載進度條
- 修正了支援使用者下載後手動移動檔案後系統退出的問題
- 程式碼修復和更新

**`(6/6/24)`**
- 修正了可執行檔的安全性問題

**`(24/5/24)`**
- 使用壓縮快取載入辭典檔案以獲得更好的效能（大檔案啟動會很慢，因為載入檔案本身+第一次建立快取）
- 儲存字典檔案時更新快取文件
- 改進了樹查看器性能（某種程度上）...
- 修正了開啟「YAML」檔案在有空白行時拋出無「grapheme」條目錯誤的問題
- 修正了 `ruamel.yaml` yaml 寬度以防止長條目換行
- 效能修復
- 載入檔案時新增載入訊息

**`(5/20/24)`**
- 重新設計了 YAML 保存功能以使用 `Ruamel.yaml` yaml.dump
- 將 2 個 YAML 儲存按鈕合併為 1 個主按鈕（標準函式庫和 diffsinger 函式庫都支援 `yaml.org,2002:map` yaml 映射格式）
- 將符號儲存為範本時新增 YAML 驗證
- 儲存檔案時準備儲存/載入訊息窗口
- 程式碼優化和修復
- 在地化更新
- 修復保存錯誤

**`(5/17/24)`**
- 修正了帶有特殊字元的音素不為整個字串添加引號的問題。
- 新增了 Synthv 匯入和匯出 `json` 辭典檔
- 儲存時自動新增擴充檔名
- 將「檢視符號」更新為「修改符號」（功能僅限於：新增/刪除符號、選擇/取消選擇、搜尋符號、儲存至範本）
- 新增了「儲存至範本」yaml 檔案和更新範本組合框，當透過「儲存至範本」儲存新檔案時，組合框會讀取「Templates」資料夾
- 更新所有在地化 + 「Cebuano」, 「Spanish (Latin America)」在地化
- 在正規表示式對話方塊中新增了「Find next」和「Find previous」條目
- 將“替換”按鈕拆分為“替換”和“全部替換”

**`(5/13/24)`**
- 修正了「v0.6.1」上的正規表示式對話方塊、複製、剪下、貼上、刪除、搜尋損壞的問題
- 變更按鍵綁定，以便「windows」和「macos」不會重疊

**`(5/12/24)`**
- 刪除詢問檔案對話方塊以尋找「templates」資料夾並替換為自動使用「templates」資料夾。
- 修正了正規表示式對話框上的頂級窗口
- 修復圖示在Windows視窗頂部無法顯示的問題
- 修正了刪除條目也會清除輸入框的問題
- 修正了載入 CMUDict 檔案後載入 YAML 導致「list indices must be integers or slices, not str」錯誤
- 新增透過「Ctrl + a」或「Command + a」選擇所有功能
- 修正了匯出 CMUDict 未匯出已刪除音素重音和小寫音素的條目的問題
- 改進了剪切和刪除條目性能
- 修復了在地化組合框，以更新 GUI 的當前本地位置，並使用人類可讀的選項而不是檔案名稱。
- 新增了「Japanese」在地化（使用 DeepL 製作）
- 在樹狀圖檢視上新增了索引標題

**`(5/7/24)`**
- 修正儲存 YAML 的錯誤
- 透過 `Ctrl + c`/`Command + c` `Ctrl + x`/`Command + x` `Ctrl + v`/`Command + v` 加入`複製`、`剪下`和`貼上`功能
- 已選擇的樹視圖現在可以同時處理多個數據
- 條目的多項選擇將在條目框中可見，而不僅僅是最後選擇的條目。
- Utau/OpenUtau 傳統插件（Legacy Plug-in）功能
- 適用於「Windows」、「MacOS」和「Linux」的可移植可執行文件，請使用「.pyw」腳本
- 修正了「tcl」無法找到主題導致應用程式無法啟動的問題
- 修改正規表示式對話框
- 修正搜尋條目的儲存功能，僅儲存搜尋條目，其餘條目消失
- 下載後開啟檔案目錄的選項
- 更新「Chinese Simplified」、「Chinese Traditional」和「Cantonese」在地化（感謝 @Zout141 ）


**`(5/4/24)`**
- 更新「Chinese Simplified」、「Chinese Traditional」和「Cantonese」在地化（感謝 @Zout141 ）
- 修復了重音按鈕上的「Lemon Ginger」主題字體顏色，以獲得更好的對比度
- 新增條目功能現在將條目新增至所選條目下方而不是樹狀圖視圖的結尾，如果沒有所選條目，它將新增至樹狀圖視圖的末端。
- 透過**`右鍵`**新增項目取消選擇功能
- 修正了拖曳標籤在拖曳到條目以外的其他內容時卡住的問題
- 新增匯出 CMUdict 檔的功能
- 修正了如果互聯網暫時斷開並再次重新連接的情況下，更新按鈕無法檢查更新的問題
- 搜尋功能現在忽略搜尋中的“,”，從“hh, eh, l, ow”到“hh eh l ow”，與正規表示式查找和取代功能相同。
- 加入透過`Ctrl + z`/`Command + z`進行撤回和`Ctrl + y`/`Command + y`進行重做的功能
- 更多修復

**`(24/4/24)`**
- 增加了更多主題和顏色色調 `["Amaranth", "Amethyst", "Burnt Sienna", "Dandelion", "Denim", "Electric Blue", "Fern", "Lemon Ginger", "Lightning Yellow", "Mint", "Orange", "Pear", "Persian Red", "Pink", "Salmon", "Sapphire", "Sea Green", "Seance"]`
- 自動滾動速度從“10”調整為“20”
- 在樹狀檢視器上新增了字形重新縮放功能
- 新增了「Chinese Simplified」、「Chinese Traditional」和「Cantonese」在地化（感謝 @Zout141 ）
- 新增了標準 Python .gitignore （感謝 @oxygen-diicide ）
- 新增了自動更新程式的功能
- 新增了符號檢視器（有點問題且無法編輯符號）
- 將 Windows 字型從 **Segoe UI** 改為 **Arial Rounded MT Bold**
- 修復了 UI 元素
- 更多修復

**`(4/19/24)`**
- 增加標籤欄
- 允許透過 YAML 檔案進行在地化
- 使用者介面更改
- **`templates.ini`** 現已棄用並更改為 **`settings.ini`**，使用者現在可以刪除 **`templates.ini`**
- 修復了樹視圖
- 將主題移至「設定」選項卡，資料透過 **`settings.ini`** 存儲

**`(24/4/15)`**
- **V.01 發布**
- **初始版本已發布，工具的功能介紹均在自述文件的[功能部分](#功能)**
