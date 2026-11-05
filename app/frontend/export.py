"""Excel-де қазақша мәтіні дұрыс ашылатын CSV экспорты."""

import csv
from io import StringIO


def export_csv(tools, disciplines, teachers):
    buffer = StringIO(newline="")
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(["№", "Атауы", "Түрі", "Пән", "Автор", "Жалпы балл", "Мазмұны"])
    for tool in tools:
        row = [tool["id"], tool["title"], tool["tool_type"],
               disciplines.get(tool["discipline_id"], ""),
               teachers.get(tool["author_id"], ""), tool["total_score"], tool["content"]]
        # Пайдаланушы мәтіні электрондық кестеде формула болып орындалмасын.
        writer.writerow(["'" + value if isinstance(value, str) and
                         value.lstrip().startswith(("=", "+", "-", "@")) else value
                         for value in row])
    return buffer.getvalue().encode("utf-8-sig")
