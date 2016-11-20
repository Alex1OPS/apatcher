"""
Wrap-скрит для вызова автопатчилки.
Простая делегация в метод main основного модуля fwpt_apatcher
"""

import fwpt_apatcher.apather_do as fa

def main():
    fa.main()

if __name__ == "__main__":
    main()