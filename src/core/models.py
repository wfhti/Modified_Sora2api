"""Data models"""
from datetime import datetime
from typing import Optional, List, Union
from pydantic import BaseModel

class Token(BaseModel):
    """Token model"""
    id: Optional[int] = None
    token: str
    email: str
    name: Optional[str] = ""
    st: Optional[str] = None
    rt: Optional[str] = None
    client_id: Optional[str] = None
    remark: Optional[str] = None
    expiry_time: Optional[datetime] = None
    is_active: bool = True
    cooled_until: Optional[datetime] = None
    created_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    use_count: int = 0
    # 订阅信息
    plan_type: Optional[str] = None  # 账户类型，如 chatgpt_team
    plan_title: Optional[str] = None  # 套餐名称，如 ChatGPT Business
    subscription_end: Optional[datetime] = None  # 套餐到期时间
    # Sora2 支持信息
    sora2_supported: Optional[bool] = None  # 是否支持Sora2
    sora2_invite_code: Optional[str] = None  # Sora2邀请码
    sora2_redeemed_count: int = 0  # Sora2已用次数
    sora2_total_count: int = 0  # Sora2总次数
    # Sora2 剩余次数
    sora2_remaining_count: int = 0  # Sora2剩余可用次数
    sora2_cooldown_until: Optional[datetime] = None  # Sora2冷却时间
    # 功能开关
    image_enabled: bool = True  # 是否启用图片生成
    video_enabled: bool = True  # 是否启用视频生成
    # 并发限制
    image_concurrency: int = -1  # 图片并发数限制，-1表示不限制
    video_concurrency: int = -1  # 视频并发数限制，-1表示不限制

class TokenStats(BaseModel):
    """Token statistics"""
    id: Optional[int] = None
    token_id: int
    image_count: int = 0
    video_count: int = 0
    error_count: int = 0  # Historical total errors (never reset)
    last_error_at: Optional[datetime] = None
    today_image_count: int = 0
    today_video_count: int = 0
    today_error_count: int = 0
    today_date: Optional[str] = None
    consecutive_error_count: int = 0  # Consecutive errors for auto-disable

class Task(BaseModel):
    """Task model"""
    id: Optional[int] = None
    task_id: str
    token_id: int
    model: str
    prompt: str
    status: str = "processing"  # processing/completed/failed
    progress: float = 0.0
    result_urls: Optional[str] = None  # JSON array
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class Character(BaseModel):
    """Character (角色卡) model"""
    id: Optional[int] = None
    cameo_id: str  # Sora cameo ID (e.g., 693afd1c8848819183981970eea64a31)
    character_id: Optional[str] = None  # Sora character ID
    token_id: int  # Associated token ID
    username: str  # Character username
    display_name: str  # Character display name
    profile_url: Optional[str] = None  # Profile image URL
    instruction_set: Optional[str] = None  # JSON string of instruction_set
    safety_instruction_set: Optional[str] = None  # JSON string of safety_instruction_set
    visibility: str = "private"  # private/public
    status: str = "finalized"  # processing/finalized/deleted
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class RequestLog(BaseModel):
    """Request log model"""
    id: Optional[int] = None
    token_id: Optional[int] = None
    operation: str
    request_body: Optional[str] = None
    response_body: Optional[str] = None
    status_code: int
    duration: float
    created_at: Optional[datetime] = None

class AdminConfig(BaseModel):
    """Admin configuration"""
    id: int = 1
    admin_username: str  # Read from database, initialized from setting.toml on first startup
    admin_password: str  # Read from database, initialized from setting.toml on first startup
    error_ban_threshold: int = 3
    updated_at: Optional[datetime] = None

class ProxyConfig(BaseModel):
    """Proxy configuration"""
    id: int = 1
    proxy_enabled: bool  # Read from database, initialized from setting.toml on first startup
    proxy_url: Optional[str] = None  # Read from database, initialized from setting.toml on first startup
    proxy_pool_enabled: bool = False  # Enable proxy pool rotation from data/proxy.txt
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class WatermarkFreeConfig(BaseModel):
    """Watermark-free mode configuration"""
    id: int = 1
    watermark_free_enabled: bool  # Read from database, initialized from setting.toml on first startup
    parse_method: str  # Read from database, initialized from setting.toml on first startup
    custom_parse_url: Optional[str] = None  # Read from database, initialized from setting.toml on first startup
    custom_parse_token: Optional[str] = None  # Read from database, initialized from setting.toml on first startup
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class CacheConfig(BaseModel):
    """Cache configuration"""
    id: int = 1
    cache_enabled: bool  # Read from database, initialized from setting.toml on first startup
    cache_timeout: int  # Read from database, initialized from setting.toml on first startup
    cache_base_url: Optional[str] = None  # Read from database, initialized from setting.toml on first startup
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class GenerationConfig(BaseModel):
    """Generation timeout configuration"""
    id: int = 1
    image_timeout: int  # Read from database, initialized from setting.toml on first startup
    video_timeout: int  # Read from database, initialized from setting.toml on first startup
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class TokenRefreshConfig(BaseModel):
    """Token refresh configuration"""
    id: int = 1
    at_auto_refresh_enabled: bool  # Read from database, initialized from setting.toml on first startup
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class WebDAVConfig(BaseModel):
    """WebDAV configuration"""
    id: int = 1
    webdav_enabled: bool = False
    webdav_url: Optional[str] = None
    webdav_username: Optional[str] = None
    webdav_password: Optional[str] = None
    webdav_upload_path: str = "/video"  # Default upload path
    auto_delete_enabled: bool = False  # Auto delete after specified days
    auto_delete_days: int = 30  # Days to keep files
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class VideoRecord(BaseModel):
    """Video record for WebDAV uploaded videos"""
    id: Optional[int] = None
    task_id: str  # Associated task ID
    token_id: int  # Associated token ID
    original_url: str  # Original video URL (with watermark)
    watermark_free_url: Optional[str] = None  # Watermark-free video URL
    webdav_path: Optional[str] = None  # Path on WebDAV server
    webdav_url: Optional[str] = None  # Full WebDAV access URL
    file_size: Optional[int] = None  # File size in bytes
    status: str = "pending"  # pending/uploading/uploaded/failed/deleted
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    uploaded_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

class UploadLog(BaseModel):
    """Upload log for WebDAV operations"""
    id: Optional[int] = None
    video_record_id: Optional[int] = None
    operation: str  # upload/delete/list
    status: str  # success/failed
    message: Optional[str] = None
    duration: Optional[float] = None  # Operation duration in seconds
    created_at: Optional[datetime] = None

# API Request/Response models
class ChatMessage(BaseModel):
    role: str
    content: Union[str, List[dict]]  # Support both string and array format (OpenAI multimodal)

class CharacterOptions(BaseModel):
    """Character creation options"""
    timestamps: Optional[str] = None  # e.g., "0,3" - video timestamps for character extraction
    username: Optional[str] = None  # Custom username for character
    display_name: Optional[str] = None  # Custom display name for character
    instruction_set: Optional[str] = None  # Character instruction set
    safety_instruction_set: Optional[str] = None  # Safety instruction set

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    image: Optional[str] = None
    video: Optional[str] = None  # Base64 encoded video file
    remix_target_id: Optional[str] = None  # Sora share link video ID for remix
    stream: bool = False
    max_tokens: Optional[int] = None
    # Character creation options
    character_options: Optional[CharacterOptions] = None
    # Video style (festive, retro, news, selfie, handheld, anime)
    style_id: Optional[str] = None

class ChatCompletionChoice(BaseModel):
    index: int
    message: Optional[dict] = None
    delta: Optional[dict] = None
    finish_reason: Optional[str] = None

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
