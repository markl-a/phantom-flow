"""
WebSocket 實時通信工具
WebSocket Real-time Communication Tools

提供 WebSocket 服務器和客戶端功能，支持實時雙向通信。
"""

import asyncio
import json
import inspect
import logging
from typing import Dict, Set, Callable, Any, Optional
from datetime import datetime

# Set up logger for this module
logger = logging.getLogger(__name__)

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False
    WebSocketServerProtocol = object


class WebSocketServer:
    """WebSocket 服務器"""

    # Security constants
    MAX_MESSAGE_SIZE = 1024 * 1024  # 1MB max message size
    OPERATION_TIMEOUT = 30  # 30 seconds timeout for WebSocket operations

    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        """
        初始化 WebSocket 服務器

        Args:
            host: 主機地址
            port: 端口號
        """
        if not HAS_WEBSOCKETS:
            raise ImportError("需要安裝 websockets: pip install websockets")

        self.host = host
        self.port = port
        self.clients: Set[WebSocketServerProtocol] = set()
        self.message_handlers: Dict[str, Callable] = {}
        self.rooms: Dict[str, Set[WebSocketServerProtocol]] = {}

    def on_message(self, message_type: str):
        """
        消息處理器裝飾器

        Args:
            message_type: 消息類型
        """
        def decorator(func: Callable):
            # Validate that handler is an async function
            if not inspect.iscoroutinefunction(func):
                raise TypeError(f"Handler for '{message_type}' must be an async function")
            self.message_handlers[message_type] = func
            return func
        return decorator

    async def handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """
        處理客戶端連接

        Args:
            websocket: WebSocket 連接
            path: 連接路徑
        """
        # 添加客戶端
        self.clients.add(websocket)
        logger.info(f"新客戶端連接: {websocket.remote_address}")

        try:
            async for message in websocket:
                # Validate message size
                if len(message) > self.MAX_MESSAGE_SIZE:
                    await self.send_to_client(websocket, {
                        'type': 'error',
                        'payload': {'message': f'Message too large. Maximum size: {self.MAX_MESSAGE_SIZE} bytes'}
                    })
                    continue

                await self.process_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"客戶端斷開連接: {websocket.remote_address}")
        except asyncio.TimeoutError:
            logger.warning(f"客戶端連接超時: {websocket.remote_address}")
        finally:
            # 移除客戶端
            self.clients.remove(websocket)
            # 從所有房間移除
            for room_clients in self.rooms.values():
                room_clients.discard(websocket)

    async def process_message(self, websocket: WebSocketServerProtocol, message: str):
        """
        處理接收到的消息

        Args:
            websocket: WebSocket 連接
            message: 消息內容
        """
        try:
            data = json.loads(message)
            message_type = data.get('type', 'unknown')
            payload = data.get('payload', {})

            # 調用對應的消息處理器
            if message_type in self.message_handlers:
                handler = self.message_handlers[message_type]
                response = await handler(websocket, payload)

                if response:
                    await self.send_to_client(websocket, response)
            else:
                await self.send_to_client(websocket, {
                    'type': 'error',
                    'payload': {'message': f'Unknown message type: {message_type}'}
                })

        except json.JSONDecodeError:
            await self.send_to_client(websocket, {
                'type': 'error',
                'payload': {'message': 'Invalid JSON'}
            })
        except Exception as e:
            await self.send_to_client(websocket, {
                'type': 'error',
                'payload': {'message': str(e)}
            })

    async def send_to_client(
        self,
        websocket: WebSocketServerProtocol,
        message: Dict[str, Any]
    ):
        """
        發送消息到單個客戶端

        Args:
            websocket: WebSocket 連接
            message: 消息字典
        """
        try:
            await asyncio.wait_for(
                websocket.send(json.dumps(message)),
                timeout=self.OPERATION_TIMEOUT
            )
        except asyncio.TimeoutError:
            print(f"發送消息超時: {websocket.remote_address}")
        except Exception as e:
            print(f"發送消息失敗: {e}")

    async def broadcast(self, message: Dict[str, Any], exclude: Optional[WebSocketServerProtocol] = None):
        """
        廣播消息到所有客戶端

        Args:
            message: 消息字典
            exclude: 排除的客戶端
        """
        message_json = json.dumps(message)
        tasks = [
            asyncio.wait_for(
                client.send(message_json),
                timeout=self.OPERATION_TIMEOUT
            )
            for client in self.clients
            if client != exclude
        ]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def broadcast_to_room(self, room: str, message: Dict[str, Any]):
        """
        廣播消息到房間內的所有客戶端

        Args:
            room: 房間名稱
            message: 消息字典
        """
        if room not in self.rooms:
            return

        message_json = json.dumps(message)
        tasks = [
            asyncio.wait_for(
                client.send(message_json),
                timeout=self.OPERATION_TIMEOUT
            )
            for client in self.rooms[room]
        ]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def join_room(self, websocket: WebSocketServerProtocol, room: str):
        """
        客戶端加入房間

        Args:
            websocket: WebSocket 連接
            room: 房間名稱
        """
        if room not in self.rooms:
            self.rooms[room] = set()
        self.rooms[room].add(websocket)

    def leave_room(self, websocket: WebSocketServerProtocol, room: str):
        """
        客戶端離開房間

        Args:
            websocket: WebSocket 連接
            room: 房間名稱
        """
        if room in self.rooms:
            self.rooms[room].discard(websocket)

    async def start(self):
        """啟動 WebSocket 服務器"""
        async with websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            max_size=self.MAX_MESSAGE_SIZE,
            ping_timeout=self.OPERATION_TIMEOUT
        ):
            print(f"🚀 WebSocket 服務器啟動: ws://{self.host}:{self.port}")
            await asyncio.Future()  # 運行永久


class WebSocketClient:
    """WebSocket 客戶端"""

    # Security constants
    MAX_MESSAGE_SIZE = 1024 * 1024  # 1MB max message size
    OPERATION_TIMEOUT = 30  # 30 seconds timeout for WebSocket operations

    def __init__(self, uri: str):
        """
        初始化 WebSocket 客戶端

        Args:
            uri: WebSocket 服務器 URI
        """
        if not HAS_WEBSOCKETS:
            raise ImportError("需要安裝 websockets: pip install websockets")

        self.uri = uri
        self.websocket = None
        self.message_handlers: Dict[str, Callable] = {}

    def on_message(self, message_type: str):
        """
        消息處理器裝飾器

        Args:
            message_type: 消息類型
        """
        def decorator(func: Callable):
            # Validate that handler is an async function
            if not inspect.iscoroutinefunction(func):
                raise TypeError(f"Handler for '{message_type}' must be an async function")
            self.message_handlers[message_type] = func
            return func
        return decorator

    async def connect(self):
        """連接到 WebSocket 服務器"""
        self.websocket = await asyncio.wait_for(
            websockets.connect(
                self.uri,
                max_size=self.MAX_MESSAGE_SIZE,
                ping_timeout=self.OPERATION_TIMEOUT
            ),
            timeout=self.OPERATION_TIMEOUT
        )
        print(f"✅ 已連接到服務器: {self.uri}")

    async def send(self, message_type: str, payload: Dict[str, Any]):
        """
        發送消息

        Args:
            message_type: 消息類型
            payload: 消息負載
        """
        if not self.websocket:
            raise ConnectionError("未連接到服務器")

        message = {
            'type': message_type,
            'payload': payload,
            'timestamp': datetime.now().isoformat()
        }
        message_json = json.dumps(message)

        # Validate message size
        if len(message_json) > self.MAX_MESSAGE_SIZE:
            raise ValueError(f"Message too large. Maximum size: {self.MAX_MESSAGE_SIZE} bytes")

        await asyncio.wait_for(
            self.websocket.send(message_json),
            timeout=self.OPERATION_TIMEOUT
        )

    async def receive(self):
        """接收並處理消息"""
        if not self.websocket:
            raise ConnectionError("未連接到服務器")

        async for message in self.websocket:
            try:
                # Validate message size
                if len(message) > self.MAX_MESSAGE_SIZE:
                    logger.warning(f"接收到的消息過大，已忽略。最大大小: {self.MAX_MESSAGE_SIZE} 字節")
                    continue

                data = json.loads(message)
                message_type = data.get('type', 'unknown')
                payload = data.get('payload', {})

                # 調用對應的消息處理器
                if message_type in self.message_handlers:
                    handler = self.message_handlers[message_type]
                    await handler(payload)
                else:
                    print(f"未處理的消息類型: {message_type}")

            except json.JSONDecodeError:
                print(f"無效的 JSON: {message}")
            except Exception as e:
                print(f"處理消息錯誤: {e}")

    async def close(self):
        """關閉連接"""
        if self.websocket:
            await asyncio.wait_for(
                self.websocket.close(),
                timeout=self.OPERATION_TIMEOUT
            )
            print("❌ 已斷開連接")


# 示例：聊天服務器
class ChatServer(WebSocketServer):
    """聊天服務器示例"""

    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        super().__init__(host, port)
        self.setup_handlers()

    def setup_handlers(self):
        """設置消息處理器"""

        @self.on_message('join')
        async def handle_join(websocket, payload):
            room = payload.get('room', 'general')
            username = payload.get('username', 'Anonymous')

            self.join_room(websocket, room)

            # 通知房間內的其他人
            await self.broadcast_to_room(room, {
                'type': 'user_joined',
                'payload': {
                    'username': username,
                    'room': room,
                    'timestamp': datetime.now().isoformat()
                }
            })

            return {
                'type': 'joined',
                'payload': {
                    'room': room,
                    'message': f'歡迎來到 {room} 房間！'
                }
            }

        @self.on_message('message')
        async def handle_message(websocket, payload):
            room = payload.get('room', 'general')
            username = payload.get('username', 'Anonymous')
            message = payload.get('message', '')

            # 廣播消息到房間
            await self.broadcast_to_room(room, {
                'type': 'message',
                'payload': {
                    'username': username,
                    'message': message,
                    'room': room,
                    'timestamp': datetime.now().isoformat()
                }
            })

        @self.on_message('leave')
        async def handle_leave(websocket, payload):
            room = payload.get('room', 'general')
            username = payload.get('username', 'Anonymous')

            self.leave_room(websocket, room)

            # 通知房間內的其他人
            await self.broadcast_to_room(room, {
                'type': 'user_left',
                'payload': {
                    'username': username,
                    'room': room,
                    'timestamp': datetime.now().isoformat()
                }
            })


__all__ = ['WebSocketServer', 'WebSocketClient', 'ChatServer']
