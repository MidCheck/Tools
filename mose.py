#! /usr/bin/python
import sys

class MorseCoder: 
    __encode_alphabet = {
            "A": ".-", "B": "-...", "C": "-.-.", "D": "-..", # 加密对照表 
            "E": ".", "F": "..-.", "G": "--.", "H": "....", 
            "I": "..", "J": ".---", "K": "-.-", "L": ".-..", 
            "M": "--", "N": "-.", "O": "---", "P": ".--.", 
            "Q": "--.-", "R": ".-.", "S": "...", "T": "-", 
            "U": "..-", "V": "...-", "W": ".--", "X": "-..-", 
            "Y": "-.--", "Z": "--..", "1": ".---", "2": "..---", 
            "3": "...--", "4": "....-", "5": ".....", "6": "-....", 
            "7": "--...", "8": "---..", "9": "----.", "0": "-----", 
            "(": ".--.-", "-": "-....-", "?": "..--..", "/": "-..-.", 
            ".": ".-.-.-", "@": ".--.-." } 
    __decode_alphabet = dict([val, key] for key, val in __encode_alphabet.items()) # 解密对照表
    
    def encode(self, plaintext): 
        """Encode AscII chars in plaintext to morse code""" 
        charList = list(plaintext.upper()) 
        morsecodeList = [self.__encode_alphabet[char] if char in self.__encode_alphabet.keys() else " " for char in charList] 
        return " ".join(morsecodeList) 
    
    def decode(self, morsecode): 
        morsecodeList = morsecode.split(" ") 
        charList = [self.__decode_alphabet[char] if char in self.__decode_alphabet.keys() else char for char in morsecodeList] 
        return "".join(charList) 
    
    def get_encode_alphabet(self): 
        return self.__encode_alphabet 
    
    def get_decode_alphabet(self): 
        return self.__decode_alphabet 

if __name__ == '__main__': 
    mc = MorseCoder() 
    # plaintext = "abcdABCD12345678" 
    plaintext = sys.argv[1] if(len(sys.argv) > 1) else input();
    morsecode = mc.encode(plaintext) 
    print(morsecode) 
    #morsecode = ".. .-.. --- ...- . - .- -. . -.. .- .-. .. ... .-" 
    #plaintext = mc.decode(morsecode) 
    #print("decode result: ", plaintext) 
    mc.get_encode_alphabet() 
    mc.get_decode_alphabet()
