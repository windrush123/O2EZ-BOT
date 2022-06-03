import songlist
print("----- O2EZ Songlist Database Management ----- ")

def main():
    ans = input("""
[1] Import songlist.txt (For First time Setup).
[2] Add song to the mappool (update_songlist.txt).
[3] Bring back song to the mappool [...]
[4] Change song metadata (update_song_metadata.txt).
[5] Delete all data from songlist database.
Input: """)
    if ans == "1":
        ans2 = input("This will delete existing songlist and highscore data. Do you see you want to proceed...? [Y/N]\nInput: ")
        if any(ans2.lower() == f for f in ["yes", 'y', '1']):
            songlist.songlist_main()
            main()
        elif any(ans.lower() == f for f in ["no", 'n', '0']):
            main()  
        else: main()     
    elif ans == "2":
        songlist.update_songlist()
        main()
    elif ans == "3": #
        pass
    elif ans == "4":
        songlist.update_song_metadata()
        main()
    elif ans == "5":
        ans2 = input("Are you sure you want to delete all data in the database? [Y/N]\nInput: ")
        if any(ans2.lower() == f for f in ["yes", 'y', '1']):
            songlist.delete_songlist()
            main()
        elif any(ans.lower() == f for f in ["no", 'n', '0']):
            main()
        else: main()
    else: main()
main()
    