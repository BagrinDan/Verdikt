

# Данная 'смарт' функция нужна чтобы сразу сменить бранч на 'main'
# если был введён 'master' и наоборот


def switch(branch: str) -> str:
    if branch == 'main':
        return 'master'
    else:
        return 'main'
