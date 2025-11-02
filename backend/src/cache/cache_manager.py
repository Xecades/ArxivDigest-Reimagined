"""Cache manager for storing and retrieving filtered papers across stages."""

import hashlib
import json
from pathlib import Path
from typing import Any

from diskcache import Cache
from loguru import logger


class CacheManager:
    """
    Manages caching of paper filtering results across stages.

    Uses diskcache for persistent storage with automatic expiration and
    size management. Supports separate caches for each stage and custom
    cache keys based on configuration.
    """

    def __init__(
        self,
        cache_dir: str = ".cache",
        size_limit: int = 1024 * 1024 * 1024,  # 1GB default
        expire_days: int = 30,
    ):
        """
        Initialize the cache manager.

        Args:
            cache_dir: Directory to store cache files
            size_limit: Maximum cache size in bytes
            expire_days: Days until cache entries expire
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Separate caches for each stage
        self.stage1_cache = Cache(
            str(self.cache_dir / "stage1"),
            size_limit=size_limit // 4,
        )
        self.stage2_cache = Cache(
            str(self.cache_dir / "stage2"),
            size_limit=size_limit // 4,
        )
        self.stage3_cache = Cache(
            str(self.cache_dir / "stage3"),
            size_limit=size_limit // 4,
        )
        self.highlight_cache = Cache(
            str(self.cache_dir / "highlight"),
            size_limit=size_limit // 4,
        )

        self.expire_seconds = expire_days * 24 * 3600

        logger.info(
            f"Cache manager initialized at {cache_dir} "
            f"(size_limit={size_limit / 1024 / 1024:.0f}MB, "
            f"expire_days={expire_days})"
        )

    def _get_cache_by_stage(self, stage: int | str) -> Cache:
        """Get the cache object for a specific stage."""
        if stage == 1 or stage == "stage1":
            return self.stage1_cache
        elif stage == 2 or stage == "stage2":
            return self.stage2_cache
        elif stage == 3 or stage == "stage3":
            return self.stage3_cache
        elif stage == "highlight":
            return self.highlight_cache
        else:
            raise ValueError(f"Invalid stage: {stage}, must be 1, 2, 3, or 'highlight'")

    def _generate_key(self, paper_id: str, config_hash: str | None = None) -> str:
        """
        Generate a cache key for a paper.

        Args:
            paper_id: arXiv paper ID (e.g., "2503.10630v3")
            config_hash: Hash of the configuration (to invalidate cache when config changes)

        Returns:
            Cache key string
        """
        if config_hash:
            return f"{paper_id}:{config_hash}"
        return paper_id

    def hash_config(self, config: dict) -> str:
        """
        Generate a hash from configuration dict.

        Args:
            config: Configuration dictionary

        Returns:
            Hash string (first 8 characters of SHA256)
        """
        # Sort keys to ensure consistent hashing
        config_str = json.dumps(config, sort_keys=True)
        hash_obj = hashlib.sha256(config_str.encode())
        return hash_obj.hexdigest()[:8]

    def get(
        self,
        stage: int | str,
        paper_id: str,
        config_hash: str | None = None,
    ) -> Any | None:
        """
        Retrieve cached result for a paper.

        Args:
            stage: Stage number (1, 2, 3) or 'highlight'
            paper_id: arXiv paper ID
            config_hash: Optional configuration hash

        Returns:
            Cached result or None if not found
        """
        cache = self._get_cache_by_stage(stage)
        key = self._generate_key(paper_id, config_hash)

        result = cache.get(key)
        if result is not None:
            logger.debug(f"Cache HIT: {stage}/{key}")
        else:
            logger.debug(f"Cache MISS: {stage}/{key}")

        return result

    def set(
        self,
        stage: int | str,
        paper_id: str,
        result: Any,
        config_hash: str | None = None,
    ) -> None:
        """
        Store result in cache.

        Args:
            stage: Stage number (1, 2, 3) or 'highlight'
            paper_id: arXiv paper ID
            result: Result to cache
            config_hash: Optional configuration hash
        """
        cache = self._get_cache_by_stage(stage)
        key = self._generate_key(paper_id, config_hash)

        cache.set(key, result, expire=self.expire_seconds)
        logger.debug(f"Cache SET: {stage}/{key}")

    def exists(
        self,
        stage: int | str,
        paper_id: str,
        config_hash: str | None = None,
    ) -> bool:
        """
        Check if a result exists in cache.

        Args:
            stage: Stage number (1, 2, 3) or 'highlight'
            paper_id: arXiv paper ID
            config_hash: Optional configuration hash

        Returns:
            True if cached result exists
        """
        cache = self._get_cache_by_stage(stage)
        key = self._generate_key(paper_id, config_hash)
        return key in cache

    def delete(
        self,
        stage: int | str,
        paper_id: str,
        config_hash: str | None = None,
    ) -> bool:
        """
        Delete a cached result.

        Args:
            stage: Stage number (1, 2, 3) or 'highlight'
            paper_id: arXiv paper ID
            config_hash: Optional configuration hash

        Returns:
            True if entry was deleted, False if not found
        """
        cache = self._get_cache_by_stage(stage)
        key = self._generate_key(paper_id, config_hash)

        if key in cache:
            del cache[key]
            logger.debug(f"Cache DELETE: {stage}/{key}")
            return True

        return False

    def clear_stage(self, stage: int | str) -> None:
        """
        Clear all cached results for a specific stage.

        Args:
            stage: Stage number (1, 2, 3) or 'highlight'
        """
        cache = self._get_cache_by_stage(stage)
        cache.clear()
        logger.info(f"Cleared {stage} cache")

    def clear_all(self) -> None:
        """Clear all cached results from all stages."""
        self.stage1_cache.clear()
        self.stage2_cache.clear()
        self.stage3_cache.clear()
        self.highlight_cache.clear()
        logger.info("Cleared all caches")

    def get_stats(self, stage: int | str | None = None) -> dict:
        """
        Get cache statistics.

        Args:
            stage: Optional stage number (1, 2, 3) or 'highlight'. If None, returns stats for all stages.

        Returns:
            Dictionary with cache statistics
        """
        if stage is not None:
            cache = self._get_cache_by_stage(stage)
            return {
                str(stage): {
                    "size": len(cache),  # type: ignore
                    "volume": cache.volume(),
                    "size_limit": cache.size_limit,  # type: ignore
                }
            }

        # Return stats for all stages
        return {
            "stage1": {
                "size": len(self.stage1_cache),  # type: ignore
                "volume": self.stage1_cache.volume(),
                "size_limit": self.stage1_cache.size_limit,  # type: ignore
            },
            "stage2": {
                "size": len(self.stage2_cache),  # type: ignore
                "volume": self.stage2_cache.volume(),
                "size_limit": self.stage2_cache.size_limit,  # type: ignore
            },
            "stage3": {
                "size": len(self.stage3_cache),  # type: ignore
                "volume": self.stage3_cache.volume(),
                "size_limit": self.stage3_cache.size_limit,  # type: ignore
            },
            "highlight": {
                "size": len(self.highlight_cache),  # type: ignore
                "volume": self.highlight_cache.volume(),
                "size_limit": self.highlight_cache.size_limit,  # type: ignore
            },
        }

    def close(self) -> None:
        """Close all cache connections."""
        self.stage1_cache.close()
        self.stage2_cache.close()
        self.stage3_cache.close()
        self.highlight_cache.close()
        logger.debug("Cache manager closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
