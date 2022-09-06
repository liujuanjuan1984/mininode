import os
import sys

this_repo = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, this_repo)
from mininode import MiniNode, create_private_key

pvtkey = create_private_key()
# pvtkey = "0x01d468448180b444ed197f4684f76df2201cd3938e697b26d0b439f797d7e1b4"
print(pvtkey)

seed = "rum://seed?v=1&e=0&n=0&b=wRJZSa5fQvOhhOBluJupaA&c=tBzr2eUUPkBteARtKEkyZF1C1IydXZwghG23L8ZH1sY&g=wgb-PvHZQHm2tFfS2eO5wA&k=AgZKtJqzwgFcfKpJm-91qoMx7WaDDhmKsWTKEX0Ri_co&s=xmyKvW03SM63qcCPXOoAAndXduFDTK9_VL5_qMhHUs56xsZ1rrAVra22c-T3HPg-e9Gyawc4c3fN0U7cr1IApQA&t=FxIuIx4VxGA&a=test&y=group_timeline&u=http%3A%2F%2F127.0.0.1%3A57772%3Fjwt%3DeyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhbGxvd0dyb3VwcyI6WyJjMjA2ZmUzZS1mMWQ5LTQwNzktYjZiNC01N2QyZDllM2I5YzAiXSwiZXhwIjoxODIwMTIxOTQxLCJuYW1lIjoiYWxsb3ctYzIwNmZlM2UtZjFkOS00MDc5LWI2YjQtNTdkMmQ5ZTNiOWMwIiwicm9sZSI6Im5vZGUifQ.ude-xq9rhnsRuILSvBz8HDuYndpqXu2B09Tz44NWdGQ"
bot = MiniNode(seed)

r = bot.api.send_content(pvtkey, content="hi", images=[r"D:\game\box.png"])
print(r)

r = bot.api.edit_trx(pvtkey, trx_id=r["trx_id"], content="hihihihi", images=[r"D:\game\box.png", r"D:\game\box.png"])
print(r)

r = bot.api.reply_trx(pvtkey, trx_id=r["trx_id"], content="回复你一个", images=[r"D:\game\box.png", r"D:\game\box.png"])
print(r)

r = bot.api.like(pvtkey, trx_id=r["trx_id"])
print(r)

r = bot.api.update_profile(pvtkey, name="testmininode", image=r"D:\game\box.png")
print(r)

r = bot.api.send_content(pvtkey, content="hi,again")
print(r)

trxs = bot.api.get_content(num=30, trx_types=["text_only"])
for trx in trxs:
    print(trx)
