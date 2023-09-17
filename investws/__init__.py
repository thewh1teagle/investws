import websockets
import asyncio
import random
import asyncio
import json
import random
import re
from typing import List, Callable
from pathlib import Path

class InvestWS:

    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'

    def __init__(self, pairs: List[str], on_update: Callable[[], dict]) -> None:
        self.url = self._generate_stream_url()

        json_path = Path(__file__).parent / 'pairs.json'
        json_path = json_path.resolve().absolute()
        with open(json_path) as f: # took from https://github.com/DavideViolante/investing-com-api/blob/master/mapping.js
            pairs_dict: dict = json.load(f)
        self.pids = []
        for pair in pairs:
            pair_info = pairs_dict.get(pair)
            if not pair_info:
                raise Exception(f'pair {pair} not found!')
            pid = pair_info['pairId']
            self.pids.append(pid)

        self.on_update = on_update

    def get_pairs() -> List[str]:
        json_path = Path(__file__).parent / 'pairs.json'
        json_path = json_path.resolve().absolute()
        with open(json_path) as f: # took from https://github.com/DavideViolante/investing-com-api/blob/master/mapping.js
            pairs_dict: dict = json.load(f)
        return list(pairs_dict.keys())



    async def start(self):
        async with websockets.connect(self.url, user_agent_header=self.USER_AGENT, ping_interval=None) as websocket:
            message = await websocket.recv()
            if message != 'o':
                raise Exception('Unxcpected initial message received!')
            await self._subscribe(websocket)
            asyncio.create_task(self._heartbeat_loop(websocket))
            await self._poll_messages(websocket)

    async def _subscribe(self, websocket):
        message_content = ''
        for pid in self.pids:
            message_content += f'%%pid-{pid}:'
        message = json.dumps({
            '_event': 'bulk-subscribe',
            'tzID': 8,
            'message': message_content
        })
        message = [message]
        message = json.dumps(message)

        await websocket.send(message)


        # some initial message
        message = json.dumps({
            '_event': 'UID',
            'UID': 0
        })
        message = json.dumps([message])
        await websocket.send(message)

    async def _poll_messages(self, websocket):
        async for message in websocket:
            await self._handle_raw_message(message)

    def _generate_stream_url(self, ):
        rnd = random.Random()

        return "wss://stream2{:02d}.forexpros.com/echo/{:03x}/{:08x}/websocket".format(
            rnd.randint(0, 99),
            rnd.randint(0, 0xfff),
            rnd.randint(0, 0xffffffff)
        )

    async def _heartbeat_loop(self, conn):
        data = json.dumps({'_event': 'heartbeat', 'data': 'h'})
        data = json.dumps([data])
        # heartbeat = "[\"{\\\"_event\\\":\\\"heartbeat\\\",\\\"data\\\":\\\"h\\\"}\"]"
        while True:
            await conn.send(data)
            await asyncio.sleep(3.2)

    async def _handle_message(self, message):
        match = re.match('pid-[0-9]+::(.+)', message)
        data = match.group(1)
        data: dict = json.loads(data)
        await self.on_update(data)

    async def _handle_raw_message(self, message):
        data = json.loads(message[1:])
        data[0] = json.loads(data[0])
        if not data:
            return
        raw_message = data[0]  # first message

        if not isinstance(raw_message, dict):
            return

        data = raw_message.get('message')
        if data:
            await self._handle_message(data)
