import asyncio
import uvicorn
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))


async def main() -> None:
    uvicorn.run('src.application:get_app', host='localhost', port=8000, reload=True, factory=True)

if __name__ == '__main__':
    asyncio.run(main())