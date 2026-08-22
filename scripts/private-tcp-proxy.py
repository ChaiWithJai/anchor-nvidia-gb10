#!/usr/bin/env python3
"""Expose a loopback TCP service on one explicitly selected private bridge."""

import argparse
import asyncio
import contextlib


async def pipe(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    try:
        while data := await reader.read(64 * 1024):
            writer.write(data)
            await writer.drain()
    except (ConnectionError, asyncio.CancelledError):
        pass
    finally:
        writer.close()
        with contextlib.suppress(ConnectionError):
            await writer.wait_closed()


async def handle(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    target_host: str,
    target_port: int,
) -> None:
    try:
        upstream_reader, upstream_writer = await asyncio.open_connection(
            target_host, target_port
        )
    except ConnectionError:
        writer.close()
        return
    await asyncio.gather(
        pipe(reader, upstream_writer),
        pipe(upstream_reader, writer),
    )


async def main(args: argparse.Namespace) -> None:
    server = await asyncio.start_server(
        lambda reader, writer: handle(
            reader, writer, args.target_host, args.target_port
        ),
        args.listen_host,
        args.listen_port,
    )
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--listen-host", required=True)
    parser.add_argument("--listen-port", type=int, default=18000)
    parser.add_argument("--target-host", default="127.0.0.1")
    parser.add_argument("--target-port", type=int, default=18000)
    try:
        asyncio.run(main(parser.parse_args()))
    except KeyboardInterrupt:
        pass
