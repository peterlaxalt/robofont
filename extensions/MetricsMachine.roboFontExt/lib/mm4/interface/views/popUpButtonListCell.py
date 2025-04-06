import AppKit


def PopUpButtonListCell(items):
    cell = AppKit.NSPopUpButtonCell.alloc().init()
    cell.setBordered_(False)
    # add the basic items
    titles = []
    for title in items:
        if isinstance(title, (AppKit.NSString, AppKit.NSAttributedString)):
            title = title.string()
        titles.append(title)
    cell.addItemsWithTitles_(titles)
    # add attributed titles
    for index, title in enumerate(items):
        if not isinstance(title, AppKit.NSAttributedString):
            continue
        item = cell.itemAtIndex_(index)
        item.setAttributedTitle_(title)
    return cell
