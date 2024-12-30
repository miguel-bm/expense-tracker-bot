from io import BytesIO
from typing import Literal

import xlrd
from openpyxl import load_workbook
from telegram import Update
from telegram.ext import ContextTypes

from app.bot.utils import filter_message, send_typing_action
from app.models.movement import Movement
from app.utils.logger import logger


def process_bbva(file_bytes: bytes) -> list[Movement]:
    wb = load_workbook(filename=BytesIO(file_bytes))
    sheet = wb.worksheets[0]
    movements = []

    # Start from row 5 and column B (which is index 1)
    row = 6
    while sheet.cell(row=row, column=2).value:  # Check if Fecha cell is not empty
        concept = str(sheet.cell(row=row, column=4).value)
        movement_str = str(sheet.cell(row=row, column=5).value)
        observations = str(sheet.cell(row=row, column=10).value)
        text = f"{concept}; {movement_str}; {observations}"
        movements.append(
            Movement(
                date_=sheet.cell(row=row, column=2).value.date(),  # type: ignore
                date_value=sheet.cell(row=row, column=3).value.date(),  # type: ignore
                description=text,
                amount=float(sheet.cell(row=row, column=6).value or 0.0),  # type: ignore
                balance=float(sheet.cell(row=row, column=8).value or 0.0),  # type: ignore
            )
        )
        row += 1

    return movements


def process_imagin(file_bytes: bytes) -> list[Movement]:
    wb: xlrd.book.Book = xlrd.open_workbook(file_contents=file_bytes)
    sheet: xlrd.sheet.Sheet = wb.sheet_by_index(0)
    movements = []
    for row_idx in range(3, sheet.nrows):  # Start from row 4
        if not sheet.cell_value(row_idx, 0):  # Empty first cell
            break

        # Convert Excel dates to Python dates
        date_ = xlrd.xldate.xldate_as_datetime(sheet.cell_value(row_idx, 0), 0).date()
        date_value = xlrd.xldate.xldate_as_datetime(
            sheet.cell_value(row_idx, 1), 0
        ).date()

        concept = str(sheet.cell_value(row_idx, 2) or "")
        description = str(sheet.cell_value(row_idx, 3) or "")
        text = f"{concept}; {description}"

        movements.append(
            Movement(
                date_=date_,
                date_value=date_value,
                description=text,
                amount=float(sheet.cell_value(row_idx, 4) or 0.0),
                balance=float(sheet.cell_value(row_idx, 5) or 0.0),
            )
        )
    return movements


def discriminate_format(
    file_bytes: bytes, file_extension: str
) -> Literal["bbva", "imagin"] | None:
    """Discriminate the format of the sheet"""
    if file_extension == "xls":
        return "imagin"
    elif file_extension == "xlsx":
        return "bbva"
    return None


def process_tabular_file(file_bytes: bytes, file_extension: str) -> list[Movement]:
    """Process tabular files (XLS, XLSX) and return movements."""
    try:
        file_format = discriminate_format(file_bytes, file_extension)

        if file_format == "imagin":
            return process_imagin(file_bytes)
        elif file_format == "bbva":
            return process_bbva(file_bytes)
        else:
            raise ValueError("Unsupported file format")

    except Exception as e:
        logger.exception(f"Error processing file: {str(e)}")
        raise e


@send_typing_action
@filter_message
async def handle_file_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    assert update.message and update.message.document

    from_user = update.message.from_user
    username = from_user.username if from_user else "unknown"
    file = update.message.document

    logger.info(f"Received file from {username}: {file.file_name}")

    # Get file extension and download file

    if file.file_name is None:
        await update.message.reply_text(
            "Sorry, I couldn't process this file because I couldn't get the file name."
        )
        return

    file_extension = file.file_name.lower().split(".")[-1]
    file_content = await file.get_file()
    file_bytes = await file_content.download_as_bytearray()

    # Process the file
    if file_extension not in ["xls", "xlsx"]:
        await update.message.reply_text(
            "Sorry, I can only process CSV, XLS, or XLSX files at the moment."
        )
        return

    movements = process_tabular_file(file_bytes, file_extension)
    logger.info(f"Processed {len(movements)} movements")
    return


# if __name__ == "__main__":
#     imagin_file_path = "tests/Movimientos_cuenta_0096303 (8).xls"
#     imagin_bytes = open(imagin_file_path, "rb").read()
#     print("Read bytes for imagin file")
#     imagin_movements = process_tabular_file(imagin_bytes, "xls")
#     print(imagin_movements[0])

#     bbva_file_path = "tests/2024Y-12M-27D-13_42_25-Últimos movimientos.xlsx"
#     bbva_bytes = open(bbva_file_path, "rb").read()
#     bbva_movements = process_tabular_file(bbva_bytes, "xlsx")
#     print(bbva_movements[0])