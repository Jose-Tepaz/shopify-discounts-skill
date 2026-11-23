#!/usr/bin/env python3
"""Genera códigos de descuento únicos y los divide en lotes para discountRedeemCodeBulkAdd.

Uso:
    python3 redeem_codes.py --count 2000 --prefix BF26- --out codes/
    python3 redeem_codes.py --from-file mis_codigos.txt --out codes/   # trocea una lista existente

Salida en --out:
    codes.csv         todos los códigos (uno por línea, con encabezado)
    batch-001.json    variables {"codes": [{"code": "..."}]} con <= --batch-size códigos

El ID del descuento no se incluye: pásalo como variable aparte ($discountId).
"""
import argparse
import csv
import json
import secrets
import sys
from pathlib import Path

# Sin caracteres ambiguos (0/O, 1/I/L) para que los clientes los escriban sin errores.
ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
MAX_BATCH = 250  # límite de discountRedeemCodeBulkAdd por llamada (API 2026-10)


def generate(count: int, prefix: str, length: int, exclude: set[str]) -> list[str]:
    # Alfabeto de 31 símbolos: con length=8 hay ~8.5e11 combinaciones, colisiones despreciables.
    if len(ALPHABET) ** length < count * 10:
        sys.exit(f"--length {length} es demasiado corto para {count} códigos únicos")
    seen = {c.upper() for c in exclude}
    codes: list[str] = []
    while len(codes) < count:
        code = prefix + "".join(secrets.choice(ALPHABET) for _ in range(length))
        if code.upper() not in seen:  # Shopify compara códigos sin distinguir mayúsculas
            seen.add(code.upper())
            codes.append(code)
    return codes


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--count", type=int, help="cuántos códigos generar")
    src.add_argument("--from-file", type=Path, help="archivo con un código por línea")
    p.add_argument("--prefix", default="", help="prefijo, p. ej. BF26-")
    p.add_argument("--length", type=int, default=8, help="caracteres aleatorios tras el prefijo")
    p.add_argument("--exclude", type=Path, help="archivo con códigos existentes a evitar")
    p.add_argument("--batch-size", type=int, default=MAX_BATCH)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()

    if not 1 <= a.batch_size <= MAX_BATCH:
        sys.exit(f"--batch-size debe estar entre 1 y {MAX_BATCH}")

    exclude: set[str] = set()
    if a.exclude:
        exclude = {l.strip() for l in a.exclude.read_text().splitlines() if l.strip()}

    if a.from_file:
        raw = [l.strip() for l in a.from_file.read_text().splitlines() if l.strip()]
        codes, seen = [], {c.upper() for c in exclude}
        for c in raw:
            if c.upper() in seen:
                print(f"omitido duplicado/existente: {c}", file=sys.stderr)
                continue
            seen.add(c.upper())
            codes.append(c)
    else:
        codes = generate(a.count, a.prefix, a.length, exclude)

    if len(codes) > 20_000_000:
        sys.exit("excede el límite de 20M códigos por tienda")

    a.out.mkdir(parents=True, exist_ok=True)
    with (a.out / "codes.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["code"])
        w.writerows([c] for c in codes)

    batches = [codes[i : i + a.batch_size] for i in range(0, len(codes), a.batch_size)]
    for n, batch in enumerate(batches, 1):
        (a.out / f"batch-{n:03d}.json").write_text(json.dumps({"codes": [{"code": c} for c in batch]}))

    print(json.dumps({"codes": len(codes), "batches": len(batches), "out": str(a.out)}))


if __name__ == "__main__":
    main()
