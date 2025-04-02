from ftplib import FTP
import re



def findUrlInString(string):
    # findall() has been used
    # with valid conditions for urls in string
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex, string)
    return [x[0] for x in url]



def DownloadNewFiles(feed):
    host_name = feed.ftp_host
    user = feed.ftp_user
    password = feed.ftp_pass
    path = "/"
    file = feed.file_pattern

    print("Starting connection to {}.".format(host_name))
    
    ftp = FTP(host_name)
    ftp.login(user=user, passwd=password)

    print("Successfully logged in to {}.".format(host_name))

    print("Starting download of {}.".format(file))

    data = []
    def handle_binary(more_data):
        data.append(more_data)

    resp = ftp.retrbinary("RETR " + str(file), callback=handle_binary)
    
    print("Download completed, decoding data...")

    # Decode bytes to string using UTF-8 (common for XML)
    data = b"".join(data).decode('utf-8')  # Join bytes first, then decode
    
    print("Decoding completed")

    print("Closing connection to {}.".format(host_name))
    
    ftp.quit()
    return data

    # if str(path) != "":
    #     ftp.cwd(path)

    # for file in files:
    #     print("downloading {}.".format(file))

    #     with open(file, "wb") as fp:
    #         ftp.retrbinary(f"RETR {file}", fp.write)
    #     fetched_files.append(file)
    #     print("download completed.")
    # ftp.quit()

    # print("Moving files: ")
    # for file in fetched_files:
    #     shutil.move(str(file), os.path.join(settings.PATH_TO_PRODUCT_FEEDS, file))
    #     print("moved {} to its final location".format(file))