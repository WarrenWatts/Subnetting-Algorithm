from pathlib import Path
from helpers import ExcelFileReader, CreateNetwork

def main():

    mainDir = Path.cwd()
    npviewDir = mainDir.joinpath("res")
    fileName = "AssetInventory.xlsx"
    onlyUseTheseCol = ["Name", "Type", "IP Address"]

    # Using List format as an example since multiple columns may need formatting.
    """NOTE: Make sure columns without a format value are given an empty string or 0 respectively.
    So, each column to format must have a format value for each of the respective variables to replace 
    even if they are empty. YOU must input them manually, at least for now since this is a work in progress..."""
    columnsToFormat = ["IP Address"]
    sep = [","]
    replaceVal = ["\""]
    intToSliceChars = [1]

    npviewInventory = ExcelFileReader(npviewDir, fileName, onlyUseTheseCol)
    npviewInventory.reformatData(columnsToFormat, sep, replaceVal, intToSliceChars)
    npviewData = npviewInventory.getData()
    print(f"{npviewData}\n")

    newNet = CreateNetwork(npviewData)
    newNet.assetInventoryNodes()
    newNet.findAndSortAllNetworks()
    newNet.subnetDetermination()
    print(newNet.getNodeDict())

if __name__ == "__main__":
    main()