"""Tool implementations for agents."""

# Common Tools
from ai_automation_framework.tools.common_tools import (
    WebSearchTool,
    CalculatorTool,
    FileSystemTool,
    DateTimeTool,
    DataProcessingTool,
    TOOL_SCHEMAS,
    TOOL_REGISTRY
)

# Document Loaders
from ai_automation_framework.tools.document_loaders import (
    BaseDocumentLoader,
    TextLoader,
    PDFLoader,
    DocxLoader,
    MarkdownLoader,
    DirectoryLoader,
    load_document
)

# Advanced Automation
from ai_automation_framework.tools.advanced_automation import (
    EmailAutomationTool,
    DatabaseAutomationTool,
    WebScraperTool,
)

# Data Processing
from ai_automation_framework.tools.data_processing import (
    ExcelAutomationTool,
    CSVProcessingTool,
    DataAnalysisTool,
)

# Scheduler and Testing
from ai_automation_framework.tools.scheduler_and_testing import (
    TaskScheduler,
    APITestingTool,
)

# Media and Messaging
from ai_automation_framework.tools.media_messaging import (
    ImageProcessingTool,
    OCRTool,
    SlackTool,
    DiscordTool,
)

# DevOps and Cloud
from ai_automation_framework.tools.devops_cloud import (
    GitAutomationTool,
    CloudStorageTool,
    BrowserAutomationTool,
    PDFAdvancedTool,
)

# AI Development Assistant
from ai_automation_framework.tools.ai_dev_assistant import (
    AICodeReviewer,
    AIDebugAssistant,
    AIDocGenerator,
    AITestGenerator,
    AIRefactoringAssistant,
)

# Performance Monitoring
from ai_automation_framework.tools.performance_monitoring import (
    PerformanceMetrics,
    PerformanceMonitor,
    ResourceOptimizer,
    PerformanceProfiler,
    HealthChecker,
)

# Video Processing
from ai_automation_framework.tools.video_processing import (
    VideoProcessor,
)

# Audio Processing
from ai_automation_framework.tools.audio_processing import (
    SpeechToText,
    TextToSpeech,
)

# GraphQL API
from ai_automation_framework.tools.graphql_api import (
    GraphQLServer,
    GraphQLClient,
)

# WebSocket
from ai_automation_framework.tools.websocket_server import (
    WebSocketServer,
    WebSocketClient,
    ChatServer,
)


__all__ = [
    # Common Tools
    "WebSearchTool",
    "CalculatorTool",
    "FileSystemTool",
    "DateTimeTool",
    "DataProcessingTool",
    "TOOL_SCHEMAS",
    "TOOL_REGISTRY",
    # Document Loaders
    "BaseDocumentLoader",
    "TextLoader",
    "PDFLoader",
    "DocxLoader",
    "MarkdownLoader",
    "DirectoryLoader",
    "load_document",
    # Advanced Automation
    "EmailAutomationTool",
    "DatabaseAutomationTool",
    "WebScraperTool",
    # Data Processing
    "ExcelAutomationTool",
    "CSVProcessingTool",
    "DataAnalysisTool",
    # Scheduler and Testing
    "TaskScheduler",
    "APITestingTool",
    # Media and Messaging
    "ImageProcessingTool",
    "OCRTool",
    "SlackTool",
    "DiscordTool",
    # DevOps and Cloud
    "GitAutomationTool",
    "CloudStorageTool",
    "BrowserAutomationTool",
    "PDFAdvancedTool",
    # AI Development Assistant
    "AICodeReviewer",
    "AIDebugAssistant",
    "AIDocGenerator",
    "AITestGenerator",
    "AIRefactoringAssistant",
    # Performance Monitoring
    "PerformanceMetrics",
    "PerformanceMonitor",
    "ResourceOptimizer",
    "PerformanceProfiler",
    "HealthChecker",
    # Video Processing
    "VideoProcessor",
    # Audio Processing
    "SpeechToText",
    "TextToSpeech",
    # GraphQL API
    "GraphQLServer",
    "GraphQLClient",
    # WebSocket
    "WebSocketServer",
    "WebSocketClient",
    "ChatServer",
]
