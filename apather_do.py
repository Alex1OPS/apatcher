import ApatcherClass as ac
import sys
import argparse
import configparser

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
    parent_group.add_argument("-p", "--project", required=True, help="Проект")
    parent_group.add_argument("-c", "--commit", action='store_true', default=False, help="Флаг коммита после сборки")
    parent_group.add_argument("-t", "--text", default="Empty comment line", help="Текст комментария к коммиту")
    parent_group.add_argument("--help", "-h", action="help", help="Справка")
    parent_group.add_argument("--version",
                              action="version",
                              help="Номер версии",
                              version="%(prog)s {}".format(version))
    return parser


def main():
    # получим аргументы командной строки
    parser = create_parser()
    namespace = parser.parse_args(sys.argv[1:])
    # получим полный путь до папки проекта
    try:
        t = ac.CfgInfo
        t.init(t)
        path_dir = t.path.get("projects_path", namespace.project)
        print(path_dir)
    except configparser.NoOptionError:
        print("Config file parse error")
        exit(0)


if __name__ == "__main__":
    main()
