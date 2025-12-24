"""Proxy management module"""
from typing import Optional, List
from pathlib import Path
import asyncio
from ..core.database import Database
from ..core.models import ProxyConfig

class ProxyManager:
    """Proxy configuration manager with pool rotation support"""
    
    def __init__(self, db: Database):
        self.db = db
        self._proxy_pool: List[str] = []
        self._pool_index: int = 0
        self._pool_lock = asyncio.Lock()
        self._proxy_file_path = Path(__file__).parent.parent.parent / "data" / "proxy.txt"
    
    def _load_proxy_pool(self) -> List[str]:
        """Load proxy list from data/proxy.txt"""
        proxies = []
        if self._proxy_file_path.exists():
            try:
                with open(self._proxy_file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            proxies.append(line)
            except Exception as e:
                print(f"⚠️ Failed to load proxy pool: {e}")
        return proxies
    
    async def get_proxy_url(self) -> Optional[str]:
        """Get proxy URL if enabled, with pool rotation support"""
        config = await self.db.get_proxy_config()
        
        if not config.proxy_enabled:
            return None
        
        # If proxy pool is enabled, rotate through proxies
        if config.proxy_pool_enabled:
            async with self._pool_lock:
                # Reload proxy pool if empty
                if not self._proxy_pool:
                    self._proxy_pool = self._load_proxy_pool()
                
                if self._proxy_pool:
                    # Get current proxy and rotate index
                    proxy = self._proxy_pool[self._pool_index]
                    self._pool_index = (self._pool_index + 1) % len(self._proxy_pool)
                    return proxy
                else:
                    # Fallback to single proxy if pool is empty
                    return config.proxy_url if config.proxy_url else None
        
        # Use single proxy
        return config.proxy_url if config.proxy_url else None
    
    async def update_proxy_config(self, enabled: bool, proxy_url: Optional[str], proxy_pool_enabled: bool = False):
        """Update proxy configuration"""
        await self.db.update_proxy_config(enabled, proxy_url, proxy_pool_enabled)
        
        # Reset proxy pool when config changes
        async with self._pool_lock:
            self._proxy_pool = []
            self._pool_index = 0
    
    async def get_proxy_config(self) -> ProxyConfig:
        """Get proxy configuration"""
        return await self.db.get_proxy_config()
    
    async def get_proxy_pool_count(self) -> int:
        """Get the number of proxies in the pool"""
        proxies = self._load_proxy_pool()
        return len(proxies)
    
    async def reload_proxy_pool(self):
        """Force reload proxy pool from file"""
        async with self._pool_lock:
            self._proxy_pool = self._load_proxy_pool()
            self._pool_index = 0
        return len(self._proxy_pool)
