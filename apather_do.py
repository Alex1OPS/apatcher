import ApatcherClass as ac
import sys
import argparse

version = "0.1b"


# Не будем городить класс для парсера, т.к. argparse создает его внутри методов.
# Навернем немного функциональной лапши до непосредственного формирования шаблона.
def create_parser():
    parser = argparse.ArgumentParser(
        prog="apatcher_forward",
        description="Автоматизированная сборка template патча",
        epilog="(c) Alex1OPS.",
        add_help=False
    )
    # группа параметров
    parent_group = parser.add_argument_group(title="Параметры")
    parent_group.add_argument("-p", "--project", required=True)
    parent_group.add_argument("-c", "--commit", action='store_true', default=False)
    parent_group.add_argument("-t", "--text", default="Empty comment line")
    parent_group.add_argument("--help", "-h", action="help", help="Справка")
    parent_group.add_argument("--version",
                              action="version",
                              help="Вывести номер версии",
                              version="%(prog)s {}".format(version))
    return parser


def main():
    parser = create_parser()
    namespace = parser.parse_args(sys.argv[1:])
    print(namespace.project)


if __name__ == "__main__":
    main()
