from poe_api_wrapper import PoeApi

from poe_api_wrapper import AsyncPoeApi
import asyncio

tokens = {
    "p-b": r"aXIj0yshxMVZe5EQrj-Xqw%3D%3D",
    "p-lat": r"SPKVAm2Ep57juUJo5%2Bb%2FW1RhwSyiLYGakXqaOwpd8A%3D%3D",
    "formkey": r"f6e323b2f1d43ecd5834b7f43627ecc5",
    "__cf_bm": r"j6TQopuSTecEBdkGzH6CpyHPsaiy8ug9l8rNbhRe_DA-1730408522-1.0.1.1-BbFwbHVuUippDE9dr81I3TLp17w81yy2z.qgzkOXD_Lct_mpAHRmmktdS6nZGFwdF9M8phzt3fZUeN43inZg7w",
    "cf_clearance": r"4Kjd1IlcvAOSA3uqHekE1.oODj7h.kQn7IDz0pQMJGI-1730406185-1.2.1.1-n7E25aq.oovFIhsdahgfJjx9Ce5VRtOIgSJkw.Vu.aBTNEZmiuNDZlfknQae1lFWLz06aETDbHILsAZ43ue446C6EKCJLYkX0bgzEUj5Xi39qApomRR.W1WL8Q4ttUA6Xg6Z9PPaH0nKXtSLWq8RanHdiYp7pm4qwxEDFIghKxV1qMxFl_X5PwVYopJFVvQgHclBBWWSzDVqpyCPKPumMe8GrsEgYT9zqZJVRB47msiIVMKUZVYINwRSygRiHsKTdvbpZLVJkUxV4gKIE0esLTCzNG6FQySXJ4aVLSGRswzUdR0yByX69tou6dbVXdjX8vsTUWgZhvUQqdo__xjTQGN7byyX3y9mjhFr9Q3f0Uyypch1UUm51QCZAVdlBG3Zq7UiN6BYiUyJkmJ7Bga3wA"
}

async def main():
    client = await AsyncPoeApi(tokens=tokens).create()
    message = "Explain quantum computing in simple terms"
    async for chunk in client.send_message(bot="gpt3_5", message=message):
        print(chunk["response"], end='', flush=True)
        
asyncio.run(main())