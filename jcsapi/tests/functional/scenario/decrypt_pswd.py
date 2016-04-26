import base64
from Crypto.PublicKey import RSA
import binascii

def pkcs1_unpad(text):
    #From http://kfalck.net/2011/03/07/decoding-pkcs1-padding-in-python
    if len(text) > 0 and text[0] == '\x02':
        # Find end of padding marked by nul
        pos = text.find('\x00')
        if pos > 0:
            return text[pos+1:]
    return None

def long_to_bytes (val):
    try:
        #Python < 2.7 doesn't have bit_length =(
        width = val.bit_length()
    except:
        width = len(val.__hex__()[2:-1]) * 4
    # unhexlify wants an even multiple of eight (8) bits, but we don't
    # want more digits than we need (hence the ternary-ish 'or')
    width += 8 - ((width % 8) or 8)
    fmt = '%%0%dx' % (width // 4)
    s = binascii.unhexlify(fmt % val)
    return s

def decryptPassword(rsaKey, password):
    encryptedData = base64.b64decode(base64.b64decode(password))
    ciphertext = int(binascii.hexlify(encryptedData), 16)
    plaintext = rsaKey.decrypt(ciphertext)
    decryptedData = long_to_bytes(plaintext)
    unpaddedData = pkcs1_unpad(decryptedData)
    return unpaddedData


if __name__ == "__main__":
            keyFile = open("vis.pem", "r")
   	    keyLines = keyFile.readlines()
            try:
                key = RSA.importKey(keyLines)
            except ValueError, ex:
                print "Could not import SSH Key (Is it an RSA key? Is it password protected?): %s" % ex
                sys.exit(-1)
            password = "UklGaFNEa3ZBR2FCa3NNZEtGRmhzajFTV1BuRG1qNVpRT2lqaTl2aGxYT1lBaGNBN1NidUJYdXlRUDJGWnBvcG4xZnlpajRscU9MQWZ6WGkvM044YWRIYmFVQXVpWkx2M3BmOEtXdGt2R1ptTWMwVVplZUVxeW9kNmdEd0dOTWtFczRLV082RFlBZStyNGZNSDZUTmhkZGNZdy93Smp4TW9PTTZqUk41d3Yrb0lTcis5OEJMRE9sTStUVFVTdWZHZW5QdEVoeHRxL1NIRVJ4dkd0TGp4S2VYVk1PYk0rcjRkd21LUGlRY1FlWUtzN291Sk90UE1RSCtSTEZZTG1vRHg1Z2VuQkhVR0hkQ25LSjVteWdZWENzQzJNaFVZaGVSNzNsYTdBZm1mVi96Vk1BU3VUd1hickd4NDl5dTZyUEhKQzRrM2ZJM1F1akdNelUyaEt6MUN3PT0="
            print decryptPassword(key,password)		 

