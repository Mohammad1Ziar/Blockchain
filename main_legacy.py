from block import Block

# create first block (genesis block)
block = Block(0, "First Block", "0")

print("Block Hash:", block.hash)
