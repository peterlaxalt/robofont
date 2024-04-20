from mojo.UI import CurrentFontWindow
import AppKit
import unicodedata
from vanilla import CheckBox, FloatingWindow, List, LevelIndicatorListCell
import glyphNameFormatter

f = CurrentFont()

u_ranges = glyphNameFormatter.unicodeRangeNames.unicodeRangeNames
reverse_ranges = {v: k for k, v in u_ranges.items()}

category_to_codepoints = {}
for code_point in range(0, 0xFFFF + 1):
    category = unicodedata.category(chr(code_point))
    category_to_codepoints.setdefault(category, []).append(code_point)

ignore_cats = [
    cat for cat in category_to_codepoints.keys() if cat.startswith('C')]
ignore_codepoints = []
for category in ignore_cats:
    ignore_codepoints.extend(category_to_codepoints.get(category))


def percentage(sample, full_amount):
    if full_amount > 0:
        return sample / (full_amount / 100)
    else:
        return 0


class RangeList(object):

    def __init__(self, font):
        self.f = font
        self.select_suffix = False
        self.font_code_points = list(
            sum([g.unicodes for g in f if g.unicodes], ()))
        self.font_ranges = self.get_supported_range_names(
            self.font_code_points)
        self.display_range_list = []
        for range_name in self.font_ranges:
            percentage = self.support_percentage(range_name)
            self.display_range_list.append({
                'Range': range_name,
                'Support': percentage / 10,
                '%': f'{round(percentage)}%',
            })

        list_height = 24 + 20 * len(self.font_ranges)
        window_height = list_height + 24
        self.w = FloatingWindow(
            (350, window_height),
            title='Unicode support',
        )
        self.w.bind('close', self.close_callback)

        self.w.myList = List(
            (0, 0, -0, list_height),
            self.display_range_list,
            columnDescriptions=[
                {'title': 'Range', 'width': 150},
                {
                    'title': 'Support',
                    'cell': LevelIndicatorListCell(style="continuous"),
                    'width': 105
                },
                {'title': '%', 'width': 55}
            ],
            selectionCallback=self.sel_callback,
            allowsMultipleSelection=True
        )
        self.w.myCheckBox = CheckBox(
            (10, -23, -10, 20),
            "Show Suffixed",
            callback=self.check_callback,
            value=False)
        self.w.open()
        # select the first item in the list and filter the glyph set
        # according to that selection
        self.w.myList.setSelection([0])
        self.sel_callback(self.w.myList)

    def get_range_from_edges(self, range_name):
        r_start, r_stop = reverse_ranges.get(range_name)
        u_range = range(r_start, r_stop + 1)
        return u_range

    def get_supported_range_names(self, codepoints):
        supported_range_names = []
        for range_name in reverse_ranges.keys():
            u_range = self.get_range_from_edges(range_name)
            if set(codepoints) & set(u_range):
                supported_range_names.append(range_name)
        # not sure it needs sorting or not
        return sorted(
            supported_range_names,
            key=lambda r: reverse_ranges.get(r)
        )
        # return supported_range_names

    def support_percentage(self, range_name):
        u_range = self.get_range_from_edges(range_name)
        u_range_clean = set(u_range) - set(ignore_codepoints)
        range_support = set(u_range_clean) & set(self.font_code_points)
        support_percentage = percentage(len(range_support), len(u_range_clean))
        return support_percentage

    def sel_callback(self, sender):
        sel_indices = sender.getSelection()
        range_names = []
        for sel_index in sel_indices:
            range_name = self.font_ranges[sel_index]
            range_names.append(range_name)
        self.selected_ranges = range_names
        self.select_ranges(range_names)

    def close_callback(self, sender):
        CurrentFontWindow().getGlyphCollection().setQuery(None)

    def check_callback(self, sender):
        self.select_suffix = sender.get()
        self.select_ranges(self.selected_ranges)

    def select_ranges(self, range_names):
        g_name_list = []
        for range_name in range_names:
            g_name_list.extend([
                g.name for g in self.f if
                g.unicode in self.get_range_from_edges(range_name)])

        if self.select_suffix:
            sel_list = [
                g.name for g in self.f if g.name.split('.')[0] in g_name_list]
        else:
            sel_list = g_name_list

        query = 'Name in {"%s"}' % '", "'.join(sel_list)
        query = AppKit.NSPredicate.predicateWithFormat_(query)
        CurrentFontWindow().getGlyphCollection().setQuery(query)


f = CurrentFont()
RangeList(f)