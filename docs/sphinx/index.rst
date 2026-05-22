Data Analysis with Chatbots 文檔
=================================

歡迎來到 Data Analysis with Chatbots 的官方文檔！

這是一個全面的客戶分析框架，結合傳統數據科學方法與最新的 AI 技術，幫助企業深入了解客戶行為、進行精準分群，並制定有效的營銷策略。

.. toctree::
   :maxdepth: 2
   :caption: 目錄:

   installation
   quickstart
   user_guide
   api_reference
   examples
   contributing
   changelog

快速開始
--------

安裝
~~~~

.. code-block:: bash

   pip install data-analysis-chatbots

基本使用
~~~~~~~~

.. code-block:: python

   from data_analysis_chatbots import DataLoader, KMeansClusterer

   # 加載數據
   loader = DataLoader()
   df = loader.load_csv('customer_data.csv')

   # 執行聚類
   clusterer = KMeansClusterer(n_clusters=5)
   labels = clusterer.fit_predict(df, ['Age', 'Income', 'Spending'])

核心功能
--------

* **數據預處理**: 完整的數據清洗和驗證工具
* **RFM 分析**: 客戶價值分析和分群
* **K-Means 聚類**: 智能客戶分群
* **CLV 預測**: 客戶終身價值預測
* **營銷活動管理**: 數據驅動的營銷策略

主要模塊
--------

.. autosummary::
   :toctree: _autosummary
   :recursive:

   data_analysis_chatbots.preprocessing
   data_analysis_chatbots.clustering
   data_analysis_chatbots.visualization
   data_analysis_chatbots.marketing

索引和表格
----------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

授權
----

本專案採用 MIT 授權 - 詳見 `LICENSE <https://github.com/markl-a/Data-Analysis-with-Chatbots/blob/main/LICENSE>`_ 文件。

致謝
----

感謝所有為本專案做出貢獻的開發者！

聯繫方式
--------

* GitHub: https://github.com/markl-a/Data-Analysis-with-Chatbots
* 問題回報: https://github.com/markl-a/Data-Analysis-with-Chatbots/issues
