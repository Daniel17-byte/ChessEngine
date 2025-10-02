class MCTSNode:
    def __init__(self, board, parent=None, prior=1.0):
        self.board = board.copy()
        self.parent = parent
        self.children = {}  # move -> MCTSNode
        self.N = 0          # visit count
        self.W = 0.0        # total value
        self.P = prior      # prior probability from policy
    @property
    def Q(self):
        return self.W / self.N if self.N > 0 else 0.0
