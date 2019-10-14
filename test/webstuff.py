import requests
import zlib

TIOQUERY = 'Vlang\u00001\u0000jelly\u0000F.code.tio\u0000{}\u0000{}F.input.tio\u0000{}\u0000{}Vargs\u0000{}{}\u0000R'
TIOURL = 'https://tio.run/cgi-bin/run/api/'

KEY = 'LsKipr*3F6CmnQp5oQpM9w(('
SEARCHQUERY = 'https://api.stackexchange.com/2.2/search?order=desc&sort=votes&tagged=code-golf&site=codegolf&key='
# 1: Latest year
# 2: Vote minimum
# 3: Vote maximum
# 4: '%5b' + '%5b%20%5d'.join(<tags>) + '%5d'

def sendtioreq(code, args, inputs):
    session = requests.Session()
    data = zlib.compress(bytes(TIOQUERY.format(len(bytes(code, 'utf-8')), code, len(inputs), inputs, len(args), (len(args) * '\u0000{}').format(*args)), 'utf-8'), 9)[2:-4]
    returned = session.post(TIOURL, data, verify=True, cookies=requests.utils.dict_from_cookiejar(session.cookies)).text
    sep = returned[:16]
    return returned[16:-17].split(sep)

def sendsereq(year='2013', min_votes='20', max_votes='', *tags):
    session = requests.Session()
    quests = session.get(SEARCHQUERY)
    return quests.json()

if __name__ == '__main__':
    print(sendsereq())
    
