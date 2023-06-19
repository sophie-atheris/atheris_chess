import Atheris as a
import time as t


with open('test_positions') as f:
    positions = f.readlines()
game = a.Board(positions[1])

start = t.process_time()
for _ in range(10000000):
    game.evaluate()
print(t.process_time()-start)


board, turn = a2.array_from_fen(positions[1])
start = t.process_time()
for _ in range(10000000):
    a2.evaluate_position(board)
print(t.process_time()-start)
