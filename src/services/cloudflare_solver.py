"""Cloudflare Solver - Unified Cloudflare challenge handling with global state"""
import asyncio
import threading
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from ..core.config import config


class CloudflareState:
    """全局 Cloudflare 状态管理器
    
    维护全局共享的 cf_clearance cookies 和 user_agent，
    所有请求都使用相同的凭据，直到遇到新的 429 challenge 或凭据过期。
    
    特性：
    - 线程安全（使用 threading.Lock）
    - 凭据有效期 10 分钟，自动过期
    - 遇到 429/403 时自动标记凭据无效
    """
    
    # 凭据有效期（秒）
    CREDENTIAL_TTL = 600  # 10 分钟
    
    def __init__(self):
        self._cookies: Dict[str, str] = {}
        self._user_agent: Optional[str] = None
        self._last_updated: Optional[datetime] = None
        self._is_valid: bool = False
        self._lock = threading.Lock()
    
    @property
    def cookies(self) -> Dict[str, str]:
        """获取当前的 Cloudflare cookies"""
        with self._lock:
            if not self._check_validity():
                return {}
            return self._cookies.copy()
    
    @property
    def user_agent(self) -> Optional[str]:
        """获取当前的 User-Agent"""
        with self._lock:
            if not self._check_validity():
                return None
            return self._user_agent
    
    @property
    def is_valid(self) -> bool:
        """检查是否有有效的 Cloudflare 凭据"""
        with self._lock:
            return self._check_validity()
    
    @property
    def last_updated(self) -> Optional[datetime]:
        """获取最后更新时间"""
        with self._lock:
            return self._last_updated
    
    @property
    def expires_at(self) -> Optional[datetime]:
        """获取凭据过期时间"""
        with self._lock:
            if self._last_updated:
                return self._last_updated + timedelta(seconds=self.CREDENTIAL_TTL)
            return None
    
    @property
    def remaining_seconds(self) -> int:
        """获取剩余有效时间（秒）"""
        with self._lock:
            if not self._last_updated or not self._is_valid:
                return 0
            expires = self._last_updated + timedelta(seconds=self.CREDENTIAL_TTL)
            remaining = (expires - datetime.now()).total_seconds()
            return max(0, int(remaining))
    
    def _check_validity(self) -> bool:
        """检查凭据是否有效（内部方法，不加锁）"""
        if not self._is_valid or not self._cookies or not self._user_agent:
            return False
        if not self._last_updated:
            return False
        # 检查是否过期
        expires = self._last_updated + timedelta(seconds=self.CREDENTIAL_TTL)
        if datetime.now() > expires:
            self._is_valid = False
            return False
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前状态信息"""
        with self._lock:
            is_valid = self._check_validity()
            return {
                "is_valid": is_valid,
                "has_credentials": bool(self._cookies) and bool(self._user_agent),
                "last_updated": self._last_updated.isoformat() if self._last_updated else None,
                "expires_at": (self._last_updated + timedelta(seconds=self.CREDENTIAL_TTL)).isoformat() if self._last_updated else None,
                "remaining_seconds": self.remaining_seconds if is_valid else 0,
                "cookies_count": len(self._cookies),
                "user_agent": self._user_agent[:50] + "..." if self._user_agent and len(self._user_agent) > 50 else self._user_agent,
            }
    
    def update(self, cookies: Dict[str, str], user_agent: str):
        """更新 Cloudflare 凭据（同步方法）
        
        Args:
            cookies: 新的 cookies 字典
            user_agent: 新的 User-Agent
        """
        with self._lock:
            self._cookies = cookies.copy()
            self._user_agent = user_agent
            self._last_updated = datetime.now()
            self._is_valid = True
            print(f"✅ 全局 Cloudflare 凭据已更新 (cookies: {list(cookies.keys())}, ua: {user_agent[:50]}...)")
    
    async def update_async(self, cookies: Dict[str, str], user_agent: str):
        """更新 Cloudflare 凭据（异步方法）"""
        self.update(cookies, user_agent)
    
    def invalidate(self):
        """标记凭据无效（遇到 429/403 时调用）"""
        with self._lock:
            self._is_valid = False
            print("⚠️ Cloudflare 凭据已标记为无效")
    
    def clear(self):
        """清除 Cloudflare 凭据（同步方法）"""
        with self._lock:
            self._cookies = {}
            self._user_agent = None
            self._last_updated = None
            self._is_valid = False
            print("🗑️ 全局 Cloudflare 凭据已清除")
    
    async def clear_async(self):
        """清除 Cloudflare 凭据（异步方法）"""
        self.clear()
    
    def apply_to_session(self, session, domain: str = ".sora.chatgpt.com"):
        """将 cookies 应用到 session
        
        Args:
            session: curl_cffi AsyncSession 实例
            domain: cookie 域名
        """
        with self._lock:
            if not self._check_validity():
                return
            for name, value in self._cookies.items():
                session.cookies.set(name, value, domain=domain)
    
    def get_headers_update(self) -> Dict[str, str]:
        """获取需要更新的请求头
        
        Returns:
            包含 User-Agent 的字典（如果有）
        """
        with self._lock:
            if self._check_validity() and self._user_agent:
                return {"User-Agent": self._user_agent}
            return {}


# 全局单例
_cf_state = CloudflareState()


def get_cloudflare_state() -> CloudflareState:
    """获取全局 Cloudflare 状态管理器"""
    return _cf_state


async def solve_cloudflare_challenge(
    proxy_url: Optional[str] = None, max_retries: int = 3
) -> Optional[Dict[str, Any]]:
    """解决 Cloudflare challenge 并更新全局状态
    
    使用配置的 Cloudflare Solver API，最多重试指定次数。
    成功后会自动更新全局 Cloudflare 状态。
    
    Args:
        proxy_url: 代理 URL（当前未使用，保留接口兼容性）
        max_retries: 最大重试次数
        
    Returns:
        包含 cookies 和 user_agent 的字典，如 {"cookies": {...}, "user_agent": "..."}
        失败返回 None
    """
    import httpx
    
    if not config.cloudflare_solver_enabled or not config.cloudflare_solver_api_url:
        print("⚠️ Cloudflare Solver API 未配置")
        return None
    
    api_url = config.cloudflare_solver_api_url
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"🔄 调用 Cloudflare Solver API: {api_url} (尝试 {attempt}/{max_retries})")
            
            # 使用更细粒度的超时设置：连接超时10秒，读取超时120秒
            timeout = httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=10.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(api_url)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        cookies = data.get("cookies", {})
                        user_agent = data.get("user_agent")
                        elapsed = data.get("elapsed_seconds", 0)
                        print(f"✅ Cloudflare Solver API 返回成功，耗时 {elapsed:.2f}s")
                        
                        # 更新全局状态
                        if cookies and user_agent:
                            _cf_state.update(cookies, user_agent)
                        
                        return {"cookies": cookies, "user_agent": user_agent}
                    else:
                        print(f"⚠️ Cloudflare Solver API 返回失败: {data.get('error')}")
                else:
                    print(f"⚠️ Cloudflare Solver API 请求失败: {response.status_code}")
        
        except httpx.ConnectError as e:
            print(f"⚠️ Cloudflare Solver API 连接失败: {e}")
            # 连接失败时不重试，直接返回
            return None
        except httpx.ConnectTimeout as e:
            print(f"⚠️ Cloudflare Solver API 连接超时: {e}")
            # 连接超时时不重试，直接返回
            return None
        except Exception as e:
            print(f"⚠️ Cloudflare Solver API 调用失败: {e}")
        
        # 如果不是最后一次尝试，等待后重试
        if attempt < max_retries:
            wait_time = attempt * 2
            print(f"⏳ 等待 {wait_time}s 后重试...")
            await asyncio.sleep(wait_time)
    
    print(f"❌ Cloudflare Solver API 调用失败，已重试 {max_retries} 次")
    return None


def is_cloudflare_challenge(status_code: int, headers: dict, response_text: str) -> bool:
    """检测响应是否为 Cloudflare challenge
    
    Args:
        status_code: HTTP 状态码
        headers: 响应头
        response_text: 响应文本
    
    Returns:
        True 如果是 Cloudflare challenge
    """
    if status_code not in [429, 403]:
        return False
    
    return (
        "cf-mitigated" in str(headers)
        or "Just a moment" in response_text
        or "challenge-platform" in response_text
    )
