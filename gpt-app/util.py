from bs4 import BeautifulSoup


def parse_content(content):
    # Parse the table with BeautifulSoup
    soup = BeautifulSoup(content, "html.parser")
    table = soup.find("table")

    if not table:
        print("No table found on the page.")
        return None

    return table


def find_info_in_cell(table):
    rows = table.find_all("tr")

    if len(rows) < 1:
        print("The table has fewer than 1 rows.")
        return None

    second_row = rows[1]  # Index 1 = second row
    cell = second_row.find("td")

    if not cell:
        print("No cell found in the second row.")
        return None

    # Extract the cell's text
    cell_text = cell.get_text(strip=True)
    return cell_text


def update_4th_cell(table, new_value):
    """Updates the 4th cell"""
    rows = table.find_all("tr")

    # Ensure there are enough rows
    if len(rows) > 3:
        cells = rows[3].find_all("td")
        cell = cells[0]
        p_tag = cell.find("p")  # Find the <p> tag inside the <td>
        print(p_tag)
        if p_tag:
            p_tag.string = new_value


def generate_content(table):
    """Generates updated content from the modified table."""
    return str(table)