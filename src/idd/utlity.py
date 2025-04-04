# Adapted from https://github.com/mmlb/ansi2txt/blob/main/ansi2txt.py


def uncolored(text: str):
    start = 0
    result = ""

    def putchar(ch: str):
        nonlocal result
        result += ch

    def getchar() -> str:
        nonlocal start
        if start < len(text):
            ch = text[start]
        else:
            ch = ""
        start += 1
        return ch

    EOF = ""
    ch = None

    while ch != EOF:
        ch = getchar()
        while ch == "\r":
            ch = getchar()
            if ch != "\n":
                putchar("\r")

        if ch == "\x1b":
            ch = getchar()
            if ch == "[":
                ch = getchar()
                while ch == ";" or (ch >= "0" and ch <= "9") or ch == "?":
                    ch = getchar()
            elif ch == "]":
                ch = getchar()
                if ord(ch) >= 0 and ch <= "9":
                    while True:
                        ch = getchar()
                        if ch == EOF or ord(ch) == 7:
                            break
                        elif ch == "\x1b":
                            ch = getchar()
                            break
            elif ch == "%":
                ch = getchar()
            else:
                pass
        elif ch != EOF:
            putchar(ch)

    return result


if __name__ == "__main__":
    import sys

    print(uncolored(sys.stdin.read()))
