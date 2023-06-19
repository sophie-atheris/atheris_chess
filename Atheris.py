from copy import deepcopy


Point = tuple[int, int]
BoardArray = list[list[list[int]]]


class Board:
    def __init__(self, fen):
        with open('piece_tables') as g:
            ls = g.readlines()
        ls = [[int(x) for x in l.strip().split(', ')] for l in ls if l[0] != '#']
        self.board, self.turn = array_from_fen(fen)
        self.half_moves = 0
        self.past_states = []
        self.result = None
        self.input = None
        self.last_move = None
        self._move_functions = (
            self.gen_all_pawn_moves,
            self.gen_knight_moves,
            self.gen_bishop_moves,
            self.gen_rook_moves,
            self.gen_queen_moves,
            self.gen_all_king_moves,
        )
        self._tables = [
            (ls[0:8], 100),
            (ls[8:16], 320),
            (ls[16:24], 330),
            (ls[24:32], 500),
            (ls[32:40], 900),
            (ls[40:48], 0),
        ]

    def display_board(self, **kwargs):
        persp = kwargs.get("persp", True)
        print(f"Side to play: {'White' if self.turn else 'Black'}")
        for i in range(1, 9):
            print('\n', 9 - i, end=' ')
            for j in range(8):
                print(display_int(self.board[-i][j][0], self.board[-i][j][2]), end=' ')
            print('|', end='')
        print("\n    a  b c d e f g h\n")
        print(
            f"Moves: {self.half_moves // 2}, Result: {'Playing' if self.result is None else self.result}"
        )

    def is_threefold(self):
        repetitions = 0
        current = fen_from_array(self.board, self.turn)
        for i in range(len(self.past_states)):
            if self.past_states[i] == current:
                repetitions += 1
        result = "Threefold" if repetitions >= 2 else None

    def set_input(self, move: str) -> bool:
        try:
            move = move.strip().lower()
            if move == "resign":
                self.result = f"{'White' if self.turn else 'Black'} resigned."
                self.input = None
                return True
            if all(
                (
                    len(move) == 4,
                    move[0] in col_dict,
                    move[2] in col_dict,
                    int(move[1]) in range(1, 9),
                    int(move[3]) in range(1, 9),
                )
            ):
                coords = (
                    (int(move[1]) - 1, col_dict[move[0]]),
                    (int(move[3]) - 1, col_dict[move[2]]),
                )
                piece_color = self.board[coords[0][0]][coords[0][1]][2]
                if piece_color == self.turn and self.result is None:
                    self.input = coords
                    return True
        except (IndexError, ValueError):
            print(90)
        return False

    def execute_input(self) -> bool:  # AKA play_move()
        if self.input is None:
            return False
        if self.input[1] not in self.fetch_moves(self.input[0]):
            print(95)
            return False
        if self.move_piece():
            print(97)
            self.turn = not self.turn
            # TODO After every move, update prior move to store potential en passant, but also after each simulation

    def move_piece(self) -> bool:
        p1, p2 = self.input[0], self.input[1]
        tile_1 = self.board[p1[0]][p1[1]]
        tile_2 = self.board[p2[0]][p2[1]]
        backup = (deepcopy(self.board), self.turn, self.last_move)

        if tile_1[2] != self.turn:
            print("Wrong Turn")
            return False

        if tile_1[0] == 1 and (
            self.turn and p2[0] == 7 or not self.turn and p2[0] == 0
        ):  # Promotion
            promotion = input("Promote to q, n, b, r?").strip().lower()
            if promotion not in ("q", "n", "b", "r"):
                promotion = "q"
            tile_2[0] = piece_dict[promotion]
        else:  # Normal move
            print(123)
            tile_2[0] = tile_1[0]

        if all((tile_1[0] == 6, p1[1] == 4, p2[1] in (2, 6))):  # Castling
            if self.turn:
                if p2[1] == 6:  # white short castle
                    self.board[0][7] = [0, 1, 0]
                    self.board[0][5] = [4, 1, 1]
                if p2[1] == 2:  # white long castle
                    self.board[0][0] = [0, 1, 0]
                    self.board[0][3] = [4, 1, 1]
            else:
                if p2[1] == 6:  # black short castle
                    self.board[7][7] = [0, 1, 0]
                    self.board[7][5] = [4, 1, 0]
                if p2[1] == 2:  # black long castle
                    self.board[7][0] = [0, 1, 0]
                    self.board[7][3] = [4, 1, 0]

        tile_2[1:3] = [1, tile_1[2]]
        self.board[p1[0]][p1[1]] = [0, 1, 0]

        if (
            self.fetch_attackers(self.find_king(self.turn), self.turn)
            or self.result is not None
        ):
            self.board, self.turn, self.last_move = backup
            return False

        k1 = self.find_king(self.turn)
        k2 = self.find_king(not self.turn)
        for a1 in self.fetch_attackers(k2, not self.turn):
            attacker = self.board[a1[0]][a1[1]][0]
            if self.is_checkmate(a1, k2, not self.turn):
                print(f"Checkmate: {'white' if self.turn else 'black'} wins")
                self.result = "checkmate_white"

        if self.result is None and self.is_stalemate():
            print("Stalemate")
            self.result = "stalemate"

        if self.result is None and self.is_threefold():
            print("Draw by Threefold Repetition")
            self.result = "threefold"

        return True

    def update(self, p1: Point, p2: Point):
        tile_1 = self.board[p1[0]][p1[1]]
        self.board[p2[0]][p2[1]] = [tile_1[0], 1, tile_1[2]]
        self.board[p1[0]][p1[1]] = [0, 1, 0]

    def fetch_moves(self, p1: Point) -> list[Point]:
        tile = self.board[p1[0]][p1[1]]
        k1 = self.find_king(tile[2])
        return (
            self._move_functions[tile[0] - 1](p1, k1, tile[2])
            if tile[0] and k1 is not None
            else []
        )

    def find_king(self, side: int) -> Point:
        for i in range(8):
            for j in range(8):
                if self.board[i][j][0] == 6 and self.board[i][j][2] == side:
                    return i, j
        return 0, 0

    def check_king(self, k1: Point, p1: Point, p2: Point, king_side: int) -> bool:
        tile_1 = self.board[p1[0]][p1[1]]
        tile_2 = self.board[p2[0]][p2[1]]
        stored_data = (
            tile_1[0],
            tile_1[1],
            tile_1[2],
            tile_2[0],
            tile_2[1],
            tile_2[2],
        )
        self.update(p1, p2)
        in_check = True if self.fetch_attackers(k1, king_side) else False
        if (k1, p1, p2) == ((4, 4), (5, 4), (4, 4)):
            print(196, in_check)
            print(197, k1, king_side)
        self.board[p1[0]][p1[1]] = [stored_data[0], stored_data[1], stored_data[2]]
        self.board[p2[0]][p2[1]] = [stored_data[3], stored_data[4], stored_data[5]]
        return in_check

    def gen_castling_moves(self, p1: Point, kr_side: int) -> list[Point]:
        output = []
        i = 0 if kr_side else 7
        rook = 4
        king = 6
        king_j = 2
        rook_i = 0
        rook_j = 3
        extra = self.board[0][1][0] == 0
        for long in (0, 1):
            if not long:
                king_j, rook_i, rook_j, extra = 6, 7, 5, True
            king_legal = self.board[i][4][0] == king and self.board[i][4][1] == 0
            rook_legal = self.board[i][rook_i] == rook and self.board[i][rook_i][1] == 0
            check = all(
                (
                    not self.fetch_attackers((i, 4), kr_side),
                    not self.fetch_attackers((i, king_j), kr_side),
                    not self.fetch_attackers((i, rook_j), kr_side),
                    self.board[i][rook_j][0] == 0,
                    self.board[i][king_j][0] == 0,
                    extra,
                    king_legal,
                    rook_legal,
                )
            )
            if check and long:
                output.append((i, 2))
            if check and not long:
                output.append((i, 6))
        return output

    def gen_knight_moves(self, p1: Point, k1: Point, piece_side: int) -> list[Point]:
        output = []
        for dx, dy in (
            (1, 2),
            (1, -2),
            (-1, 2),
            (-1, -2),
            (2, 1),
            (2, -1),
            (-2, 1),
            (-2, -1),
        ):
            p2 = p1[0] + dx, p1[1] + dy
            if not 0 <= p2[0] <= 7 or not 0 <= p2[1] <= 7:
                continue
            tile = self.board[p2[0]][p2[1]]
            if any(
                (
                    tile[0] != 0 and tile[2] == piece_side,
                    self.check_king(k1, p1, p2, piece_side),
                )
            ):
                continue
            output.append(p2)
        return output

    def gen_king_moves(self, p1: Point, k1: Point, piece_side: int) -> list[Point]:
        output = []
        for dx, dy in (
            (1, 1),
            (1, 0),
            (1, -1),
            (0, 1),
            (0, -1),
            (-1, 1),
            (-1, 0),
            (-1, -1),
        ):
            p2 = p1[0] + dx, p1[1] + dy
            if not 0 <= p2[0] <= 7 or not 0 <= p2[1] <= 7:
                continue
            tile = self.board[p2[0]][p2[1]]
            if all((tile[0] != 0, tile[2] == piece_side)) or self.check_king(
                p2, p1, p2, piece_side
            ):
                continue
            if (dx, dy) == (-1, 0):
                print(280, self.check_king(k1, p1, p2, piece_side), k1, p1, p2, piece_side)
            output.append(p2)
        return output

    def gen_pawn_moves(self, p1: Point, k1: Point, piece_side: int) -> list[Point]:
        output = []
        direct = 1 if piece_side else -1
        for dist in (1, 2):
            row_i = p1[0] + dist * direct
            if not 0 <= row_i <= 7:
                break
            tile = self.board[row_i][p1[1]]
            if tile[0] != 0 or (dist == 2 and not (p1[0] == 1 or p1[0] == 6)):
                break
            if not self.check_king(k1, p1, (row_i, p1[1]), piece_side):
                output.append((row_i, p1[1]))

        for i in (-1, 1):
            p2 = p1[0] + direct, p1[1] + i
            if not 0 <= p2[0] <= 7 or not 0 <= p2[1] <= 7:  # Bounds check
                continue
            tile = self.board[p2[0]][p2[1]]
            if tile[0] == 0 or tile[2] != piece_side:
                continue
            output.append(p2)
        return output

    def gen_passant(self, p1: Point, k1: Point, piece_side: int) -> list[Point]:
        if self.last_move is None:
            return []
        p2 = (p1[0] + 1 if piece_side else -1, self.last_move[1][1])
        return (
            []
            if any(
                (
                    self.last_move is None,
                    piece_side and p1[0] != 4,
                    not piece_side and p1[0] != 3,
                    not abs(self.last_move[1][1] - p1[1]) == 1,
                    not abs(self.last_move[0][0] - self.last_move[1][0]) == 2,
                    self.check_king(k1, p1, p2, piece_side),
                )
            )
            else [p2]
        )

    def gen_ray_moves(
        self, p1: Point, k1: Point, piece_side: int, toggle: tuple[bool, bool]
    ) -> list[Point]:
        output = []
        comp = [
            (1, 1),
            (-1, -1),
            (-1, 1),
            (1, -1),
            (0, 1),
            (1, 0),
            (0, -1),
            (-1, 0),
        ]
        if toggle[0] and not toggle[1]:
            comp = comp[0:4]
        elif not toggle[0] and toggle[1]:
            comp = comp[4:8]

        for dx, dy in comp:
            for i in range(1, 8):
                p2 = p1[0] + i * dx, p1[1] + i * dy
                if not 0 <= p2[0] <= 7 or not 0 <= p2[1] <= 7:
                    continue
                tile = self.board[p2[0]][p2[1]]
                if any(
                    (
                        tile[0] != 0 and tile[2] == piece_side,
                        self.check_king(k1, p1, p2, piece_side),
                    )
                ):
                    break

                output.append(p2)
                if tile[0] == 0:
                    continue
                if tile[2] != piece_side:
                    break
        return output

    def gen_queen_moves(self, p1: Point, k1: Point, piece_side: int) -> list[Point]:
        return self.gen_ray_moves(p1, k1, piece_side, (True, True))

    def gen_bishop_moves(self, p1: Point, k1: Point, piece_side: int) -> list[Point]:
        return self.gen_ray_moves(p1, k1, piece_side, (True, False))

    def gen_rook_moves(self, p1: Point, k1: Point, piece_side: int) -> list[Point]:
        return self.gen_ray_moves(p1, k1, piece_side, (False, True))

    def gen_all_king_moves(self, p1: Point, k1: Point, piece_side: int) -> list[Point]:
        return self.gen_king_moves(p1, k1, piece_side) + self.gen_castling_moves(
            p1, piece_side
        )

    def gen_all_pawn_moves(self, p1: Point, k1: Point, piece_side: int) -> list[Point]:
        return self.gen_pawn_moves(p1, k1, piece_side) + self.gen_passant(p1, k1, piece_side)

    def ray_checks(self, p1: Point, side: int) -> list[Point]:
        output = []
        directions = (
            ((1, 1), (-1, 1), (1, -1), (-1, -1)),
            ((0, 1), (1, 0), (0, -1), (-1, 0)),
        )
        for d in (0, 1):
            x = 3 if d == 0 else 4
            for dx, dy in directions[d]:
                for i in range(1, 8):
                    p2 = p1[0] + dx * i, p1[1] + dy * i
                    if not 0 <= p2[0] <= 7 or not 0 <= p2[1] <= 7:
                        break
                    tile = self.board[p2[0]][p2[1]]
                    if tile[0] == 0:
                        continue
                    opponent = tile[2] != side
                    if not opponent or tile[0] not in (x, 5):
                        break
                    output.append(p2)
                    break
        return output

    def knight_checks(self, p1: Point, side: int) -> list[Point]:
        output = []
        for dx, dy in (
            (1, 2),
            (1, -2),
            (-1, 2),
            (-1, -2),
            (2, 1),
            (2, -1),
            (-2, 1),
            (-2, -1),
        ):
            p2 = p1[0] + dx, p1[1] + dy
            if not 0 <= p2[0] <= 7 or not 0 <= p2[1] <= 7:
                continue
            tile = self.board[p2[0]][p2[1]]
            if tile[0] == 0:
                continue
            opponent = tile[2] != side
            if tile[2] == side or tile[0] != 2:
                continue
            output.append(p2)
        return output

    def pawn_checks(self, p1: Point, side: int) -> list[Point]:
        output = []
        direct = 1 if side else -1
        for i in (-1, 1):
            p2 = p1[0] + direct, p1[1] + i
            if not 0 <= p2[0] <= 7 or not 0 <= p2[1] <= 7:
                continue
            tile = self.board[p2[0]][p2[1]]
            if tile[0] != 1 or tile[2] == side:
                continue
            output.append(p2)
        return output

    def king_checks(self, p1: Point, side: int) -> list[Point]:
        output = []
        for dx, dy in (
            (1, 1),
            (1, 0),
            (1, -1),
            (0, 1),
            (0, -1),
            (-1, 1),
            (-1, 0),
            (-1, -1),
        ):
            p2 = p1[0] + dx, p1[1] + dy
            if not 0 <= p2[0] <= 7 or not 0 <= p2[1] <= 7:
                continue
            tile = self.board[p2[0]][p2[1]]
            if tile[0] != 6 or tile[2] == side:
                continue
            output.append(p2)
        return output

    def fetch_attackers(self, p1: Point, side: int) -> list[Point]:
        return (
            self.king_checks(p1, side)
            + self.pawn_checks(p1, side)
            + self.knight_checks(p1, side)
            + self.ray_checks(p1, side)
        )

    def is_checkmate(self, a1: Point, k1: Point, side: int) -> bool:
        tile_1 = self.board[k1[0]][k1[1]]
        tile_2 = self.board[a1[0]][a1[1]]

        if any((tile_1[0] != 6, tile_2[2] == tile_1[2], self.fetch_moves(k1))):
            print(484)
            print((tile_1[0] != 6, tile_2[2] == tile_1[2], self.fetch_moves(k1)))
            return False

        for a2 in self.fetch_attackers(a1, side):
            if self.board[a2[0]][a2[1]][0] == 6:
                if not self.fetch_attackers(a1, not side):
                    print(490)
                    return False
            else:
                print(493)
                return False

        if tile_2[0] == 2:
            print(497)
            return True

        blockers = self.fetch_blockers(a1, k1, not side)

        for i in range(len(blockers)):
            b1 = blockers[i][0]
            b2 = blockers[i][1]
            if any(
                (
                    not 0 <= b1[0] <= 7,
                    not 0 <= b1[1] <= 7,
                    not 0 <= b2[0] <= 7,
                    not 0 <= b2[1] <= 7,
                )
            ):
                continue
            tile_1 = self.board[b1[0]][b1[1]]
            tile_2 = self.board[b2[0]][b2[1]]
            stored_data = (
                tile_1[0],
                tile_1[1],
                tile_1[2],
                tile_2[0],
                tile_2[1],
                tile_2[2],
            )
            self.update(b1, b2)
            attacked = self.fetch_attackers(k1, side)
            self.board[b1[0]][b1[1]] = [stored_data[0], stored_data[1], stored_data[2]]
            self.board[b2[0]][b2[1]] = [stored_data[3], stored_data[4], stored_data[5]]

            if not attacked:
                print(536)
                return False
        print(538)
        return True

    def is_stalemate(self) -> bool:
        ws, bs = True, True
        for i in range(8):
            for j in range(8):
                tile = self.board[i][j]
                if not tile[0]:
                    continue
                moves = self.fetch_moves((i, j))
                if len(moves) > 0:
                    if tile[2]:
                        ws = False
                    if not tile[2]:
                        bs = False
                if not ws and not bs:
                    return False
        return True

    def fetch_blockers(
        self, a1: Point, k1: Point, side: int
    ) -> list[tuple[Point, Point]]:
        row_diff = a1[0] - k1[0]
        col_diff = a1[1] - k1[1]
        row_dir, col_dir, dist = 0, 0, 0
        output = []
        if not col_diff or not row_diff:
            dist = abs(row_diff) + abs(col_diff)
        if abs(col_diff) == abs(row_diff):
            dist = abs(row_diff)

        if col_diff > 0:
            col_dir = 1
        elif col_diff < 0:
            col_dir = -1
        if row_diff > 0:
            row_dir = 1
        elif row_diff < 0:
            row_dir = -1

        for move in range(1, dist):
            m1 = a1[0] + move * row_dir, a1[1] + move * col_dir
            attackers = self.fetch_attackers(m1, not side)
            for coord in attackers:
                output.append((coord, m1))
        return output

    def evaluate(self) -> int:
        score = 0
        for i in range(8):
            for j in range(8):
                count = 0
                tile = self.board[i][j]
                if tile[0] == 0:
                    continue
                if tile[0] == 6:
                    k1 = (i, j)
                    attackers = self.fetch_attackers(k1, tile[2])
                    for a1 in attackers:
                        if self.is_checkmate(a1, k1, tile[2]):
                            return 100000 if tile[2] else -100000

                x, y = (7 - i, j) if tile[2] else (i, j)
                table, mat = self._tables[tile[0] - 1]
                count = table[x][y] + mat

                if tile[2]:
                    score += count
                else:
                    score -= count
        return score


piece_dict = {
    " ": 0,
    "p": 1,
    "n": 2,
    "b": 3,
    "r": 4,
    "q": 5,
    "k": 6,
}
col_dict = {
    "a": 0,
    "b": 1,
    "c": 2,
    "d": 3,
    "e": 4,
    "f": 5,
    "g": 6,
    "h": 7,
}


def array_from_fen(fen: str) -> tuple[BoardArray, bool]:
    side = "w" in fen  # Reads side data from FEN
    piece_list = []
    for row in fen.split("/"):
        piece_row = []
        for piece in row:
            if piece == " ":
                break
            if piece.isnumeric():
                piece = [" " for _ in range(int(piece))]
            for i in piece:
                piece_row.append([piece_dict[i.lower()], i.isupper()])
        piece_list.append(piece_row)
    return [
        [[piece_list[7 - j][i][0], 0, piece_list[7 - j][i][1]] for i in range(8)]
        for j in range(8)
    ], side


def fen_from_array(boardstate: BoardArray, side: bool) -> str:
    fen = []
    blank_squares = 0
    for row in range(-1, -9, -1):
        for col in range(8):
            tile = boardstate[row][col]
            if 6 >= tile[0] >= 1:
                if blank_squares > 0:
                    fen.append(str(blank_squares))
                    blank_squares = 0
                fen.append(display_int_alpha(tile[0], tile[2]))
            elif tile[0] == 0:
                blank_squares += 1
        if blank_squares > 0:
            fen.append(str(blank_squares))
            blank_squares = 0
        fen.append("/")
    if not side:
        fen.append(" b ")
    else:
        fen.append(" w ")

    return "".join(fen)


def display_int(piece: int, side: int) -> str:
    return " ♟♞♝♜♛♚︎"[piece] if side else " ♙♘♗♖♕♔"[piece]


def display_int_alpha(piece: int, side: int) -> str:
    return " pnbrqk"[piece] if not side else " PNBRQK"[piece]


def points_pgn(points: list[Point]) -> None:
    for p in points:
        print(f"{'abcdefgh'[p[1]]}{p[0] + 1}", end=', ')
    print('\b\b')


def turn(board: Board, coords: str):
    board.set_input(coords)
    print("legal moves:", end=' ')
    points_pgn(board.fetch_moves(board.input[0]))
    board.execute_input()
    print("checkmate?:", board.is_checkmate(board.input[1], board.find_king(board.turn), board.turn))
    print("legal king moves:", end=' ')
    points_pgn(board.fetch_moves(board.find_king(board.turn)))
    points_pgn(board.fetch_attackers((5, 4), 0))
    board.display_board()


if __name__ == "__main__":
    with open('test_positions') as f:
        positions = f.readlines()
    game = Board(positions[4])
    game.display_board()
    while True:
        entry = "h5e5"  # input("Enter chess notation (or x to exit)")
        if entry == "x":
            break
        turn(game, entry)
        break
