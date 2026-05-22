"""
客戶服務自動化系統
Customer Service Automation System

這個示例展示了如何構建一個完整的客戶服務自動化系統，包括：
- 自動回覆常見問題
- 情感分析
- 工單自動分類和路由
- 多渠道支持（郵件、聊天、社交媒體）
- 客戶滿意度追蹤
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from ai_automation_framework.llm.openai_client import OpenAIClient
from ai_automation_framework.agents.tool_agent import ToolAgent
from ai_automation_framework.rag.embeddings import EmbeddingModel
from ai_automation_framework.rag.vector_store import VectorStore
from ai_automation_framework.rag.retriever import Retriever


class TicketPriority(Enum):
    """工單優先級"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


class TicketStatus(Enum):
    """工單狀態"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class SentimentType(Enum):
    """情感類型"""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"


@dataclass
class CustomerTicket:
    """客戶工單"""
    ticket_id: str
    customer_id: str
    customer_name: str
    subject: str
    description: str
    channel: str  # email, chat, phone, social_media
    priority: TicketPriority
    status: TicketStatus
    sentiment: Optional[SentimentType] = None
    category: Optional[str] = None
    assigned_to: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    resolved_at: Optional[datetime] = None
    customer_satisfaction: Optional[int] = None  # 1-5

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now()
        if not self.updated_at:
            self.updated_at = datetime.now()


class CustomerServiceAgent:
    """客戶服務代理"""

    def __init__(self, api_key: str, knowledge_base_path: Optional[str] = None):
        """
        初始化客戶服務代理

        Args:
            api_key: OpenAI API 密鑰
            knowledge_base_path: 知識庫路徑
        """
        self.llm_client = OpenAIClient(api_key=api_key)

        # 初始化 RAG 系統用於常見問題
        self.embedding_model = EmbeddingModel()
        self.vector_store = VectorStore()
        self.rag_retriever = Retriever(
            embedding_model=self.embedding_model,
            vector_store=self.vector_store
        )

        # 加載知識庫
        if knowledge_base_path and os.path.exists(knowledge_base_path):
            self._load_knowledge_base(knowledge_base_path)

        # 初始化工單存儲
        self.tickets: Dict[str, CustomerTicket] = {}

        # 分類和路由規則
        self.categories = {
            "billing": ["invoice", "payment", "charge", "bill", "refund"],
            "technical": ["error", "bug", "not working", "broken", "issue"],
            "account": ["password", "login", "access", "register", "profile"],
            "shipping": ["delivery", "tracking", "order", "shipment"],
            "product": ["feature", "how to", "usage", "guide"],
        }

        # 路由規則
        self.routing_rules = {
            "billing": "billing_team",
            "technical": "tech_support",
            "account": "account_team",
            "shipping": "logistics_team",
            "product": "product_team",
        }

    def _load_knowledge_base(self, path: str):
        """加載知識庫到 RAG 系統"""
        # 這裡可以從文件或數據庫加載常見問題和答案
        faq_data = [
            {
                "question": "How do I reset my password?",
                "answer": "You can reset your password by clicking 'Forgot Password' on the login page and following the instructions sent to your email."
            },
            {
                "question": "How long does shipping take?",
                "answer": "Standard shipping takes 3-5 business days. Express shipping takes 1-2 business days."
            },
            {
                "question": "What is your refund policy?",
                "answer": "We offer a 30-day money-back guarantee on all products. Simply contact us to initiate a return."
            },
        ]

        for faq in faq_data:
            combined_text = f"Q: {faq['question']}\nA: {faq['answer']}"
            self.rag_retriever.add_document(combined_text, metadata=faq)

    def analyze_sentiment(self, text: str) -> SentimentType:
        """
        分析文本情感

        Args:
            text: 要分析的文本

        Returns:
            情感類型
        """
        prompt = f"""
        分析以下客戶消息的情感。返回以下之一：
        - positive: 正面、滿意、讚美
        - neutral: 中性、詢問
        - negative: 負面、不滿
        - very_negative: 非常負面、憤怒、威脅

        消息：{text}

        只返回一個詞：positive, neutral, negative, 或 very_negative
        """

        response = self.llm_client.simple_chat(prompt)
        sentiment_str = response.strip().lower()

        sentiment_map = {
            "positive": SentimentType.POSITIVE,
            "neutral": SentimentType.NEUTRAL,
            "negative": SentimentType.NEGATIVE,
            "very_negative": SentimentType.VERY_NEGATIVE,
        }

        return sentiment_map.get(sentiment_str, SentimentType.NEUTRAL)

    def categorize_ticket(self, ticket: CustomerTicket) -> str:
        """
        自動分類工單

        Args:
            ticket: 客戶工單

        Returns:
            分類名稱
        """
        text = f"{ticket.subject} {ticket.description}".lower()

        # 基於關鍵詞的簡單分類
        for category, keywords in self.categories.items():
            if any(keyword in text for keyword in keywords):
                return category

        # 使用 LLM 進行更複雜的分類
        prompt = f"""
        請將以下客戶工單分類到這些類別之一：
        {', '.join(self.categories.keys())}

        主題：{ticket.subject}
        描述：{ticket.description}

        只返回類別名稱。
        """

        response = self.llm_client.simple_chat(prompt)
        category = response.strip().lower()

        if category in self.categories:
            return category
        return "general"

    def determine_priority(self, ticket: CustomerTicket) -> TicketPriority:
        """
        確定工單優先級

        Args:
            ticket: 客戶工單

        Returns:
            工單優先級
        """
        # 基於情感和關鍵詞確定優先級
        priority_score = 1

        # 情感影響優先級
        if ticket.sentiment == SentimentType.VERY_NEGATIVE:
            priority_score += 3
        elif ticket.sentiment == SentimentType.NEGATIVE:
            priority_score += 2

        # 關鍵詞影響優先級
        text = f"{ticket.subject} {ticket.description}".lower()
        urgent_keywords = ["urgent", "asap", "immediately", "critical", "emergency"]
        if any(keyword in text for keyword in urgent_keywords):
            priority_score += 2

        # 轉換為優先級枚舉
        if priority_score >= 5:
            return TicketPriority.URGENT
        elif priority_score >= 3:
            return TicketPriority.HIGH
        elif priority_score >= 2:
            return TicketPriority.MEDIUM
        else:
            return TicketPriority.LOW

    def route_ticket(self, ticket: CustomerTicket) -> str:
        """
        路由工單到適當的團隊

        Args:
            ticket: 客戶工單

        Returns:
            分配的團隊名稱
        """
        category = ticket.category or self.categorize_ticket(ticket)
        return self.routing_rules.get(category, "general_support")

    def generate_auto_response(self, ticket: CustomerTicket) -> Optional[str]:
        """
        生成自動回覆（如果適用）

        Args:
            ticket: 客戶工單

        Returns:
            自動回覆文本，如果沒有找到合適的答案則返回 None
        """
        # 使用 RAG 檢索相關的常見問題
        query = f"{ticket.subject} {ticket.description}"
        results = self.rag_retriever.retrieve(query, top_k=1)

        if results and results[0].get('score', 0) > 0.8:  # 高相似度閾值
            # 找到了相關的常見問題答案
            metadata = results[0].get('metadata', {})
            answer = metadata.get('answer', '')

            # 使用 LLM 個性化回覆
            prompt = f"""
            基於以下模板答案，為客戶生成一個友好且個性化的回覆：

            客戶問題：{ticket.subject}
            客戶描述：{ticket.description}

            模板答案：{answer}

            請生成一個專業、友好且有幫助的回覆。
            """

            response = self.llm_client.simple_chat(prompt)
            return response

        return None

    def create_ticket(
        self,
        customer_id: str,
        customer_name: str,
        subject: str,
        description: str,
        channel: str = "email"
    ) -> CustomerTicket:
        """
        創建新工單

        Args:
            customer_id: 客戶 ID
            customer_name: 客戶名稱
            subject: 主題
            description: 描述
            channel: 渠道

        Returns:
            創建的工單
        """
        # 生成工單 ID
        ticket_id = f"TICKET-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # 創建工單
        ticket = CustomerTicket(
            ticket_id=ticket_id,
            customer_id=customer_id,
            customer_name=customer_name,
            subject=subject,
            description=description,
            channel=channel,
            priority=TicketPriority.MEDIUM,
            status=TicketStatus.OPEN,
        )

        # 分析情感
        ticket.sentiment = self.analyze_sentiment(f"{subject} {description}")

        # 分類工單
        ticket.category = self.categorize_ticket(ticket)

        # 確定優先級
        ticket.priority = self.determine_priority(ticket)

        # 路由工單
        ticket.assigned_to = self.route_ticket(ticket)

        # 保存工單
        self.tickets[ticket_id] = ticket

        print(f"\n✅ 工單已創建: {ticket_id}")
        print(f"   分類: {ticket.category}")
        print(f"   優先級: {ticket.priority.name}")
        print(f"   情感: {ticket.sentiment.value}")
        print(f"   分配給: {ticket.assigned_to}")

        # 嘗試生成自動回覆
        auto_response = self.generate_auto_response(ticket)
        if auto_response:
            print(f"\n📧 自動回覆已生成:")
            print(f"{auto_response}")
            ticket.status = TicketStatus.RESOLVED
            ticket.resolved_at = datetime.now()
        else:
            print(f"\n⏳ 工單已轉交給 {ticket.assigned_to} 處理")

        return ticket

    def update_ticket_status(
        self,
        ticket_id: str,
        status: TicketStatus,
        satisfaction: Optional[int] = None
    ):
        """
        更新工單狀態

        Args:
            ticket_id: 工單 ID
            status: 新狀態
            satisfaction: 客戶滿意度評分 (1-5)
        """
        if ticket_id not in self.tickets:
            print(f"❌ 工單 {ticket_id} 不存在")
            return

        ticket = self.tickets[ticket_id]
        ticket.status = status
        ticket.updated_at = datetime.now()

        if status == TicketStatus.RESOLVED or status == TicketStatus.CLOSED:
            ticket.resolved_at = datetime.now()

        if satisfaction:
            ticket.customer_satisfaction = satisfaction

        print(f"✅ 工單 {ticket_id} 已更新為 {status.value}")

    def get_analytics(self) -> Dict[str, Any]:
        """
        獲取客戶服務分析數據

        Returns:
            分析數據字典
        """
        if not self.tickets:
            return {"message": "沒有工單數據"}

        total_tickets = len(self.tickets)
        resolved_tickets = sum(
            1 for t in self.tickets.values()
            if t.status in [TicketStatus.RESOLVED, TicketStatus.CLOSED]
        )

        # 按分類統計
        category_stats = {}
        for ticket in self.tickets.values():
            category = ticket.category or "unknown"
            category_stats[category] = category_stats.get(category, 0) + 1

        # 按優先級統計
        priority_stats = {}
        for ticket in self.tickets.values():
            priority = ticket.priority.name
            priority_stats[priority] = priority_stats.get(priority, 0) + 1

        # 按情感統計
        sentiment_stats = {}
        for ticket in self.tickets.values():
            if ticket.sentiment:
                sentiment = ticket.sentiment.value
                sentiment_stats[sentiment] = sentiment_stats.get(sentiment, 0) + 1

        # 客戶滿意度
        satisfaction_scores = [
            t.customer_satisfaction for t in self.tickets.values()
            if t.customer_satisfaction is not None
        ]
        avg_satisfaction = (
            sum(satisfaction_scores) / len(satisfaction_scores)
            if satisfaction_scores else None
        )

        return {
            "total_tickets": total_tickets,
            "resolved_tickets": resolved_tickets,
            "resolution_rate": f"{(resolved_tickets / total_tickets * 100):.1f}%",
            "category_distribution": category_stats,
            "priority_distribution": priority_stats,
            "sentiment_distribution": sentiment_stats,
            "average_satisfaction": f"{avg_satisfaction:.2f}" if avg_satisfaction else "N/A",
        }


def main():
    """主函數 - 演示客戶服務自動化"""
    print("="*60)
    print("客戶服務自動化系統演示")
    print("="*60)

    # 初始化系統
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ 請設置 OPENAI_API_KEY 環境變量")
        return

    cs_agent = CustomerServiceAgent(api_key=api_key)

    # 測試案例 1: 密碼重置問題（應該自動回覆）
    print("\n" + "="*60)
    print("案例 1: 密碼重置問題")
    print("="*60)

    ticket1 = cs_agent.create_ticket(
        customer_id="CUST001",
        customer_name="John Doe",
        subject="Cannot login to my account",
        description="I forgot my password and cannot access my account. How can I reset it?",
        channel="email"
    )

    # 測試案例 2: 緊急技術問題
    print("\n" + "="*60)
    print("案例 2: 緊急技術問題")
    print("="*60)

    ticket2 = cs_agent.create_ticket(
        customer_id="CUST002",
        customer_name="Jane Smith",
        subject="URGENT: Application crashed and lost my data",
        description="The application crashed while I was working and I lost all my unsaved data. This is critical for my business!",
        channel="chat"
    )

    # 測試案例 3: 帳單問題
    print("\n" + "="*60)
    print("案例 3: 帳單問題")
    print("="*60)

    ticket3 = cs_agent.create_ticket(
        customer_id="CUST003",
        customer_name="Bob Johnson",
        subject="Wrong charge on my credit card",
        description="I was charged twice for the same order. Please refund the duplicate charge.",
        channel="email"
    )

    # 模擬解決工單並獲取客戶反饋
    cs_agent.update_ticket_status(ticket2.ticket_id, TicketStatus.RESOLVED, satisfaction=5)
    cs_agent.update_ticket_status(ticket3.ticket_id, TicketStatus.RESOLVED, satisfaction=4)

    # 顯示分析數據
    print("\n" + "="*60)
    print("客戶服務分析數據")
    print("="*60)

    analytics = cs_agent.get_analytics()
    print(f"\n總工單數: {analytics['total_tickets']}")
    print(f"已解決工單: {analytics['resolved_tickets']}")
    print(f"解決率: {analytics['resolution_rate']}")

    print(f"\n分類分佈:")
    for category, count in analytics['category_distribution'].items():
        print(f"  - {category}: {count}")

    print(f"\n優先級分佈:")
    for priority, count in analytics['priority_distribution'].items():
        print(f"  - {priority}: {count}")

    print(f"\n情感分佈:")
    for sentiment, count in analytics['sentiment_distribution'].items():
        print(f"  - {sentiment}: {count}")

    print(f"\n平均客戶滿意度: {analytics['average_satisfaction']}/5.00")

    print("\n" + "="*60)
    print("演示完成！")
    print("="*60)


if __name__ == "__main__":
    main()
