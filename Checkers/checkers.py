import argparse
import copy


class State:
    def __init__(self, board):
        self.board = board
        self.width = 8
        self.height = 8

    def display(self):
        for row in self.board:
            print(''.join(row))
        print("")

    def clone(self):
        return State(copy.deepcopy(self.board))


def evaluate(state, current_depth):
        b_piece = sum([row.count('b') + 1.5 * row.count('B') for row in state.board])
        r_piece = sum([row.count('r') + 1.5 * row.count('R') for row in state.board])
        return r_piece - b_piece - 0.2 * current_depth

def is_game_over(state, player):
        b_pieces = sum([row.count('b') + row.count('B') for row in state.board])
        r_pieces = sum([row.count('r') + row.count('R') for row in state.board])
        moves = get_valid_moves(state, player)
        return b_pieces == 0 or r_pieces == 0 or moves == []

def get_opp_char(player):
    return ['r', 'R'] if player in ['b', 'B'] else ['b', 'B']

def get_next_turn(curr_turn):
    return 'b' if curr_turn == 'r' else 'r'

def read_from_file(filename):
    with open(filename) as f:
        lines = f.readlines()
        board = [[x for x in line.rstrip()] for line in lines]
    return board

def move_piece(state, move):
    new_state = state.clone()
    board = new_state.board
    update = False

    if len(move) == 2:
        (start, end) = move
        start_x, start_y = start
        end_x, end_y = end
        piece = board[start_x][start_y]
        board[end_x][end_y] = piece
        board[start_x][start_y] = '.'

    elif len(move) == 3:
        (start, end, jumped) = move
        start_x, start_y = start
        end_x, end_y = end
        jump_x, jump_y = jumped
        piece = board[start_x][start_y]
        board[end_x][end_y] = piece
        board[start_x][start_y] = '.'
        board[jump_x][jump_y] = '.'

    if piece == 'r' and end_x == 0:
        board[end_x][end_y] = 'R'
        update = True
        
    elif piece == 'b' and end_x == 7:
        board[end_x][end_y] = 'B'
        update = True

    return new_state, update


def get_valid_moves(state, player):
    moves = []
    captures = []

    directions = [(-1, -1), (-1, 1)] if player == 'r' else [(1, -1), (1, 1)]  
    king_directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)] 

    for i in range(state.height):
        for j in range(state.width):
            piece = state.board[i][j]
            if piece.lower() == player:
                move_dirs = king_directions if piece.isupper() else directions

                for dx, dy in move_dirs:
                    new_x, new_y = i + dx, j + dy
                    if is_in_bounds(new_x, new_y) and state.board[new_x][new_y] == '.':
                        new_state, _ = move_piece(state, ((i, j), (new_x, new_y)))
                        moves.append(new_state)

                for dx, dy in move_dirs:
                    mid_x, mid_y = i + dx, j + dy
                    jump_x, jump_y = i + 2 * dx, j + 2 * dy
                    if is_in_bounds(jump_x, jump_y) and state.board[jump_x][jump_y] == '.' and \
                            state.board[mid_x][mid_y] in get_opp_char(player):
                        captures.append(get_jump_chain(state, (i, j), (jump_x, jump_y), (mid_x, mid_y), move_dirs))

    return captures if captures else moves

def get_jump_chain(state, start, jump, jumped, directions):
    new_state, update = move_piece(state, (start, jump, jumped))
    if (update):
        return new_state
    piece = new_state.board[jump[0]][jump[1]]

    for dx, dy in directions:
        mid_x, mid_y = jump[0] + dx, jump[1] + dy
        jump_x, jump_y = jump[0] + 2 * dx, jump[1] + 2 * dy
        if is_in_bounds(jump_x, jump_y) and new_state.board[jump_x][jump_y] == '.' and \
                new_state.board[mid_x][mid_y] in get_opp_char(piece):
            additional_jumps = get_jump_chain(new_state, jump, (jump_x, jump_y), (mid_x, mid_y), directions)
            new_state = additional_jumps

    return new_state

def is_in_bounds(x, y):
    return 0 <= x < 8 and 0 <= y < 8

def alpha_beta(state, depth, alpha, beta, maximizing_player, player, current_depth=0):
    if depth == 0 or is_game_over(state, player):
        return evaluate(state, current_depth), None

    valid_moves = get_valid_moves(state, player)

    if maximizing_player:
        max_eval = -float('inf')
        best_move = None
        for new_state in valid_moves:
            eval, _ = alpha_beta(new_state, depth - 1, alpha, beta, False, get_next_turn(player), current_depth + 1)
            if eval > max_eval:
                max_eval = eval
                best_move = new_state
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        best_move = None
        for new_state in valid_moves:
            eval, _ = alpha_beta(new_state, depth - 1, alpha, beta, True, get_next_turn(player), current_depth + 1)
            if eval < min_eval:
                min_eval = eval
                best_move = new_state
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval, best_move

def write_to_file(best_moves, output_file):
    with open(output_file, 'w') as f:
        for state in best_moves:
            for row in state.board:
                f.write(''.join(row) + '\n')
            f.write('\n')
    return None

def solve_checkers(state, turn, max_depth=7):
    best_moves = [state]
    max_player = True
    while (not is_game_over(state, turn)):

        _, best_move = alpha_beta(state, max_depth, -float('inf'), float('inf'), max_player, turn)
        best_moves.append(best_move)
        state = best_move

        turn = get_next_turn(turn)
        max_player = not max_player
    return best_moves

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--inputfile",
        type=str,
        required=True,
        help="The input file that contains the puzzle."
    )
    parser.add_argument(
        "--outputfile",
        type=str,
        required=True,
        help="The output file that contains the solution."
    )
    args = parser.parse_args()

    initial_board = read_from_file(args.inputfile)
    state = State(initial_board)
    turn = 'r'
    best_moves = solve_checkers(state, turn)
    write_to_file(best_moves, args.outputfile)
