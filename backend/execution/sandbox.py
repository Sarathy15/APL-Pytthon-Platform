import asyncio

class TimeoutHandler:
    @staticmethod
    async def run_with_timeout(coro, seconds: int):
        try:
            return await asyncio.wait_for(coro, timeout=seconds)
        except asyncio.TimeoutError:
            return {"error": "Execution timed out"}

class Sandbox:
    @staticmethod
    def execute_safe(code: str):
        # Restricted execution environment simulation
        # In production, this would use a Docker container or gVisor
        local_scope = {}
        try:
            exec(code, {"np": __import__("numpy")}, local_scope)
            return {"success": True, "output": str(local_scope.get("result"))}
        except Exception as e:
            return {"success": False, "error": str(e)}
