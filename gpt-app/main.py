import openai
from confluence import read_doc, update_doc
from util import parse_content, find_info_in_cell, update_cell, generate_content
import asyncio


async def main():
    old_info = ''
    while True:
        await asyncio.sleep(2)
        content = read_doc()
        table = parse_content(content)
        info = find_info_in_cell(table)
        if info and info != old_info:
            update_cell(4, table, f'hello from application')
            new_content = generate_content(table)
            update_doc(new_content)
        if not info:
            update_cell(4, table, '')
            new_content = generate_content(table)
            update_doc(new_content)
        old_info = info


if __name__ == "__main__":
    asyncio.run(main())

