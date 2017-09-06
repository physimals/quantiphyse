import os, sys

from PySide import QtCore, QtGui

LOCAL_FILE_PATH=""

def set_local_file_path(path):
    global LOCAL_FILE_PATH
    LOCAL_FILE_PATH = path

def get_icon(name):
    """
    Get path to the named icon
    """
    global LOCAL_FILE_PATH
    name, extension = os.path.splitext(name)
    if extension == "":
        if sys.platform.startswith("win") or sys.platform.startswith("darwin"):
            extension = ".png"
        else:
            extension = ".svg"
    return os.path.join(LOCAL_FILE_PATH, "icons/%s%s" % (name, extension))

def get_local_file(name):
    """
    Get path to the named icon
    """
    global LOCAL_FILE_PATH
    return os.path.join(LOCAL_FILE_PATH, name)

def table_to_str(tabmod):
    """ Turn a QT table model into a TSV string """
    tsv = ""
    rows = range(tabmod.rowCount())
    cols = range(tabmod.columnCount())
    colheaders = ["",] + [tabmod.horizontalHeaderItem(col).text().replace("\n", " ") for col in cols]
    tsv += "\t".join(colheaders) + "\n"

    for row in rows:
        rowdata = [tabmod.verticalHeaderItem(row).text(),] 
        rowdata += [tabmod.item(row, col).text() for col in cols]
        tsv += "\t".join(rowdata) + "\n"
    #print(tsv)
    return tsv

def copy_table(tabmod):
    """ Copy a QT table model to the clipboard in a form suitable for paste into Excel etc """
    clipboard = QtGui.QApplication.clipboard()
    tsv = table_to-str(tabmod)
    clipboard.setText(tsv)

def get_col(cmap, idx, out_of):
    """ Get RGB color for an index within a range, using a Matplotlib colour map """
    if out_of == 0: 
        return [255, 0, 0]
    else:
        return [int(255 * rgbf) for rgbf in cmap(float(idx)/out_of)[:3]]

    return lut

# Kelly (1965) - set of 20 contrasting colours
# We alter the order a bit to prioritize those that give good contrast to our dark background
# plus we add an 'off white' at the start
KELLY_COLORS = [("off_white", (230, 230, 230)),
                ("vivid_yellow", (255, 179, 0)),
                ("vivid_orange", (255, 104, 0)),
                ("very_light_blue", (166, 189, 215)),
                ("vivid_red", (193, 0, 32)),
                ("grayish_yellow", (206, 162, 98)),
                ("medium_gray", (129, 112, 102)),
                ("strong_purple", (128, 62, 117)),

                # these aren't good for people with defective color vision:
                ("vivid_green", (0, 125, 52)),
                ("strong_purplish_pink", (246, 118, 142)),
                ("strong_blue", (0, 83, 138)),
                ("strong_yellowish_pink", (255, 122, 92)),
                ("strong_violet", (83, 55, 122)),
                ("vivid_orange_yellow", (255, 142, 0)),
                ("strong_purplish_red", (179, 40, 81)),
                ("vivid_greenish_yellow", (244, 200, 0)),
                ("strong_reddish_brown", (127, 24, 13)),
                ("vivid_yellowish_green", (147, 170, 0)),
                ("deep_yellowish_brown", (89, 51, 21)),
                ("vivid_reddish_orange", (241, 58, 19)),
                ("dark_olive_green", (35, 44, 22))
]

def get_kelly_col(idx):
    return KELLY_COLORS[idx % len(KELLY_COLORS)][1]
