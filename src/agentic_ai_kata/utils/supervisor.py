import asyncio
import time
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

Heartbeat = Dict[str, Any]


class Supervisor:
    def __init__(self, heartbeat_cb: Optional[Callable[[Heartbeat], None]] = None) -> None:
        self.heartbeat_cb = heartbeat_cb

    def _emit(self, beat: Heartbeat) -> None:
        if self.heartbeat_cb:
            try:
                self.heartbeat_cb(beat)
            except Exception:
                pass

    async def run_with_timeout(self, name: str, coro: Awaitable[Any], timeout: float) -> Tuple[str, Any, Optional[BaseException]]:
        start = time.time()
        self._emit({"agent": name, "event": "start", "ts": start})
        try:
            res = await asyncio.wait_for(coro, timeout=timeout)
            end = time.time()
            self._emit({"agent": name, "event": "done", "ts": end, "duration": end - start})
            return name, res, None
        except Exception as e:
            end = time.time()
            self._emit({"agent": name, "event": "error", "ts": end, "duration": end - start, "error": str(e)})
            return name, None, e

    async def run_parallel(self, tasks: List[Tuple[str, Awaitable[Any], float]]) -> Dict[str, Any]:
        coros = [self.run_with_timeout(name, coro, timeout) for name, coro, timeout in tasks]
        results: Dict[str, Any] = {}
        for fut in asyncio.as_completed(coros):
            name, res, err = await fut
            results[name] = {"result": res, "error": str(err) if err else None}
        return results
