import os
import pyodbc
import utils.logsconfig as logsconfig

logger = logsconfig.logging.getLogger("bot")
from dotenv import load_dotenv
load_dotenv()

conncreate = pyodbc.connect('driver={%s};server=%s;database=%s;uid=%s;pwd=%s' % 
            (os.getenv('DRIVER'), os.getenv('SERVER'), os.getenv('DATABASE'), os.getenv('UID'), os.getenv('PASS')))

def highscore_to_db(scorelist):
        new_score = 1
        # Fetch Old score
        with conncreate.cursor() as cursor:
            query = """SELECT score_v2, song_clear FROM dbo.user_highscores WHERE 
            chart_id=? AND id=? AND chart_difficulty=?"""
            cursor.execute(query ,(scorelist[4], scorelist[2], scorelist[7]))
            for row in cursor:
                old_score = int(row.score_v2)
                old_clear = (row.song_clear)
                new_score = 0

        # If New Score
        if new_score:
            with conncreate.cursor() as cursor:
                query = """INSERT INTO dbo.user_highscores VALUES
                    (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
                cursor.execute(query,(
                    scorelist[4], # chart_id
                    scorelist[7], # chart_diff
                    scorelist[0], # score_id
                    scorelist[2], # id
                    scorelist[1], # usernick
                    scorelist[9], # cool
                    scorelist[10], # good
                    scorelist[11], # bad
                    scorelist[12], # miss
                    scorelist[13], # max combo
                    scorelist[14], # max jam
                    scorelist[15], # total score
                    scorelist[16], #  score v2
                    scorelist[17], #  accuracy
                    scorelist[18], # song clear
                    scorelist[19]))  # date_played
                cursor.commit()
                logger.info('[New Record][%s][%s] %s - %s : cool: %s good: %s bad: %s miss: %s [Max Combo:%s] [Acc: %s]  [Score: %s]' 
                % (scorelist[1] , scorelist[7],scorelist[5], scorelist[6], 
                scorelist[9], scorelist[10],scorelist[11],scorelist[12], 
                scorelist[13], round(scorelist[17],2) ,scorelist[16]))
                return True
            
        # If not a new score
        else:
            # If new score is not cleared
            if scorelist[18] == False: 
                # if old score is cleared
                if old_clear == True:
                    logger.info('[Verified][%s][%s] %s - %s : cool: %s good: %s bad: %s miss: %s [Max Combo:%s] [Acc: %s]  [Score: %s]' 
                    % (scorelist[1], scorelist[7],scorelist[5], scorelist[6], 
                    scorelist[9], scorelist[10],scorelist[11],scorelist[12], 
                    scorelist[13], round(scorelist[17],2) ,scorelist[16]))
                    return False
                else:
                    # if old score is higher than new score
                    if scorelist[16] < int(old_score):
                        logger.info('[Verified][%s][%s] %s - %s : cool: %s good: %s bad: %s miss: %s [Max Combo:%s] [Acc: %s]  [Score: %s]' 
                        % (scorelist[1], scorelist[7],scorelist[5], scorelist[6], 
                        scorelist[9], scorelist[10],scorelist[11],scorelist[12], 
                        scorelist[13], round(scorelist[17],2) ,scorelist[16]))
                        return False
                    else:
                        with conncreate.cursor() as cursor:
                            query = """UPDATE dbo.user_highscores SET 
                            score_id=?, cool=?, good=?, bad=?, miss=?, maxcombo=?,
                            maxjam=?, total_score=?, score_v2=?,
                            accuracy=?, song_clear=?, date_played=?
                            WHERE 
                            id=? AND chart_id=? AND chart_difficulty=?"""
                            cursor.execute(query, (  
                                scorelist[0],  # score_id
                                scorelist[9],  # cool
                                scorelist[10], # good
                                scorelist[11], # bad
                                scorelist[12], # miss
                                scorelist[13], # maxcombo
                                scorelist[14], # maxjam
                                scorelist[15], # total_score
                                scorelist[16], # score v2
                                scorelist[17], # accuracy
                                scorelist[18], # song clear
                                scorelist[19], # date_played

                                scorelist[2],  # id
                                scorelist[4],  # chart_id
                                scorelist[7])
                                )  # chart_diff
                            cursor.commit()
                            logger.info('[NEW HIGHSCORE][%s][%s] %s - %s : cool: %s good: %s bad: %s miss: %s [Max Combo:%s] [Acc: %s]  [Score: %s]' 
                            % (scorelist[1] , scorelist[7],scorelist[5], scorelist[6], 
                            scorelist[9], scorelist[10],scorelist[11],scorelist[12], 
                            scorelist[13], round(scorelist[17],2) ,scorelist[16]))
                            return True

            # If new score is cleared
            else:
                # if old score is cleared
                if old_clear == True:
                    # Compare each scores
                    if scorelist[16] < int(old_score):
                        logger.info('[Verified][%s][%s] %s - %s : cool: %s good: %s bad: %s miss: %s [Max Combo:%s] [Acc: %s]  [Score: %s]' 
                        % (scorelist[1], scorelist[7],scorelist[5], scorelist[6], 
                        scorelist[9], scorelist[10],scorelist[11],scorelist[12], 
                        scorelist[13], round(scorelist[17],2) ,scorelist[16]))
                        return False
                    
                with conncreate.cursor() as cursor:
                    query = """UPDATE dbo.user_highscores SET 
                    score_id=?, cool=?, good=?, bad=?, miss=?, maxcombo=?,
                    maxjam=?, total_score=?, score_v2=?,
                    accuracy=?, song_clear=?, date_played=?
                    WHERE 
                    id=? AND chart_id=? AND chart_difficulty=?"""
                    cursor.execute(query, (  
                        scorelist[0],  # score_id
                        scorelist[9],  # cool
                        scorelist[10], # good
                        scorelist[11], # bad
                        scorelist[12], # miss
                        scorelist[13], # maxcombo
                        scorelist[14], # maxjam
                        scorelist[15], # total_score
                        scorelist[16], # score v2
                        scorelist[17], # accuracy
                        scorelist[18], # song clear
                        scorelist[19], # date_played

                        scorelist[2],  # id
                        scorelist[4],  # chart_id
                        scorelist[7])
                        )  # chart_diff
                    cursor.commit()
                    logger.info('[NEW HIGHSCORE][%s][%s] %s - %s : cool: %s good: %s bad: %s miss: %s [Max Combo:%s] [Acc: %s]  [Score: %s]' 
                    % (scorelist[1] , scorelist[7],scorelist[5], scorelist[6], 
                    scorelist[9], scorelist[10],scorelist[11],scorelist[12], 
                    scorelist[13], round(scorelist[17],2) ,scorelist[16]))
                    return True