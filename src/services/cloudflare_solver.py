"""Cloudflare Solver - Unified Cloudflare challenge handling with global state"""
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
from ..core.config import config


class CloudflareState:
    """全局 Cloudflare 状态管理器
    
    维护全局共享的 cf_clearance cookies 和 user_agent，
    所有请求都使用相同的凭据，直到遇到新的 429 challenge。
    """
    
    def __init__(self):
        self._cookies: Dict[str, str] = {}
        self._user_agent: Optional[str] = None
        self._last_updated: Optional[datetime] = None
        self._lock = asyncio.Lock()
    
    @property
    def cookies(self) -> Dict[str, str]:
        """获取当前的 Cloudflare cookies"""
        return self._cookies.copy()
    
    @property
    def user_agent(self) -> Optional[str]:
        """获取当前的 User-Agent"""
        return self._user_agent
    
    @property
    def is_valid(self) -> bool:
        """检查是否有有效的 Cloudflare 凭据"""
        return bool(self._cookies) and self._user_agent is not None
    
    @property
    def last_updated(self) -> Optional[datetime]:
        """获取最后更新时间"""
        return self._last_updated
    
    async def update(self, cookies: Dict[str, str], user_agent: str):
        """更新 Cloudflare 凭据
        
        Args:
            cookies: 新的 cookies 字典
            user_agent: 新的 User-Agent
        """
        async with self._lock:
            self._cookies = cookies.copy()
            self._user_agent = user_agent
            self._last_updated = datetime.now()
            print(f"✅ 全局 Cloudflare 凭据已更新 (cookies: {list(cookies.keys())}, ua: {user_agent[:50]}...)")
    
    async def clear(self):
        """清除 Cloudflare 凭据"""
        async with self._lock:
            self._cookies = {}
            self._user_agent = None
            self._last_updated = None
            print("🗑️ 全局 Cloudflare 凭据已清除")
    
    def apply_to_session(self, session, domain: str = ".sora.chatgpt.com"):
        """将 cookies 应用到 session
        
        Args:
            session: curl_cffi AsyncSession 实例
            domain: cookie 域名
        """
        for name, value in self._cookies.items():
            session.cookies.set(name, value, domain=domain)
    
    def get_headers_update(self) -> Dict[str, str]:
        """获取需要更新的请求头
        
        Returns:
            包含 User-Agent 的字典（如果有）
        """
        if self._user_agent:
            return {"User-Agent": self._user_agent}
        return {}


# 全局单例
_cf_state = CloudflareState()


def get_cloudflare_state() -> CloudflareState:
    """获取全局 Cloudflare 状态管理器"""
    return _cf_state


async def solve_cloudflare_challenge(proxy_url: Optional[str] = None, max_retries: int = 3) -> Optional[Dict[str, Any]]:
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
        print("⚠️ Cloudflare Solver API 未配置，请在配置文件中设置 cloudflare_solver_enabled 和 cloudflare_solver_api_url")
        return None
    
    api_url = config.cloudflare_solver_api_url
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"🔄 调用 Cloudflare Solver API: {api_url} (尝试 {attempt}/{max_retries})")
            
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.get(api_url)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        cookies = data.get("cookies", {})
                        user_agent = data.get("user_agent")
                        print(f"✅ Cloudflare Solver API 返回成功，耗时 {data.get('elapsed_seconds', 0):.2f}s")
                        
                        # 更新全局状态
                        if cookies and user_agent:
                            await _cf_state.update(cookies, user_agent)
                        
                        return {"cookies": cookies, "user_agent": user_agent}
                    else:
                        print(f"⚠️ Cloudflare Solver API 返回失败: {data.get('error')}")
                else:
                    print(f"⚠️ Cloudflare Solver API 请求失败: {response.status_code}")
                    
        except Exception as e:
            print(f"⚠️ Cloudflare Solver API 调用失败: {e}")
        
        # 如果不是最后一次尝试，等待后重试
        if attempt < max_retries:
            wait_time = attempt * 2  # 2s, 4s
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
        "cf-mitigated" in str(headers) or
        "Just a moment" in response_text or
        "challenge-platform" in response_text
    )
