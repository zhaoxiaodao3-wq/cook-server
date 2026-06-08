import asyncio
import selectors
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def main():
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.core.config import settings

    engine = create_async_engine(settings.DATABASE_URL)
    Session = async_sessionmaker(engine)
    async with Session() as db:
        try:
            r = await db.execute(text("SELECT 1"))
            print("DB OK", r.scalar())

            r2 = await db.execute(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name='categories' ORDER BY 1"
                )
            )
            print("categories cols", [x[0] for x in r2.fetchall()])

            r3 = await db.execute(text("SELECT to_regclass('public.favorites')"))
            print("favorites table", r3.scalar())

            r4 = await db.execute(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name='dishes' AND column_name IN ('tags','cuisine','avg_rating') "
                    "ORDER BY 1"
                )
            )
            print("dishes cols", [x[0] for x in r4.fetchall()])

            from app.services.category import get_all_categories

            cats = await get_all_categories(db)
            print("categories count", len(cats))

            from app.services.dish import get_dishes

            dishes, total = await get_dishes(db, page=1, page_size=5)
            print("dishes OK", total, len(dishes))
        except Exception as ex:
            print("ERR", type(ex).__name__, ex)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
