"""
atheris.py
Main chess logic and processing
version 0.5
"""
from copy import deepcopy
from time import process_time


Point = tuple[int, int]
BoardArray = list[list[list[int]]]


class Board:
    """
    Represents a chess board.

    Attributes:

    - board (list): 3D list representing the current state of the chess board.
    - turn (bool): Indicates the side to play. True for White, False for Black.
    - half_moves (int): The number of half-moves played in the game.\n
    - past_states (list): List of previous board states.\n
    - result (None or str): The result of the game, if available. None if the game is still ongoing.\n
    - coord_input (None or str): Placeholder for input information.\n
    - last_move (None or str): The last move played on the board.\n
    - _move_functions (tuple): Tuple of functions used for generating different types of moves.\n
    - _tables (list): List of piece tables used for evaluation, along with their respective values.\n
    """
    def __init__(self, fen):
        with open('piece_tables.txt') as g:
            ls = g.readlines()
        ls = [[int(x) for x in l.strip().split(', ')] for l in ls if l[0] != '#']
        self.board, self.turn = array_from_fen(fen)
        self.half_moves = 0
        self.past_states = []
        self.result = None
        self.coord_input = None
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

    def display_board(self, **kwargs) -> None:
        """
        Display the current state of the board.

        Keyword Arguments:
            - persp (bool): Determines if the board should be displayed from the white or black side (True or False, respectively.
                            Defaults to True.

        Returns:
            None
        """
        persp = kwargs.get("persp", True)
        print(f"Side to play: {'White' if self.turn else 'Black'}")
        for i in range(1, 9):
            print('\n', 9 - i, end=' ')
            for j in range(8):
                print(display_int(self.board[-i][j][0], self.board[-i][j][2]), end=' ')
            print('|', end='')
        print(f"\n    a  b c d e f g h\n\nMoves: {self.half_moves // 2}, Result: {'Playing' if self.result is None else self.result}")

    def is_threefold(self) -> None:
        """
        Check if the current board position has occurred three times previously.

        Returns:
            None
        """
        repetitions = 0
        current = fen_from_array(self.board, self.turn)
        for i in range(len(self.past_states)):
            if self.past_states[i] == current:
                repetitions += 1
        result = "Threefold" if repetitions >= 2 else None

    def set_input(self, move: str) -> bool:
        """
        Set the input move for the current player.

        Args:
            - move (str): The move to be set as input.

        Returns:
            bool: True if the move is successfully set as input, False otherwise.
        """
        try:
            move = move.strip().lower()
            if move == "resign":
                self.result = f"{'White' if self.turn else 'Black'} resigned."
                self.coord_input = None
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
                    self.coord_input = coords
                    return True
        except (IndexError, ValueError):
            print(90)
        return False

    def execute_input(self) -> bool:
        """
        Execute the input move on the board.

        Returns:
            bool: True if the move is successfully executed, False otherwise.
        """
        if self.coord_input is None:
            return False
        if self.coord_input[1] not in self.fetch_moves(self.coord_input[0]):
            print(95)
            return False
        if self.move_piece():
            print(97)
            self.turn = not self.turn
            # TODO After every move, update prior move to store potential en passant, but also after each simulation

    def move_piece(self) -> bool:
        """
        Move a chess piece on the board based on the input coordinates and legality.
        Checks for game ending states.

        Returns:
            bool: True if the piece is successfully moved, False otherwise.
        """
        p1, p2 = self.coord_input[0], self.coord_input[1]
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

    def update(self, p1: Point, p2: Point) -> None:
        """
        Update the board state by simulating a move from p1 to p2.

        Args:
            p1 (Point): The starting position of the piece to be moved.
            p2 (Point): The destination position of the piece to be moved.

        Returns:
            None
        """
        tile_1 = self.board[p1[0]][p1[1]]
        self.board[p2[0]][p2[1]] = [tile_1[0], 1, tile_1[2]]
        self.board[p1[0]][p1[1]] = [0, 1, 0]

    def fetch_moves(self, p1: Point) -> list[Point]:
        """
        Calculate the legal moves of the chess piece at position p1.

        Args:
            p1 (Point): The position of the chess piece.

        Returns:
            list[Point]: A list of positions representing the legal moves of the chess piece.
        """
        tile = self.board[p1[0]][p1[1]]
        k1 = self.find_king(tile[2])
        return (
            self._move_functions[tile[0] - 1](p1, k1, tile[2])
            if tile[0] and k1 is not None
            else []
        )

    def fetch_all_moves(self, side: int) -> list[tuple[Point, Point]]:
        """
        Calculate the legal moves of the chess piece at position p1.

        Args:
            side (int): The side to find moves for

        Returns:
            list[Point]: A list of positions representing the legal moves of the chess piece.
        """
        output = []
        for i in range(8):
            for j in range(8):
                if self.board[i][j][0] != 0 and self.board[i][j][2] == side:
                    targets = self.fetch_moves((i, j))
                    for target in targets:
                        output.append(((i, j), target))
        return output

    def find_king(self, side: int) -> Point:
        """
        Find the coordinates of the king of the specified side on the chess board.

        Args:
            side (int): The side of the king to find. Use 0 for black and 1 for white.

        Returns:
            Point: The coordinates of the king as a tuple (row, column), or (0, 0) if the king is not found.
        """
        for i in range(8):
            for j in range(8):
                if self.board[i][j][0] == 6 and self.board[i][j][2] == side:
                    return i, j
        return 0, 0

    def check_king(self, k1: Point, p1: Point, p2: Point, king_side: int) -> bool:
        """
        Check if the king would be left in check after moving the piece from position p1 to position p2.

        Args:
            k1 (Point): The current position of the king.
            p1 (Point): The position of the piece to be moved.
            p2 (Point): The destination position for the piece.
            king_side (int): The side of the king to check. Use 0 for black and 1 for white.

        Returns:
            bool: True if the king would be left in check, False otherwise.
        """
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
        """
        Generate a list of legal castling moves for the given position and king's side.

        Args:
            p1 (Point): The current position of the king.
            kr_side (int): The side of the king (0 for black, 1 for white).

        Returns:
            list[Point]: A list of valid castling moves represented as target king coordinates (Points).
        """
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
        """
        Generate a list of legal moves for a knight piece at the given position.

        Args:
            p1 (Point): The current position of the knight.
            k1 (Point): The current position of the king.
            piece_side (int): The side of the knight (0 for black, 1 for white).

        Returns:
            list[Point]: A list of valid moves for the knight represented as target coordinates (Points).
        """
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
        """
        Generate a list of legal moves for a king at the given position.

        Args:
            p1 (Point): The current position of the king.
            k1 (Point): Also the current position of the king.
            piece_side (int): The side of the king (0 for black, 1 for white).

        Returns:
            list[Point]: A list of valid moves for the king represented as target coordinates (Points).
        """
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
            output.append(p2)
        return output

    def gen_pawn_moves(self, p1: Point, k1: Point, piece_side: int) -> list[Point]:
        """
        Generate a list of legal moves for a pawn at the given position.

        Args:
            p1 (Point): The current position of the pawn.
            k1 (Point): The current position of the king.
            piece_side (int): The side of the pawn (0 for black, 1 for white).

        Returns:
            list[Point]: A list of valid moves for the pawn represented as target coordinates (Points).
        """
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
        """
        Generate a list of possible en passant moves for a pawn at the given position.

        Args:
            p1 (Point): The current position of the pawn.
            k1 (Point): The current position of the king.
            piece_side (int): The side of the pawn (0 for black, 1 for white).

        Returns:
         list[Point]: A list of valid en passant moves represented as target coordinates (Points).

        Notes:
            - If there was no previous move, an empty list is returned.
            - If all conditions are satisfied, the function returns a list containing the en passant destination position.
            - Otherwise, an empty list is returned.
        """
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
        """
        Generate a list of legal moves in diagonal or cardinal directions (based on the toggle parameter) from point p1.

        Args:
            p1 (Point): The starting position of the piece.
            k1 (Point): The current position of the king.
            piece_side (int): The side of the piece (0 for black, 1 for white).
            toggle (tuple[bool, bool]): A tuple representing the toggle parameter.
                - The first element indicates whether diagonal moves are returned.
                - The second element indicates whether cardinal moves are returned.

        Returns:
            list[Point]: A list of valid moves represented as coordinates (Points).
        """
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
        """Calls the appropriate function to generate queen moves"""
        return self.gen_ray_moves(p1, k1, piece_side, (True, True))

    def gen_bishop_moves(self, p1: Point, k1: Point, piece_side: int) -> list[Point]:
        """Calls the appropriate function to generate bishop moves"""
        return self.gen_ray_moves(p1, k1, piece_side, (True, False))

    def gen_rook_moves(self, p1: Point, k1: Point, piece_side: int) -> list[Point]:
        """Calls the appropriate function to generate rook moves"""
        return self.gen_ray_moves(p1, k1, piece_side, (False, True))

    def gen_all_king_moves(self, p1: Point, k1: Point, piece_side: int) -> list[Point]:
        """Calls the appropriate function to generate all king moves"""
        return self.gen_king_moves(p1, k1, piece_side) + self.gen_castling_moves(
            p1, piece_side
        )

    def gen_all_pawn_moves(self, p1: Point, k1: Point, piece_side: int) -> list[Point]:
        """Calls the appropriate function to generate all pawn moves"""
        return self.gen_pawn_moves(p1, k1, piece_side) + self.gen_passant(p1, k1, piece_side)

    def ray_checks(self, p1: Point, side: int) -> list[Point]:
        """
        Checks along the cardinal and diagonal directions for attacking pieces.

        Args:
            p1 (Point): The position to check for attacking pieces.
            side (int): The side of the piece (0 for black, 1 for white).

        Returns:
            list[Point]: A list of coordinates (Points) representing the attacking pieces.

        Notes:
            - The function checks for attacking pieces along the cardinal (vertical and horizontal) and diagonal directions.
            - The function iterates through two sets of directions: diagonal and cardinal.
            - The diagonal directions are ((1, 1), (-1, 1), (1, -1), (-1, -1)).
            - The cardinal directions are ((0, 1), (1, 0), (0, -1), (-1, 0)).
            - For each set of directions, the function iterates over positions in increasing distance from p1.
            - If the position is out of the chessboard bounds, the iteration for that direction is stopped.
            - If the tile at the position is empty, the iteration continues to the next position in that direction.
            - If the tile at the position is occupied, further checks are performed.
            - If the tile belongs to the same side as the piece, the iteration for that direction is stopped.
            - If the tile belongs to the opposing side and is a valid attacking piece (bishop, rook, and or queen depending), it is added to the output.
        """
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
        """
        Search for any knights attacking the given point.

        Args:
            p1 (Point): The point to check for knight attacks.
            side (int): The side of the piece (0 for black, 1 for white).

        Returns:
            list[Point]: A list of positions (Points) representing any attacking knights.

        Notes:
            - The function checks for knight attacks by considering all possible knight move patterns.
        """
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
        """
        Search for any pawns attacking the given point.

        Args:
            p1 (Point): The point to check for pawn attacks.
            side (int): The side of the piece (0 for black, 1 for white).

        Returns:
            list[Point]: A list of positions (Points) representing the attacking pawns.

        Notes:
            - The function checks for pawn attacks along the diagonal directions based on the pawn's side.
            - The function considers the pawn's direction based on its side: 1 for white pawns (side = 1), -1 for black pawns (side = 0).
        """
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
        """
        Search for any kings attacking the given point.

        Args:
            p1 (Point): The point to check for king attacks.
            side (int): The side of the piece(0 for black, 1 for white).

        Returns:
            list[Point]: A list of positions (Points) representing the attacking kings.

        Notes:
            - The function checks for king attacks in the cardinal and diagonal directions.
            - It iterates through each possible direction: (1, 1), (1, 0), (1, -1), (0, 1), (0, -1), (-1, 1), (-1, 0), (-1, -1).
        """
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
        """
        Fetches all the attacking pieces targeting the given point.

        Args:
            p1 (Point): The point to check for attackers.
            side (int): The side of the piece at the point (0 for black, 1 for white).

        Returns:
            list[Point]: A list of positions (Points) representing the attacking pieces.
        """
        return (
            self.king_checks(p1, side)
            + self.pawn_checks(p1, side)
            + self.knight_checks(p1, side)
            + self.ray_checks(p1, side)
        )

    def is_checkmate(self, a1: Point, k1: Point, side: int) -> bool:
        """
        Determines if the current game state is a checkmate for the specified side, due to the piece at a1.

        Args:
            a1 (Point): The position of the attacking piece.
            k1 (Point): The position of the king piece.
            side (int): The side for which to check for checkmate (0 for white, 1 for black).

        Returns:
            bool: True if the game state is a checkmate, False otherwise.

        Notes:
            - This function must be ran for each attacking piece in a possible checkmate scenario, as it merely checks if a specific piece is checkmating the king.
        """
        tile_1 = self.board[k1[0]][k1[1]]
        tile_2 = self.board[a1[0]][a1[1]]

        if any((tile_1[0] != 6, tile_2[2] == tile_1[2], self.fetch_moves(k1))):
            return False

        for a2 in self.fetch_attackers(a1, side):
            if self.board[a2[0]][a2[1]][0] == 6:
                if not self.fetch_attackers(a1, not side):
                    return False
            else:
                return False

        if tile_2[0] == 2:
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
                return False
        return True

    def is_stalemate(self) -> bool:
        """
        Determines if the current game state is a stalemate.

        Returns:
            bool: True if the game state is a stalemate, False otherwise.
        """
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
        """
        Fetches the blockers between attacking point a1 and the king k1.

        Args:
            a1: The attacking point.
            k1: The king's position.
            side: The side to check for blockers.

        Returns:
            list[tuple[Point, Point]]: A list of tuples representing the positions of the blockers,
            where each tuple contains two Points representing the blocker's initial position and blocking position
        """
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
        """
        Evaluates the current board position and returns a the centipawn evaluation of said game state.

        Returns:
            int: The evaluation score indicating the advantage of one side. Positive scores favor white, negative scores favor black.
        """
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

    def mate_check(self) -> bool:
        """Determines if a position has a mate in it"""
        kings = (self.find_king(0), self.find_king(1))
        for i in (0, 1):
            for a1 in self.fetch_attackers(kings[i], i):
                if self.is_checkmate(a1, kings[i], i):
                    return True
        return False


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
    """
    Converts a FEN (Forsyth–Edwards Notation) string representation of a chess position to a board array.

    Args:
        fen (str): The FEN string representing the chess position.

    Returns:
        tuple[BoardArray, bool]: A tuple containing the board array representation of the chess position
        and a boolean indicating the side to move (True for white, False for black).
    """
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
    """
    Converts a board array representation of a chess position to a FEN (Forsyth–Edwards Notation) string.

    Args:
        boardstate (BoardArray): The board array representation of the chess position.
        side (bool): The side to move. True for white, False for black.

    Returns:
        str: The FEN string representing the chess position.
    """
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
    """
    Returns the Unicode representation of a chess piece based on its integer code and side.

    Args:
        piece (int): The integer code representing the chess piece.
        side (int): The side of the chess piece. 0 for black, 1 for white.

    Returns:
        str: The Unicode representation of the chess piece.
    """
    return " ♟♞♝♜♛♚︎"[piece] if side else " ♙♘♗♖♕♔"[piece]


def display_int_alpha(piece: int, side: int) -> str:
    """
    Returns the algebraic notation representation of a chess piece based on its integer code and side.

    Args:
        piece (int): The integer code representing the chess piece.
        side (int): The side of the chess piece. 0 for black, 1 for white.

    Returns:
        str: The algebraic notation representation of the chess piece.

    """
    return " pnbrqk"[piece] if not side else " PNBRQK"[piece]


def points_pgn(points: list[Point]) -> None:
    """
    Prints the PGN (Portable Game Notation) representation of a list of points.

    Args:
        points (list[Point]): The list of points to be printed.

    Returns:
        None
    """
    for p in points:
        print(f"{'abcdefgh'[p[1]]}{p[0] + 1}", end=', ')
    print('\b\b')


def turn(board: Board, coords: str):
    """
    Perform a turn in a chess game and display relevant information.

    This function sets the input coordinates on the board, prints the legal moves for the selected piece,
    executes the input move on the board, and then displays additional information such as checkmate status,
    legal moves for the king, attackers for a specific position, and finally displays the current state of the board.

    Args:
        board (Board): The chess board object representing the game state.
        coords (str): The coordinates for the selected piece to be moved.

    Returns:
        None
    """
    board.set_input(coords)
    print("legal moves:", end=' ')
    points_pgn(board.fetch_moves(board.coord_input[0]))
    board.execute_input()
    print("checkmate?:", board.is_checkmate(board.coord_input[1], board.find_king(board.turn), board.turn))
    print("legal king moves:", end=' ')
    points_pgn(board.fetch_moves(board.find_king(board.turn)))
    points_pgn(board.fetch_attackers((5, 4), 0))
    board.display_board()


def perft(board: Board, side: int) -> int:
    """
    Calculates and evaluates board states at a depth of 4 from the starting position. Returns number of moves

    Args:
        board (Board): The board object representing the game state.
        side (int): The depth that the function needs to generate moves to.

    Returns:
        int: number of moves generated
    """
    plie_4 = 0
    plie_1 = 0
    plie_2 = 0
    plie_3 = 0
    start = process_time()
    for move in board.fetch_all_moves(side):
        p1 = move[0]
        p2 = move[1]
        tile_1 = board.board[p1[0]][p1[1]]
        tile_2 = board.board[p2[0]][p2[1]]
        stored_data = (
            tile_1[0],
            tile_1[1],
            tile_1[2],
            tile_2[0],
            tile_2[1],
            tile_2[2],
        )
        board.update(p1, p2)
        plie_1 += 1
        if not board.mate_check():
            for move2 in board.fetch_all_moves(not side):
                p11 = move2[0]
                p21 = move2[1]
                tile_11 = board.board[p11[0]][p11[1]]
                tile_21 = board.board[p21[0]][p21[1]]
                stored_data1 = (
                    tile_11[0],
                    tile_11[1],
                    tile_11[2],
                    tile_21[0],
                    tile_21[1],
                    tile_21[2],
                )
                board.update(p11, p21)
                plie_2 += 1
                if not board.mate_check():
                    for move3 in board.fetch_all_moves(side):
                        p12 = move3[0]
                        p22 = move3[1]
                        tile_12 = board.board[p12[0]][p12[1]]
                        tile_22 = board.board[p22[0]][p22[1]]
                        stored_data2 = (
                            tile_12[0],
                            tile_12[1],
                            tile_12[2],
                            tile_22[0],
                            tile_22[1],
                            tile_22[2],
                        )
                        board.update(p12, p22)
                        plie_3 += 1
                        if not board.mate_check():
                            for move4 in board.fetch_all_moves(not side):
                                p13 = move4[0]
                                p23 = move4[1]
                                tile_13 = board.board[p13[0]][p13[1]]
                                tile_23 = board.board[p23[0]][p23[1]]
                                stored_data3 = (
                                    tile_13[0],
                                    tile_13[1],
                                    tile_13[2],
                                    tile_23[0],
                                    tile_23[1],
                                    tile_23[2],
                                )
                                board.update(p13, p23)
                                if not board.mate_check():
                                    plie_4 += 1
                                    board.evaluate()
                                board.board[p13[0]][p13[1]] = [stored_data3[0], stored_data3[1], stored_data3[2]]
                                board.board[p23[0]][p23[1]] = [stored_data3[3], stored_data3[4], stored_data3[5]]
                        board.board[p12[0]][p12[1]] = [stored_data2[0], stored_data2[1], stored_data2[2]]
                        board.board[p22[0]][p22[1]] = [stored_data2[3], stored_data2[4], stored_data2[5]]
                board.board[p11[0]][p11[1]] = [stored_data1[0], stored_data1[1], stored_data1[2]]
                board.board[p21[0]][p21[1]] = [stored_data1[3], stored_data1[4], stored_data1[5]]
        board.board[p1[0]][p1[1]] = [stored_data[0], stored_data[1], stored_data[2]]
        board.board[p2[0]][p2[1]] = [stored_data[3], stored_data[4], stored_data[5]]
    time = round(process_time() - start, 2)
    print(time, round(time * 1000000 / plie_4, 2))
    print(plie_1, plie_2, plie_3, plie_4)
    return plie_4


if __name__ == "__main__":
    with open('position_fens.txt') as f:
        positions = f.readlines()
    game = Board(positions[0])
    game.display_board()
    while True:
        perft(game, game.turn)
        entry = input("Enter chess notation (or x to exit)")
        if entry == "x":
            break
        turn(game, entry)
