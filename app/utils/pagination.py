import math
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select


async def paginate(db: AsyncSession, query: Select, page: int = 1, per_page: int = 10):
    per_page = min(per_page, 50)
    page = max(page, 1)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    pages = math.ceil(total / per_page) if total > 0 else 1
    offset = (page - 1) * per_page

    result = await db.execute(query.offset(offset).limit(per_page))
    items = result.unique().scalars().all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages,
    }
