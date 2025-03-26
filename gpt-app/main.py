from confluence import read_doc, update_doc
from util import parse_content, find_data_in_cell, update_cell, generate_content
import asyncio


async def main():
    old_info = ''
    while True:
        await asyncio.sleep(2)
        content = read_doc()
        table = parse_content(content)
        initial_data = find_data_in_cell(table, 1)
        ai_answer = find_data_in_cell(table, 3)
        if initial_data and initial_data != old_info:
            update_cell(4, table, f'hello from application')
            new_content = generate_content(table)
            update_doc(new_content)
        if not initial_data and ai_answer:
            update_cell(4, table, '')
            new_content = generate_content(table)
            update_doc(new_content)
        old_info = initial_data


if __name__ == "__main__":
    asyncio.run(main())

