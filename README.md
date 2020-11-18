You can use this script to get comment and user information in a telegram channel. You must have your telegram api_hash and api_id. For information about obtaining your api information go here: https://core.telegram.org/api/obtaining_api_id

You will need python 3.x, and you can pip install this package:
pip install telethon==1.17.5

Open up the main python file and make sure you put the correct information in lines 7, 9, 11, 12, 16, and 17. 
Line 7 is your channel name. This is case sensitive and needs to be the channel name of the channel you wish to run this on. You MIGHT need admin privileges to run this.
Line 9 is the path to where you want to store your db. This needs to end in a .db see examples below:
example for pc: database = 'C:/Users/user/Desktop/Database_name.db'
example for mac/Linux: database = '/Users/user/SQL_db/Database_name.db'

Line 11 is your api_id. This has to be an integer, so it should not be surrounded by '. Example: api_id = 1111111
Line 12 is your api_has and needs to be a string, so it should be surrounded by '. Example: api_hash = '1111xxxxx111ccc1111cccc'

Lines 16 and 17 do not have ot have values. IF you want to search ALL records fromt he channel without time constraints, make sure from_date and to_date are both set = '' Example below:
from_date = ''
to_date = ''

If you want specific dates, enter them in YYYY-MM-DDD format.  The example below would give you stats for user messages between Jan 1 and Jun 1 of 2020:
from_date = '2020-01-01'
to_date = '2020-06-01'

The first time you run this program, you will have to enter your phone number. Telegram will send you a code through the app. You have to enter that code into the program in order to authenticate the program. 

If you have any questions, feel free to email me at: BPCullen@yahoo.com
