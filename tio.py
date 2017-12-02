import requests
import zlib

QUERY = 'Vlang\u00001\u0000jelly\u0000F.code.tio\u0000{}\u0000{}F.input.tio\u0000{}\u0000{}Vargs\u0000{}{}\u0000R'
URL = 'https://tio.run/cgi-bin/run/api/'

def sendreq(code, args, inputs):
    session = requests.Session()
    data = zlib.compress(bytes(QUERY.format(len(bytes(code, 'utf-8')), code, len(inputs), inputs, len(args), (len(args) * '\u0000{}').format(*args)), 'utf-8'), 9)[2:-4]
    returned = session.post(URL, data, verify=True, cookies=requests.utils.dict_from_cookiejar(session.cookies)).text
    sep = returned[:16]
    return returned[16:-17].split(sep)
