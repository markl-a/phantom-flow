"""
社交媒體管理自動化

功能：
- AI 生成社交媒體內容
- 多平台發布（Twitter, Facebook, LinkedIn等）
- 內容日曆管理
- 自動回覆評論
- 數據分析和報告
"""

import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ai_automation_framework.llm import OpenAIClient
from ai_automation_framework.agents import BaseAgent
from ai_automation_framework.tools.media_messaging import SlackTool
from ai_automation_framework.tools.data_processing import ExcelAutomationTool


class SocialMediaManager:
    """社交媒體管理自動化系統"""

    def __init__(self):
        """初始化社交媒體管理器"""
        self.client = OpenAIClient()

        # 創建專業化代理
        self.content_creator = BaseAgent(
            name="ContentCreator",
            system_message="""你是社交媒體內容創作專家。
            你擅長：
            - 創作吸引人的帖子
            - 符合品牌調性
            - 使用適當的 hashtags
            - 優化參與度
            """
        )

        self.community_manager = BaseAgent(
            name="CommunityManager",
            system_message="""你是社群經理。
            你擅長：
            - 回覆評論和私信
            - 處理客戶問題
            - 維護品牌形象
            - 建立社群關係
            """
        )

        self.analyst = BaseAgent(
            name="SocialMediaAnalyst",
            system_message="""你是社交媒體分析師。
            你擅長：
            - 數據分析
            - 趨勢識別
            - 洞察提取
            - 策略建議
            """
        )

        self.excel_tool = ExcelAutomationTool()

    def create_content_calendar(
        self,
        brand_info: str,
        platforms: List[str],
        duration_days: int = 7,
        posts_per_day: int = 3
    ) -> Dict:
        """
        創建內容日曆

        Args:
            brand_info: 品牌信息
            platforms: 平台列表
            duration_days: 天數
            posts_per_day: 每天帖子數

        Returns:
            內容日曆
        """
        print(f"📅 創建 {duration_days} 天的內容日曆...")

        prompt = f"""
        為以下品牌創建 {duration_days} 天的社交媒體內容日曆：

        **品牌信息**:
        {brand_info}

        **平台**: {', '.join(platforms)}
        **每天帖子數**: {posts_per_day}

        請生成內容日曆，包括：

        ## 格式
        對於每一天（第1天到第{duration_days}天）：

        ### Day X - [日期]

        #### 帖子 1 (時間: [建議時間])
        - **平台**: [平台]
        - **類型**: [內容類型：教育/娛樂/促銷/互動]
        - **標題/文案**: [吸引人的文案]
        - **Hashtags**: [相關標籤]
        - **圖片建議**: [圖片描述]
        - **目標**: [這個帖子的目標]

        #### 帖子 2 ...

        要求：
        1. 內容多樣化（不同類型）
        2. 適合各平台特點
        3. 包含互動元素
        4. 考慮最佳發布時間
        5. 平衡促銷和價值內容

        以結構化的 Markdown 格式輸出。
        """

        calendar = self.content_creator.chat(prompt)

        return {
            "brand": brand_info,
            "platforms": platforms,
            "duration_days": duration_days,
            "posts_per_day": posts_per_day,
            "calendar": calendar,
            "created_at": datetime.now().isoformat()
        }

    def generate_post(
        self,
        topic: str,
        platform: str,
        tone: str = "professional",
        include_hashtags: bool = True,
        include_call_to_action: bool = True
    ) -> Dict:
        """
        生成單個社交媒體帖子

        Args:
            topic: 主題
            platform: 平台（twitter/facebook/linkedin/instagram）
            tone: 語氣
            include_hashtags: 是否包含標籤
            include_call_to_action: 是否包含 CTA

        Returns:
            帖子內容
        """
        platform_specs = {
            "twitter": "280 字符限制，簡潔有力",
            "facebook": "較長內容可接受，適合故事性",
            "linkedin": "專業內容，行業洞察",
            "instagram": "視覺為主，文案輔助，多用 emoji"
        }

        prompt = f"""
        為 {platform} 創建社交媒體帖子：

        **主題**: {topic}
        **語氣**: {tone}
        **平台特點**: {platform_specs.get(platform, "通用社交媒體")}

        請生成：

        ## 主要文案
        [吸引人的文案內容]
        """

        # 動態添加可選部分
        if include_hashtags:
            prompt += """
        ## Hashtags
        [相關標籤，5-10個]
        """

        if include_call_to_action:
            prompt += """
        ## Call-to-Action
        [行動呼籲]
        """

        prompt += """

        ## 最佳發布時間
        [建議的發布時間和原因]

        ## 圖片建議
        [配圖建議描述]

        ## 預期參與度
        [預測的點讚、評論、分享情況]

        要求：
        - 符合平台特點
        - 吸引目標受眾
        - 優化參與度
        - 符合品牌調性
        """

        content = self.content_creator.chat(prompt)

        return {
            "topic": topic,
            "platform": platform,
            "tone": tone,
            "content": content,
            "created_at": datetime.now().isoformat()
        }

    def generate_content_variations(
        self,
        base_content: str,
        platforms: List[str]
    ) -> Dict[str, str]:
        """
        為不同平台生成內容變體

        Args:
            base_content: 基礎內容
            platforms: 平台列表

        Returns:
            各平台的內容變體
        """
        print("🔄 為不同平台生成內容變體...")

        prompt = f"""
        將以下基礎內容改編為適合不同平台的版本：

        **基礎內容**:
        {base_content}

        **目標平台**: {', '.join(platforms)}

        為每個平台生成適配版本：

        ## Twitter
        - 280 字符以內
        - 簡潔有力
        - 包含相關標籤

        ## Facebook
        - 較詳細的故事性內容
        - 適合分享
        - 鼓勵評論

        ## LinkedIn
        - 專業語氣
        - 行業洞察
        - 專業標籤

        ## Instagram
        - 視覺描述
        - 使用 emoji
        - Instagram 風格標籤

        確保：
        - 核心信息一致
        - 適應平台特點
        - 優化參與度
        """

        variations = self.content_creator.chat(prompt)

        return {
            "base_content": base_content,
            "platforms": platforms,
            "variations": variations
        }

    def respond_to_comment(
        self,
        comment: str,
        context: str = "",
        tone: str = "friendly"
    ) -> str:
        """
        AI 生成評論回覆

        Args:
            comment: 評論內容
            context: 上下文（原帖子內容等）
            tone: 回覆語氣

        Returns:
            回覆內容
        """
        prompt = f"""
        為以下評論生成適當的回覆：

        **評論**: {comment}

        {f"**上下文**: {context}" if context else ""}

        **語氣**: {tone}

        要求：
        1. 友好且專業
        2. 解答問題或感謝反饋
        3. 鼓勵進一步互動
        4. 維護品牌形象
        5. 簡潔明了

        只提供回覆內容，不需要額外說明。
        """

        return self.community_manager.chat(prompt)

    def analyze_post_performance(
        self,
        posts_data: List[Dict]
    ) -> str:
        """
        分析帖子表現

        Args:
            posts_data: 帖子數據列表，每個包含：
                - content: 內容
                - likes: 點讚數
                - comments: 評論數
                - shares: 分享數
                - reach: 觸達數

        Returns:
            分析報告
        """
        print("📊 分析帖子表現...")

        # 準備數據摘要
        total_posts = len(posts_data)
        total_likes = sum(p.get('likes', 0) for p in posts_data)
        total_comments = sum(p.get('comments', 0) for p in posts_data)
        total_shares = sum(p.get('shares', 0) for p in posts_data)
        avg_reach = sum(p.get('reach', 0) for p in posts_data) / total_posts if total_posts > 0 else 0

        # 找出最佳表現
        best_post = max(posts_data, key=lambda x: x.get('likes', 0) + x.get('comments', 0) * 2)

        prompt = f"""
        分析以下社交媒體表現數據：

        **總體統計**:
        - 帖子總數: {total_posts}
        - 總點讚: {total_likes}
        - 總評論: {total_comments}
        - 總分享: {total_shares}
        - 平均觸達: {avg_reach:.0f}

        **最佳表現帖子**:
        內容: {best_post.get('content', '')[:100]}...
        點讚: {best_post.get('likes', 0)}
        評論: {best_post.get('comments', 0)}
        分享: {best_post.get('shares', 0)}

        **所有帖子數據**:
        {posts_data[:5]}  # 顯示前5個

        請提供：

        ## 1. 關鍵洞察
        - 最重要的發現（3-5點）
        - 表現趨勢

        ## 2. 最佳實踐識別
        - 什麼類型的內容表現最好
        - 最佳發布時間
        - 有效的互動策略

        ## 3. 改進建議
        - 內容方面
        - 互動方面
        - 發布策略

        ## 4. 下週行動計劃
        - 優先事項（3-5項）
        - 具體行動

        以清晰、可執行的格式輸出。
        """

        return self.analyst.chat(prompt)

    def generate_monthly_report(
        self,
        month_data: Dict,
        save_to_excel: bool = True
    ) -> str:
        """
        生成月度報告

        Args:
            month_data: 月度數據
            save_to_excel: 是否保存為 Excel

        Returns:
            報告內容
        """
        print("📈 生成月度報告...")

        # 生成 AI 分析
        analysis = self.analyze_post_performance(month_data.get('posts', []))

        # 創建報告
        report = f"""
# 社交媒體月度報告

生成時間: {datetime.now().strftime('%Y年%m月%d日')}

---

{analysis}

---

## 數據摘要

- 總帖子數: {month_data.get('total_posts', 0)}
- 新增粉絲: {month_data.get('new_followers', 0)}
- 總互動數: {month_data.get('total_engagements', 0)}
- 平台分布: {month_data.get('platform_distribution', {})}

---

*此報告由 AI 自動生成*
"""

        if save_to_excel and month_data.get('posts'):
            # 保存到 Excel
            import pandas as pd
            df = pd.DataFrame(month_data['posts'])
            filename = f"social_media_report_{datetime.now().strftime('%Y%m')}.xlsx"
            self.excel_tool.write_excel(filename, df, auto_format=True)
            print(f"📊 Excel 報告已保存: {filename}")

        return report


# ==================== 使用示例 ====================

def demo_content_generation():
    """演示內容生成"""
    print("=" * 70)
    print("📱 演示 1: 社交媒體內容生成")
    print("=" * 70)

    manager = SocialMediaManager()

    # 生成單個帖子
    print("\n1. 生成 LinkedIn 帖子:")
    post = manager.generate_post(
        topic="AI 在企業自動化中的應用",
        platform="linkedin",
        tone="professional"
    )
    print(post['content'])

    # 生成內容變體
    print("\n\n2. 為多平台生成內容變體:")
    base = "我們很高興宣布推出新的 AI 自動化工具！這將幫助企業提升 50% 的工作效率。"
    variations = manager.generate_content_variations(
        base_content=base,
        platforms=["twitter", "facebook", "linkedin"]
    )
    print(variations['variations'])


def demo_content_calendar():
    """演示內容日曆"""
    print("\n\n" + "=" * 70)
    print("📅 演示 2: 內容日曆生成")
    print("=" * 70)

    manager = SocialMediaManager()

    brand_info = """
    品牌: TechFlow Solutions
    行業: 企業 AI 解決方案
    目標受眾: 企業決策者、IT 經理
    品牌調性: 專業、創新、可信賴
    主要產品: AI 自動化平台
    """

    calendar = manager.create_content_calendar(
        brand_info=brand_info,
        platforms=["linkedin", "twitter"],
        duration_days=7,
        posts_per_day=2
    )

    print("\n內容日曆:")
    print(calendar['calendar'])


def demo_community_management():
    """演示社群管理"""
    print("\n\n" + "=" * 70)
    print("💬 演示 3: 自動回覆評論")
    print("=" * 70)

    manager = SocialMediaManager()

    comments = [
        "這個產品看起來很棒！價格是多少？",
        "我遇到了技術問題，能幫忙嗎？",
        "感謝分享這麼有用的信息！",
        "你們支持哪些編程語言？"
    ]

    print("\n自動生成的回覆:")
    for i, comment in enumerate(comments, 1):
        print(f"\n評論 {i}: {comment}")
        reply = manager.respond_to_comment(comment)
        print(f"回覆: {reply}")


def demo_performance_analysis():
    """演示表現分析"""
    print("\n\n" + "=" * 70)
    print("📊 演示 4: 表現分析")
    print("=" * 70)

    manager = SocialMediaManager()

    # 模擬數據
    posts_data = [
        {
            "content": "介紹我們新的 AI 功能",
            "likes": 150,
            "comments": 25,
            "shares": 30,
            "reach": 5000
        },
        {
            "content": "客戶成功案例分享",
            "likes": 200,
            "comments": 40,
            "shares": 50,
            "reach": 8000
        },
        {
            "content": "行業趨勢分析",
            "likes": 120,
            "comments": 15,
            "shares": 20,
            "reach": 4000
        },
    ]

    analysis = manager.analyze_post_performance(posts_data)
    print("\n分析結果:")
    print(analysis)


def main():
    """主函數"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 18 + "社交媒體管理自動化" + " " * 18 + "║")
    print("╚" + "═" * 68 + "╝")

    print("\n這個工具展示如何使用 AI 自動化社交媒體管理。")

    try:
        demo_content_generation()
        demo_content_calendar()
        demo_community_management()
        demo_performance_analysis()

        print("\n\n" + "=" * 70)
        print("✅ 所有演示完成！")
        print("=" * 70)
        print("\n💡 提示：")
        print("  - 可以集成到社交媒體管理工具（Buffer, Hootsuite等）")
        print("  - 建議設置定時任務自動發布")
        print("  - 結合數據分析優化內容策略")
        print("  - 人工審核 AI 生成的內容")

    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import os
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  需要設置 OPENAI_API_KEY 環境變量")
    else:
        main()
