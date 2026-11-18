import argparse

from src.dataset import prepare_data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Volver a descargar solo los archivos SCIFACT permitidos")
    args = parser.parse_args()
    counts = prepare_data(force=args.force)
    print(f"Dataset SCIFACT listo: {counts}")


if __name__ == "__main__":
    main()
