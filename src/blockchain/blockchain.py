from .block import Block

class Blockchain:
    blocks: list[Block]
    complexity: int

    def __init__(self, complexity):
        self.complexity = complexity
        genesis = Block("", None, complexity)
        self.blocks = [ genesis ]

    def add(self, data):
        block = Block(self.blocks[-1].hash, data, self.complexity)
        block.mine()
        self.blocks.append( block )

    def add_multiple(self, items):
        for item in items:
            self.add(item)

    def validate(self):
        for i in range(1, len(self.blocks)):
            if not self.blocks[i].valid(self.blocks[i-1]):
                return False
        return True

    def search(self, block_hash):
        for block in self.blocks:
            if block.hash == block_hash:
                return block
        return None

    def print(self):
        for block in self.blocks:
            print(block)
