import logging
import os
import sys

import click

from mev_inspect.concurrency import coro
from mev_inspect.crud.prices import write_prices
from mev_inspect.db import get_sessions
from mev_inspect.inspector import MEVInspector
from mev_inspect.prices import fetch_all_supported_prices

RPC_URL_ENV = "RPC_URL"

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)


@click.group()
def cli():
    pass


@cli.command()
@click.argument("block_number", type=int)
@click.option("--rpc", default=lambda: os.environ.get(RPC_URL_ENV, ""))
@coro
async def inspect_block_command(block_number: int, rpc: str):
    inspector = MEVInspector(rpc)
    inspect_session, trace_session = get_sessions()
    await inspector.inspect_single_block(
        block=block_number, inspect_session=inspect_session, trace_session=trace_session
    )


@cli.command()
@click.argument("block_number", type=int)
@click.option("--rpc", default=lambda: os.environ.get(RPC_URL_ENV, ""))
@coro
async def fetch_block_command(block_number: int, rpc: str):
    inspector = MEVInspector(rpc)
    _, trace_session = get_sessions()
    block = await inspector.create_from_block(
        block_number=block_number, trace_session=trace_session
    )
    print(block.json())


@cli.command()
@click.argument("after_block", type=int)
@click.argument("before_block", type=int)
@click.option("--rpc", default=lambda: os.environ.get(RPC_URL_ENV, ""))
@click.option(
    "--max-concurrency",
    type=int,
    help="maximum number of concurrent connections",
    default=5,
)
@click.option(
    "--request-timeout", type=int, help="timeout for requests to nodes", default=500
)
@coro
async def inspect_many_blocks_command(
    after_block: int,
    before_block: int,
    rpc: str,
    max_concurrency: int,
    request_timeout: int,
):
    inspector = MEVInspector(
        rpc,
        max_concurrency=max_concurrency,
        request_timeout=request_timeout,
    )
    inspect_session, trace_session = get_sessions()
    await inspector.inspect_many_blocks(
        after_block=after_block,
        before_block=before_block,
        inspect_session=inspect_session,
        trace_session=trace_session,
    )


@cli.command()
@coro
async def fetch_all_prices():
    inspect_session, _ = get_sessions()

    logger.info("Fetching prices")
    prices = await fetch_all_supported_prices()

    logger.info("Writing prices")
    write_prices(inspect_session, prices)


def get_rpc_url() -> str:
    return os.environ["RPC_URL"]


if __name__ == "__main__":
    cli()
