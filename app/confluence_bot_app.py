from confluence import read_doc, update_doc
from util import parse_content, find_data_in_cell, update_cell, generate_content
import asyncio
PROMPT = ('Below is the data about our infrastructure, which is part of the effort to obtain the FedRAMP '
          'certification. Please analyze the information and identify the specific actions or improvements that we '
          'need to make in order to successfully acquire the certification. \n')


async def run_program(rag, ai_model='internal'):
    old_info = ''
    print('Program started with model: ' + ai_model)
    while True:
        await asyncio.sleep(2)
        content = read_doc()
        table = parse_content(content)
        initial_data = find_data_in_cell(table, 1)
        ai_answer = find_data_in_cell(table, 3)
        if initial_data and initial_data != old_info:
            if ai_model == 'internal':
                answer = rag.ask(PROMPT + initial_data)
            else:
                answer = rag.ask(PROMPT + initial_data)

            update_cell(4, table, answer)
            new_content = generate_content(table)
            update_doc(new_content)
        if not initial_data and ai_answer:
            update_cell(4, table, '')
            new_content = generate_content(table)
            update_doc(new_content)
        old_info = initial_data

