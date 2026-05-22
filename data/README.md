# 數據目錄

此目錄用於存儲專案使用的數據文件。

## 目錄結構

- `raw/` - 原始數據文件(從Kaggle或其他來源下載)
- `processed/` - 經過清洗和預處理的數據
- `outputs/` - 分析結果和導出的數據

## 使用方法

1. 下載數據集:
```bash
python -m data_analysis_chatbots.data_downloader --all
```

2. 數據會自動保存到相應的子目錄中

## 注意事項

- 原始數據文件較大,已添加到.gitignore
- 請勿手動修改raw/目錄中的文件
- processed/目錄中的文件可以重新生成
