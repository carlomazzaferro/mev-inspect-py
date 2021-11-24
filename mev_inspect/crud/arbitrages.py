from typing import List
from uuid import uuid4

from mev_inspect.crud.generic import delete_by_block_number
from mev_inspect.models.arbitrages import ArbitrageModel
from mev_inspect.schemas.arbitrages import Arbitrage


async def delete_arbitrages_for_block(db_session, block_number: int) -> None:
    await delete_by_block_number(
        db_session=db_session, block_number=block_number, model=ArbitrageModel
    )


async def write_arbitrages(
    db_session,
    arbitrages: List[Arbitrage],
) -> None:
    arbitrage_models = []
    swap_arbitrage_ids = []

    for arbitrage in arbitrages:
        arbitrage_id = str(uuid4())
        arbitrage_models.append(
            ArbitrageModel(
                id=arbitrage_id,
                block_number=arbitrage.block_number,
                transaction_hash=arbitrage.transaction_hash,
                account_address=arbitrage.account_address,
                profit_token_address=arbitrage.profit_token_address,
                start_amount=arbitrage.start_amount,
                end_amount=arbitrage.end_amount,
                profit_amount=arbitrage.profit_amount,
            )
        )

        for swap in arbitrage.swaps:
            swap_arbitrage_ids.append(
                {
                    "arbitrage_id": arbitrage_id,
                    "swap_transaction_hash": swap.transaction_hash,
                    "swap_trace_address": swap.trace_address,
                }
            )

    if len(arbitrage_models) > 0:
        db_session.add_all(arbitrage_models)
        await db_session.commit()
        await db_session.flush()
        await db_session.execute(
            """
            INSERT INTO arbitrage_swaps
            (arbitrage_id, swap_transaction_hash, swap_trace_address)
            VALUES
            (:arbitrage_id, :swap_transaction_hash, :swap_trace_address)
            """,
            params=swap_arbitrage_ids,
        )
        await db_session.commit()
        await db_session.flush()
