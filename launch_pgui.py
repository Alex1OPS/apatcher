"""
Wrap-скрит для вызова автопатчилки.
Простая делегация в метод main GUI модуля fwpt_apatcher
"""

import fwpt_apatcher.ApatcherGUI as AG


def main():
    AG.main()


if __name__ == "__main__":
    main()
