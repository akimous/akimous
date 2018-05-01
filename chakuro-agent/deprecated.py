#import ssl
#from ssl import Purpose

#sslContext = ssl.create_default_context(Purpose.CLIENT_AUTH)
#sslContext.load_cert_chain('../../chakuro/cert.pem', '../../chakuro/key.pem')
#print(sslContext.verify_mode)
# print(sslContext.get_ciphers())

# class RoleSet:
#     def __init__(self):
#         self._roles = set()
#
#     def add_from_file(self, path):
#         with open(path, 'r') as f:
#             text = f.read()
#         print(text)
#         for match in re.findall(':\w+:`', text):
#             print(match)
#             # break
#
#
# role_set = RoleSet()
# role_set.add_from_file('cpython/Doc/library/array.rst')
