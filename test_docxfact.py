from docxfactory import WordProcessingCompiler
from datetime import datetime
from docxfactory import WordProcessingMerger

try:
    compiler = WordProcessingCompiler.get_instance()

    start_time = datetime.now()

    compiler.compile("W:\\Documents\\Forward\\apatcher\\top_level_items.docx",
                     "W:\\Documents\\Forward\\apatcher\\top_level_items.dfw")

    print("Compiled (in", round((datetime.now() - start_time).total_seconds(), 3), " seconds).")

    merger = WordProcessingMerger.get_instance()
    merger.load("W:\\Documents\\Forward\\apatcher\\top_level_items.dfw")
    print(merger.get_fields())
    print(merger.get_items())

    merger.paste("Account")
    merger.set_clipboard_value("account", "", "Alex")

    merger.save("W:\\Documents\\Forward\\apatcher\\tmp\\top_level_items.docx")

except Exception as e:
    print(str(e))
