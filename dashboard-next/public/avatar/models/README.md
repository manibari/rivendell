# Avatar VRM models

`.vrm` 檔**不進 git**（`.gitignore:33`），因為是 11 MB 級的二進位佔位模型。
代價是**換機或重 clone 後這裡是空的**，助理頁的 3D 角色會 404，畫面一片空白
（widget console：`fetch for ".../avatar/models/male.vrm" responded with 404`）。

## 換機後重抓（就是這兩行）

```bash
cd "$(git rev-parse --show-toplevel)/dashboard-next/public/avatar/models"
curl -fL -o male.vrm   https://raw.githubusercontent.com/madjin/vrm-samples/master/vroid/masc_vroid.vrm
curl -fL -o female.vrm https://raw.githubusercontent.com/madjin/vrm-samples/master/vroid/fem_vroid.vrm
```

抓完確認：兩個檔各約 11 MB，`ls -la *.vrm`。頁面不用重啟，重整即可。

## 來源與命名

- `male.vrm` ← `vroid/masc_vroid.vrm`、`female.vrm` ← `vroid/fem_vroid.vrm`，
  取自 [madjin/vrm-samples](https://github.com/madjin/vrm-samples)（VRoid Studio 產出樣本）。
- **檔名固定**：`data/persona.conf` 直接引用 `/avatar/models/{male,female}.vrm`
  （`lindir.vrm` / `miriel.vrm` 兩行）。換成自製或購入的模型時沿用同檔名即可，
  不用改設定。

## 為什麼不用 git-lfs

單機自用、模型幾乎不換，多一個 lfs 依賴不划算。真的常換模型再考慮。
