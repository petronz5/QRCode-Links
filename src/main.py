def main():
    import sys
    from utils import generate_qr_code

    if len(sys.argv) != 2:
        print("Usage: python main.py <URL>")
        sys.exit(1)

    url = sys.argv[1]
    generate_qr_code(url, "qrcode.png")

if __name__ == "__main__":
    main()