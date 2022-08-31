import os
import sys

this_repo = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, this_repo)
from mininode import MiniNode

# from mininode.crypto import create_private_key
# pvtkey = create_private_key()
pvtkey = "0x01d468448180b444ed197f4684f76df2201cd3938e697b26d0b439f797d7e1b4"
print(pvtkey)

seed = "rum://seed?v=1&e=0&n=0&b=9UBNEeARSVqa9J4CP3FlEg&c=jwd2eq5l6oYEK-jUD9Do8inSOiHGU_98L6uqCZJntAg&g=dXHTMHCJR8WPuZoi9WZrdg&k=A-Fnlz6u4wfr12F9E8IeWDWslKYlUMvd_NPpGQYR3L2h&s=J8eJQf2ixwqlSY-qlUH8Nj85iNN7kzFrXcnE4A_cVpY_21kG1FdiwaXkxfUa47PpYLV5vde9hK7co8NVZhtlXgE&t=Fw_PHXaq1uA&a=test11&y=group_timeline&u=http%3A%2F%2F127.0.0.1%3A57772%3Fjwt%3DeyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhbGxvd0dyb3VwcyI6WyI3NTcxZDMzMC03MDg5LTQ3YzUtOGZiOS05YTIyZjU2NjZiNzYiXSwiZXhwIjoxODE5NDU0NTEzLCJuYW1lIjoiYWxsb3ctNzU3MWQzMzAtNzA4OS00N2M1LThmYjktOWEyMmY1NjY2Yjc2Iiwicm9sZSI6Im5vZGUifQ.4W-0kaGOZbLy2cZPIWHf25wVQxu3yLwiKiYiOZLgcaI"
bot = MiniNode(seed)

r = bot.api.send_content(pvtkey, content="hi", images=[r"D:\game\box.png"])
print(r)

r = bot.api.edit_trx(pvtkey, trx_id=r["trx_id"], content="hihihihi", images=[r"D:\game\box.png", r"D:\game\box.png"])
print(r)

r = bot.api.like(pvtkey, trx_id=r["trx_id"])
print(r)


r = bot.api.update_profile(pvtkey, name="testmininode", image=r"D:\game\box.png")
print(r)

trxs = bot.api.get_content(num=10, trx_types=["text_only"])
for trx in trxs:
    print(trx)
