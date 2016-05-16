def show_menu():
    print("\t1. Add file;")
    print("\t2. Delete file;")
    print("\t3. Accept;")
    print("\t4. Exit;")

    choice = input("\t\t:")
    if choice not in {"1", "2", "3", "4"}:
        print("Error in menu item")
        exit(0)

    return int(choice)


def print_list(lmass, name=""):
    print("\nEditing list of " + name)
    for i in range(0, len(lmass)):
        print(str(i) + ". " + lmass[i])


def edit_list(lmass=[], action=0):
    new_filename = ""
    del_num = -1
    if action == 1:
        # получим новый файл
        input("Enter file name: ", new_filename)
        lmass.append(new_filename)
        return lmass
    elif action == 2:
        input("Enter file number in list: ", del_num)
        del lmass[del_num]
        return lmass
    else:
        return lmass

