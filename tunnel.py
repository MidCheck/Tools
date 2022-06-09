#!/usr/bin/python3
import asyncio
import socket
import sys

class Tunnel:
    TUNNEL_DATA_SIZE = 65536

    def __init__(self, c_reader, c_writer, r_reader, r_writer, header: bytes):
        self.client_reader: asyncio.StreamReader = c_reader
        self.client_writer: asyncio.StreamWriter = c_writer
        self.remote_reader: asyncio.StreamReader = r_reader
        self.remote_writer: asyncio.StreamWriter = r_writer
        self.header_data = header
        self.is_running = True
        self.event = asyncio.Event()

    async def tunnel(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, header: bytes=None):
        if header:
            try:
                data = await reader.read(self.TUNNEL_DATA_SIZE)
                writer.write(header + data)
                await writer.drain()
            except Exception:
                self.is_running = False
                self.event.set()
                return
        
        while self.is_running:
            if reader.at_eof():
                await asyncio.sleep(1)
                continue
            try:
                data = await reader.read(self.TUNNEL_DATA_SIZE)
                writer.write(data)
                await writer.drain()
            except Exception:
                self.is_running = False
                self.event.set()

    async def close_tunnel(self):
        await self.event.wait()
        
        self.client_writer.close()
        await self.client_writer.wait_closed()
        self.remote_writer.close()
        await self.remote_writer.wait_closed()

    async def run(self):
        try:
            await asyncio.gather(
                self.tunnel(self.client_reader, self.remote_writer, self.header_data),
                self.tunnel(self.remote_reader, self.client_writer),
                self.close_tunnel()
            )
        except Exception as e:
            print("[-] gather:", str(e))
        

async def handle_connect(remote_addr: tuple, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    header = None
    # # filter unwanted data
    # header = await reader.read(4)
    # if header.startswith(b"GET ") or header.startswith(b"POST ") \
    #         or header.startswith(b"HEAD"):
    #     writer.close()
    #     await writer.wait_closed()
    #     return
    try:
        remote_ip, remote_port = socket.getaddrinfo(remote_addr[0], remote_addr[1])[0][4]
        remote_reader, remote_writer = await asyncio.open_connection(
            remote_ip, remote_port
        )
    except Exception as e:
        print("[-] connect remote failed:", str(e))
        writer.close()
        await writer.wait_closed()
        return
    
    print(f"[+] Connected: [{writer.get_extra_info('peername')}] -> [{remote_writer.get_extra_info('peername')}]")
    tunnel = Tunnel(reader, writer, remote_reader, remote_writer, header)
    await tunnel.run()

async def main(listening_port: int, remote_addr: tuple):
    server = await asyncio.start_server(
        lambda reader, writer: handle_connect(
            remote_addr, reader, writer
        ), "0.0.0.0", listening_port, 
    )

    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    print(f"Listening on {addrs}")

    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print('Usage: %s listening_port remote_host remote_port' % sys.argv[0])
        exit(-1)
    listening_port = int(sys.argv[1])
    remote_host = sys.argv[2]
    remote_port = int(sys.argv[3])
    asyncio.run(main(listening_port, (remote_host, remote_port)))
