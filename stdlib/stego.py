from PIL import Image 
import sys
sys.path.append("../src")

import data as data
import errors as errors
import wave

def encode_wav(carrier, out, outfile):
  song = wave.open(carrier.val, mode='rb')

  frame_bytes = bytearray(list(song.readframes(song.getnframes())))


  string = out.val

  string = string + int((len(frame_bytes)-(len(string)*8*8))/8) *'#'

  bits = list(map(int, ''.join([bin(ord(i)).lstrip('0b').rjust(8,'0') for i in string])))


  for i, bit in enumerate(bits):
      frame_bytes[i] = (frame_bytes[i] & 254) | bit

  frame_modified = bytes(frame_bytes)


  with wave.open(outfile.val, 'wb') as fd:
      fd.setparams(song.getparams())
      fd.writeframes(frame_modified)
  song.close()

def decode_wav(carrier):
  song = wave.open(carrier.val, mode='rb')
  
  frame_bytes = bytearray(list(song.readframes(song.getnframes())))

  
  extracted = [frame_bytes[i] & 1 for i in range(len(frame_bytes))]
  
  string = "".join(chr(int("".join(map(str,extracted[i:i+8])),2)) for i in range(0,len(extracted),8))
  
  decoded = string.split("###")[0]

  
  
  song.close()
  return data.String(decoded)
  
def genData(data): 
          
        # list of binary codes 
        # of given data 
        newd = []  
          
        for i in data: 
            newd.append(format(ord(i), '08b')) 
        return newd 
          
def modPix(pix, data): 
      
    datalist = genData(data) 
    lendata = len(datalist) 
    imdata = iter(pix) 
  
    for i in range(lendata): 
          
        pix = [value for value in imdata.__next__()[:3] +
                                  imdata.__next__()[:3] +
                                  imdata.__next__()[:3]] 
                                      
        for j in range(0, 8): 
            if (datalist[i][j]=='0') and (pix[j]% 2 != 0): 
                  
                if (pix[j]% 2 != 0): 
                    pix[j] -= 1
                      
            elif (datalist[i][j] == '1') and (pix[j] % 2 == 0): 
                pix[j] -= 1

        if (i == lendata - 1): 
            if (pix[-1] % 2 == 0): 
                pix[-1] -= 1
        else: 
            if (pix[-1] % 2 != 0): 
                pix[-1] -= 1
  
        pix = tuple(pix) 
        yield pix[0:3] 
        yield pix[3:6] 
        yield pix[6:9] 
  
def encode_enc(newimg, data): 
    w = newimg.size[0] 
    (x, y) = (0, 0) 
      
    for pixel in modPix(newimg.getdata(), data): 
          
        # Putting modified pixels in the new image 
        newimg.putpixel((x, y), pixel) 
        if (x == w - 1): 
            x = 0
            y += 1
        else: 
            x += 1
              
# Encode data into image 
def encode(carrier, out, outfile): 
    img = carrier.val
    image = Image.open(img, 'r') 
      
    out = out.val
    if (len(out) == 0): 
        raise ValueError('Data is empty') 
          
    newimg = image.copy() 
    encode_enc(newimg, out) 
      
    new_img_name = outfile.val
    newimg.save(new_img_name, str(new_img_name.split(".")[1].upper())) 
  
def decode(carrier): 
    img = carrier.val
    image = Image.open(img, 'r') 
      
    out = '' 
    imgdata = iter(image.getdata()) 
      
    while (True): 
        pixels = [value for value in imgdata.__next__()[:3] +
                                  imgdata.__next__()[:3] +
                                  imgdata.__next__()[:3]] 
        binstr = '' 
          
        for i in pixels[:8]: 
            if (i % 2 == 0): 
                binstr += '0'
            else: 
                binstr += '1'
                  
        out += chr(int(binstr, 2)) 
        if (pixels[-1] % 2 != 0): 
            return data.String(out)

attrs = {
  'encode':     data.Method(encode),
  'decode':     data.Method(decode),
  'encode_wav': data.Method(encode_wav),
  'decode_wav': data.Method(decode_wav),
}
