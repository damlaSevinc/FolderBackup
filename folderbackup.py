import hashlib
import os
import shutil
import sys
import getopt
import logging
from time import sleep


def scanFolder(root_folder, relative_path=""):
    files = {}
    for file in os.listdir(root_folder):
        file_path = os.path.join(root_folder, file)
        if os.path.isfile(file_path):
            # get file name
            if relative_path == "":
                files.update({os.path.basename(file_path): getFilehash(file_path)})
            else:
                files.update(
                    {
                        relative_path
                        + os.sep
                        + os.path.basename(file_path): getFilehash(file_path)
                    }
                )
        elif os.path.isdir(file_path):
            # get folder name
            if relative_path == "":
                files.update(scanFolder(file_path, os.path.basename(file_path)))
            else:
                files.update(
                    scanFolder(
                        file_path, relative_path + os.sep + os.path.basename(file_path)
                    )
                )
    return files


def getFilehash(file):
    with open(file, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def syncFolders(source_files, destination_files, source_folder, destination_folder):
    # check files in source folder
    for file_name, hash in source_files.items():
        # check if file exists in destination folder
        if file_name not in destination_files:
            # join source folder path with file name
            src_file_path = os.path.join(source_folder, file_name)
            dest_file_path = os.path.join(destination_folder, file_name)
            # create folder if it doesn't exist
            if not os.path.exists(os.path.dirname(dest_file_path)):
                os.makedirs(os.path.dirname(dest_file_path))
                # copy file
            logging.info("Creating file: " + file_name)
            shutil.copy(src_file_path, dest_file_path)
        else:
            # check if file is different
            if hash != destination_files[file_name]:
                # copy file to destination folder
                logging.info("Copying file: " + file_name)
                src_file_path = os.path.join(source_folder, file_name)
                dest_file_path = os.path.join(destination_folder, file_name)
                # # copy file
                shutil.copy(src_file_path, dest_file_path)

    # check if files were removed from source folder
    for file_name, hash in destination_files.items():
        if file_name not in source_files:
            # remove file from destination folder
            logging.info("Removing file: " + file_name)
            file_path = os.path.join(destination_folder, file_name)
            os.remove(file_path)
            # check if folder is empty
            if not os.listdir(os.path.dirname(file_path)):
                os.rmdir(os.path.dirname(file_path))


def sync(source_folder, destination_folder):
    source_files = scanFolder(source_folder)
    destination_files = scanFolder(destination_folder)

    logging.debug("source files: " + str(source_files))
    logging.debug("destination files: " + str(destination_files))

    if destination_files != source_files:
        syncFolders(source_files, destination_files, source_folder, destination_folder)
        destination_files = source_files
    else:
        # No changes in source folder
        return


def main(args):
    try:
        opts, args = getopt.getopt(
            args, "hs:d:i:l:", ["source=", "destination=", "interval=", "log="]
        )
        source_folder = ""
        destination_folder = ""
        interval = ""
        log_file = ""
        for opt, arg in opts:
            if opt == "-h":
                print(
                    "folderbackup.py -s <source> -d <destination> -i <interval milliseconds> -l <log>"
                )
                sys.exit()
            elif opt in ("-s", "--source"):
                source_folder = arg.strip()
            elif opt in ("-d", "--destination"):
                destination_folder = arg.strip()
            elif opt in ("-i", "--interval"):
                interval = arg.strip()
            elif opt in ("-l", "--log"):
                log_file = arg

        if (
            source_folder == ""
            or destination_folder == ""
            or interval == ""
            or log_file == ""
        ):
            print("Missing arguments")
            print("correct usage: ")
            print(
                "folderbackup.py -s <source> -d <destination> -i <interval milliseconds> -l <log file>"
            )
            sys.exit(2)

        logging.basicConfig(
            encoding="utf-8",
            level=logging.INFO,
            format="%(asctime)s %(message)s",
            datefmt="%d/%m/%Y %I:%M:%S %p",
            handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
        )

        while True:
            # send absolute path to sync function
            sync(os.path.abspath(source_folder), os.path.abspath(destination_folder))
            sleep(int(interval) / 1000)

    except getopt.GetoptError:
        print(
            "main.py -s <source> -d <destination> -i <interval milliseconds> -l <log file>"
        )
        sys.exit(2)


if __name__ == "__main__":
    main(sys.argv[1:])
