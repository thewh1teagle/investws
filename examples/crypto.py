from investws import InvestWS
import asyncio

async def main():
    api = InvestWS()
    async for message in api.listen(['crypto/ton', 'crypto/bitcoin/btc-usd']): # use get_pairs for list of all
        name = message['pair']['name']
        price = message.get('last_numeric')
        print(f'{name}: {price}')
    await api.close()
    
asyncio.run(main())