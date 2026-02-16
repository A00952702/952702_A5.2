#!/usr/bin/env python3
"""
computeSales.py

Reads:
  1) priceCatalogue.json: list of products with their prices
  2) salesRecord.json: list of sales rows (Product, Quantity, ...)

Computes total cost for all sales and writes a human-readable report to:
  SalesResults.txt

Requirements reference:
- CLI invocation with 2 file parameters
- Continue on invalid data, printing errors to console
- Print results to console and file
- Include elapsed time
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from typing import Any


RESULTS_FILENAME = "SalesResults.txt"


@dataclass(frozen=True)
class SaleLine:
    """A validated sale line."""
    sale_id: str
    sale_date: str
    product: str
    quantity: float


def _safe_str(value: Any) -> str:
    """Convert any value to a safe string for messages."""
    try:
        return str(value)
    except Exception:  # pragma: no cover
        return "<unprintable>"


def load_json_file(path: str) -> Any:
    """Load and parse JSON from a file path."""
    with open(path, "r", encoding="utf-8", errors="ignore") as file:
        return json.load(file)


def build_price_map(catalogue_json: Any) -> dict[str, float]:
    """
    Builds a product->price dictionary from the catalogue JSON.

    Expected format: a list of objects containing at least:
      - "title" (product name)
      - "price" (numeric)
    """
    prices: dict[str, float] = {}

    if not isinstance(catalogue_json, list):
        raise ValueError("Price catalogue JSON must be a list of product objects.")

    for idx, item in enumerate(catalogue_json, start=1):
        if not isinstance(item, dict):
            print(f"[Catalogue row {idx}] Invalid item (not an object). Skipping.")
            continue

        title = item.get("title")
        price = item.get("price")

        if not isinstance(title, str) or not title.strip():
            print(f"[Catalogue row {idx}] Missing/invalid 'title'. Skipping.")
            continue

        try:
            price_num = float(price)
        except (TypeError, ValueError):
            print(
                f"[Catalogue row {idx}] Invalid 'price' for title '{title}': "
                f"{_safe_str(price)}. Skipping."
            )
            continue

        prices[title.strip()] = price_num

    return prices


def parse_sale_line(raw: Any, row_num: int) -> SaleLine | None:
    """
    Validate and normalize a single sale line.
    Expected keys (minimum):
      - Product (str)
      - Quantity (number)
    Optional:
      - SALE_ID, SALE_Date
    """
    if not isinstance(raw, dict):
        print(f"[Sales row {row_num}] Invalid row (not an object). Skipping.")
        return None

    product = raw.get("Product")
    quantity = raw.get("Quantity")

    if not isinstance(product, str) or not product.strip():
        print(f"[Sales row {row_num}] Missing/invalid 'Product'. Skipping.")
        return None

    try:
        qty = float(quantity)
    except (TypeError, ValueError):
        print(
            f"[Sales row {row_num}] Invalid 'Quantity' for product '{product}': "
            f"{_safe_str(quantity)}. Skipping."
        )
        return None

    # Negative quantities don't make sense for a "sale" record; treat as invalid.
    try:
        qty = float(quantity)
    except (TypeError, ValueError):
        print(
            f"[Sales row {row_num}] Invalid 'Quantity' for product '{product}': "
            f"{_safe_str(quantity)}. Skipping."
        )
        return None

    sale_id = _safe_str(raw.get("SALE_ID", "N/A"))
    sale_date = _safe_str(raw.get("SALE_Date", "N/A"))

    return SaleLine(
        sale_id=sale_id,
        sale_date=sale_date,
        product=product.strip(),
        quantity=qty,
    )


def compute_total(prices: dict[str, float], sales_json: Any) -> tuple[float, list[str]]:
    """
    Computes total cost from sales_json using prices dict.
    Returns: (total_cost, detail_lines)
    """
    if not isinstance(sales_json, list):
        raise ValueError("Sales record JSON must be a list of sale objects.")

    total = 0.0
    detail_lines: list[str] = []
    valid_rows = 0

    for i, raw_row in enumerate(sales_json, start=1):
        sale = parse_sale_line(raw_row, i)
        if sale is None:
            continue

        valid_rows += 1
        if sale.product not in prices:
            print(
                f"[Sales row {i}] Product not found in catalogue: '{sale.product}'. "
                "Skipping."
            )
            continue

        unit_price = prices[sale.product]
        line_total = unit_price * sale.quantity
        total += line_total

        detail_lines.append(
            f"- SALE_ID={sale.sale_id} | DATE={sale.sale_date} | "
            f"PRODUCT='{sale.product}' | QTY={sale.quantity:g} | "
            f"UNIT={unit_price:.2f} | LINE_TOTAL={line_total:.2f}"
        )

    detail_lines.insert(0, f"VALID_SALES_ROWS: {valid_rows}")
    return total, detail_lines


def write_results(total: float, details: list[str], elapsed_seconds: float) -> None:
    """Write results to console and SalesResults.txt."""
    lines: list[str] = []
    lines.append("SALES SUMMARY")
    lines.append("=============")
    lines.extend(details)
    lines.append("")
    lines.append(f"TOTAL_COST: {total:.2f}")
    lines.append(f"ELAPSED_SECONDS: {elapsed_seconds:.6f}")

    for line in lines:
        print(line)

    with open(RESULTS_FILENAME, "w", encoding="utf-8") as out:
        for line in lines:
            out.write(line + "\n")


def main() -> None:
    """
    CLI entry point.

    Required invocation:
      python computeSales.py priceCatalogue.json salesRecord.json
    """
    if len(sys.argv) != 3:
        print("Usage: python computeSales.py priceCatalogue.json salesRecord.json")
        sys.exit(1)

    catalogue_path = sys.argv[1]
    sales_path = sys.argv[2]

    start = time.perf_counter()

    try:
        catalogue_json = load_json_file(catalogue_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Error reading catalogue file '{catalogue_path}': {exc}")
        sys.exit(1)

    try:
        sales_json = load_json_file(sales_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Error reading sales file '{sales_path}': {exc}")
        sys.exit(1)

    prices = build_price_map(catalogue_json)

    try:
        total, details = compute_total(prices, sales_json)
    except ValueError as exc:
        print(f"Error processing data: {exc}")
        sys.exit(1)

    elapsed = time.perf_counter() - start
    write_results(total, details, elapsed)


if __name__ == "__main__":
    main()
