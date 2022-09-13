import os
import sys

this_repo = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, this_repo)
from mininode import MiniNode, create_private_key

pvtkey = create_private_key()
# pvtkey = "0x01d468448180b444ed197f4684f76df2201cd3938e697b26d0b439f797d7e1b4"
print(pvtkey)

seed = "rum://seed?v=1&e=0&n=0&b=zIEz8KEhR5iZif_waw6WUQ&c=K61eHe7hv2jCfvTZwL9g2LbeWqDveXyWZzVAxxUIExw&g=a4vBF20HTTyxyegkgeYAfQ&k=AzpMoqDy4aUoW2-kFQhwHfy6T5p5XCi8VY5OCG5qyHN7&s=fA1e4wUYjNQeTHDwPruu9Bsx5kR6mwwEMwOkljRRc7BM-bVQkjDFjgwWgdeZIBbSfmJMdMBYxvWTBTV4slbn8AE&t=FxMhWf_H0dA&a=test_weibo&y=group_timeline&u=http%3A%2F%2F127.0.0.1%3A57772%3Fjwt%3DeyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhbGxvd0dyb3VwcyI6WyI2YjhiYzExNy02ZDA3LTRkM2MtYjFjOS1lODI0ODFlNjAwN2QiXSwiZXhwIjoxODIwMzg5MzU4LCJuYW1lIjoiYWxsb3ctNmI4YmMxMTctNmQwNy00ZDNjLWIxYzktZTgyNDgxZTYwMDdkIiwicm9sZSI6Im5vZGUifQ.w9BUzPm6ZsmhrH2hc9D8hBUUDyLg7UaTuNXpSmeR-OE"
bot = MiniNode(seed)

r = bot.api.send_content(pvtkey, content="hi", images=[r"D:\game\box.png"])
print(r)

r = bot.api.edit_trx(
    pvtkey,
    trx_id=r["trx_id"],
    content="hihihihi",
    images=[r"D:\game\box.png", r"D:\game\box.png"],
)
print(r)

r = bot.api.reply_trx(
    pvtkey,
    trx_id=r["trx_id"],
    content="回复你一个",
    images=[r"D:\game\box.png", r"D:\game\box.png"],
)
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
